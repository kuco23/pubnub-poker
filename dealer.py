from collections import namedtuple
import json

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from pokerlib.pokerlib import Player, PlayerGroup, Table
from pokerlib.pokerlib.enums import *
from lib.cryptolib import encrypt, pubkeydeserialized
import lib.config as cfg

values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
suits = ['♠', '♣', '♦', '♥']
hands = ['High Card', 'One Pair', 'Two Pair', 'Three of a Kind', 'Straight', 'Flush', 'Four of a Kind', 'Straight Flush']
turn_names = ['Preflop', 'Flop', 'Turn', 'River']

pnconfig = PNConfiguration()

pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = 'dealer'
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL

class SubscribeHandler(SubscribeCallback):
    
  def __init__(self, table):
      self.table = table
      super().__init__()
    
  def status(self, pubnub, event):
      pass

  def presence(self, pubnub, presence):
      pass  # Handle incoming presence data

  def message(self, pubnub, message):
      data = json.loads(message.message)
      pub = message.publisher
      if pub == 'dealer': return
      
      if data['msg'] == 'buyin':
          pubk = pubkeydeserialized(data['pubk'])
          player = PubNubPlayer(self.table.id, pub, 100, pubk)
          if player not in self.table: self.table += [player]
      
      elif self.table: 
        ret = self.table.translate(data['msg'])
        if ret is not None:
            cmd, val = ret
            self.table.publicIn(pub, cmd, raise_by=val)
    
      self.table.sendQueuedMessages()

  def signal(self, pubnub, signal):
      pass # Handle incoming signals

def my_publish_callback(envelope, status):
    if status.is_error():
        print(envelope, status)
    else: print(envelope, 'sent')
    

class PubNubPlayer(Player):
    def __init__(self, table_id, name, money, pubk):
        self.pubk = pubk
        super().__init__(table_id, name, name, money)

class PubNubTable(Table):
    PublicOut = namedtuple('PublicOut', ['msg'])
    PrivateOut = namedtuple('PrivateOut', ['player_id', 'msg'])
    
    def __init__(self, *args):
        self.public_out_queue = []
        self.private_out_queue = []
        super().__init__(*args)
    
    def sendQueuedMessages(self):
        public_data, private_data = [], []
        for out in self.public_out_queue:
            public_data.append({
                'msg': out.msg, 'visibility': 'public'
            })
        for out in self.private_out_queue:
            player = self.players.getPlayerById(out.player_id)
            if player is None: 
                player = self.round.players.getPlayerById(out.player_id)
            encr = encrypt(player.pubk, out.msg)
            private_data.append({
                'msg': encr, 'visibility': out.player_id
            })
        if len(public_data):
            pubnub.publish().channel(channel_name).message(
                json.dumps(public_data)).pn_async(my_publish_callback)
        if len(private_data):
            pubnub.publish().channel(channel_name).message(
                json.dumps(private_data)).pn_async(my_publish_callback)
        self.public_out_queue.clear()
        self.private_out_queue.clear()
            
    def privateOut(self, player_id, out_id, **kwargs):
        if out_id is RoundPrivateOutId.DEALTCARDS:
            player = self.round.players.getPlayerById(player_id)
            cards = self.cardrepr(player.cards)
            msg = cards.encode()
            
        self.private_out_queue.append(self.PrivateOut(player_id, msg))
    
    def publicOut(self, out_id, **kwargs):
        if out_id is RoundPublicOutId.NEWROUND:
            msg = "----------- new round -------------"
        elif out_id is RoundPublicOutId.NEWTURN:
            turn_name = turn_names[kwargs['turn'].value]
            board = self.cardrepr(self.round.board)
            msg = f"{turn_name} : {board}"
        elif out_id is RoundPublicOutId.SMALLBLIND: 
            msg = f"{kwargs['player_id']} posted a small blind of {self.small_blind}"
        elif out_id is RoundPublicOutId.BIGBLIND:
            msg = f"{kwargs['player_id']} posted a big blind of {self.big_blind}"
        elif out_id is RoundPublicOutId.PLAYERCHECK:
            msg = f"{kwargs['player_id']} checked"
        elif out_id is RoundPublicOutId.PLAYERCALL:
            msg = f"{kwargs['player_id']} called {kwargs['called']}"
        elif out_id is RoundPublicOutId.PLAYERFOLD:
            msg = f"{kwargs['player_id']} folded"
        elif out_id is RoundPublicOutId.PLAYERRAISE:
            msg = f"{kwargs['player_id']} raised by {kwargs['raised_by']}"
        elif out_id is RoundPublicOutId.PLAYERALLIN:
            msg = f"{kwargs['player_id']} went all in with {kwargs['all_in_stake']}"
        elif out_id is RoundPublicOutId.PLAYERACTIONREQUIRED:
            msg = f"{kwargs['player_id']} has to call {kwargs['to_call']}"
        elif out_id is RoundPublicOutId.PUBLICCARDSHOW:
            player = self.round.players.getPlayerById(kwargs['player_id'])
            cards = self.cardrepr(player.cards)
            msg = f"{player.id} has {cards}"
        elif out_id is RoundPublicOutId.DECLAREPREMATUREWINNER:
            msg = f"{kwargs['player_id']} won {kwargs['money_won']}"
        elif out_id is RoundPublicOutId.DECLAREFINISHEDWINNER:
            player = self.round.players.getPlayerById(kwargs['player_id'])
            handname = hands[player.hand.handenum.value]
            hand = self.cardrepr(player.hand.handbasecards)
            msg = (
                f"{player.id} won {kwargs['money_won']} with "
                f"{handname} ({hand} and {kwargs['kickers']} kickers)"
            )
        elif out_id is RoundPublicOutId.ROUNDFINISHED:
            msg = "----------- round finished ---------------"
        elif out_id is TablePublicOutId.PLAYERJOINED:
            msg = f"{kwargs['player_id']} has joined the table"
        elif out_id is TablePublicOutId.PLAYERREMOVED:
            msg = f"{kwargs['player_id']} was removed from the table"
        elif out_id is TablePublicOutId.NEWROUNDSTARTED:
            msg = f"new round was started"
        elif out_id is TablePublicOutId.ROUNDNOTINITIALIZED:
            msg = f"round is has not been initialized"
        else: return print(out_id)

        self.public_out_queue.append(self.PublicOut(msg))

    @staticmethod
    def translate(msg):
        if msg.startswith('RAISE'):
            sval = msg.split()[-1]
            if sval.isdigit(): 
                return RoundPublicInId.RAISE, int(sval)
        elif msg in RoundPublicInId.__members__:
            return RoundPublicInId.__getitem__(msg), 0
        elif msg in TablePublicInId.__members__:
            return TablePublicInId.__getitem__(msg), 0
    
    @staticmethod
    def cardrepr(cards):
        return ' '.join(
            [values[v.value] + suits[s.value] for v, s in cards]
        )
    
table = PubNubTable(0, 6, PlayerGroup([]), 100, 5, 10)
pubnub.add_listener(SubscribeHandler(table))
pubnub.subscribe().channels(channel_name).execute()
