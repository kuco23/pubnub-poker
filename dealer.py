from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from pokerlib.pokerlib import Player, PlayerGroup, Table
from pokerlib.pokerlib.enums import *
from cryptolib import encrypt, pubkeydeserialized

import config as cfg

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
      mes, pub = message.message, message.publisher
      
      if mes.startswith('pubkey'): 
          self.table.pubk[message.publisher] = pubkeydeserialized(mes[6:])
          
      elif mes == 'buyin':
          player = Player(self.table.id, pub, pub, 100)
          if player not in self.table:
              self.table += [player]
      
      elif self.table: 
        ret = self.table.translate(mes)
        if ret is None: return
        cmd, val = ret
        self.table.publicIn(pub, cmd, raise_by=val)

  def signal(self, pubnub, signal):
      pass # Handle incoming signals

def my_publish_callback(envelope, status):
    if status.is_error():
        print(envelope, status)
    else: print(envelope, 'sent')

values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
suits = ['♠', '♣', '♦', '♥']
hands = ['High Card', 'One Pair', 'Two Pair', 'Three of a Kind', 'Straight', 'Flush', 'Four of a Kind', 'Straight Flush']
turn_names = ['Preflop', 'Flop', 'Turn', 'River']

class PubNubTable(Table):
    
    def __init__(self, *args):
        self.out_queue = []
        self.pubk = {}
        super().__init__(*args)
    
    def privateOut(self, player_id, out_id, **kwargs):
        if out_id is RoundPrivateOutId.DEALTCARDS:
            player = self.round.players.getPlayerById(player_id)
            cards = self.cardrepr(player.cards)
            msg = cards.encode()
            
        encr = encrypt(self.pubk[player_id], msg)
        pubnub.publish().channel(channel_name).message(
            f'---- private {player_id} private ----- {encr}'
        ).pn_async(my_publish_callback)
            
    def publicOut(self, out_id, **kwargs):
        if out_id is RoundPublicOutId.NEWROUND:
            mes = "----------- new round -------------"
        elif out_id is RoundPublicOutId.NEWTURN:
            turn_name = turn_names[kwargs['turn'].value]
            board = self.cardrepr(self.round.board)
            mes = f"{turn_name} : {board}"
        elif out_id is RoundPublicOutId.SMALLBLIND: 
            mes = f"{kwargs['player_id']} posted a small blind of {self.small_blind}"
        elif out_id is RoundPublicOutId.BIGBLIND:
            mes = f"{kwargs['player_id']} posted a big blind of {self.big_blind}"
        elif out_id is RoundPublicOutId.PLAYERCHECK:
            mes = f"{kwargs['player_id']} checked"
        elif out_id is RoundPublicOutId.PLAYERCALL:
            mes = f"{kwargs['player_id']} called {kwargs['called']}"
        elif out_id is RoundPublicOutId.PLAYERFOLD:
            mes = f"{kwargs['player_id']} folded"
        elif out_id is RoundPublicOutId.PLAYERRAISE:
            mes = f"{kwargs['player_id']} raised by {kwargs['raised_by']}"
        elif out_id is RoundPublicOutId.PLAYERALLIN:
            mes = f"{kwargs['player_id']} went all in with {kwargs['all_in_stake']}"
        elif out_id is RoundPublicOutId.PLAYERACTIONREQUIRED:
            mes = f"{kwargs['player_id']} has to call {kwargs['to_call']}"
        elif out_id is RoundPublicOutId.PUBLICCARDSHOW:
            player = self.round.players.getPlayerById(kwargs['player_id'])
            cards = self.cardrepr(player.cards)
            mes = f"{player.id} has {cards}"
        elif out_id is RoundPublicOutId.DECLAREPREMATUREWINNER:
            mes = f"{kwargs['player_id']} won {kwargs['money_won']}"
        elif out_id is RoundPublicOutId.DECLAREFINISHEDWINNER:
            player = self.round.players.getPlayerById(kwargs['player_id'])
            handname = hands[player.hand.handenum.value]
            hand = self.cardrepr(player.hand.handbasecards)
            mes = (
                f"{player.id} won {kwargs['money_won']} with "
                f"{handname} ({hand} and {kwargs['kickers']} kickers)"
            )
        elif out_id is RoundPublicOutId.ROUNDFINISHED:
            mes = "----------- round finished ---------------"
        elif out_id is TablePublicOutId.PLAYERJOINED:
            mes = f"{kwargs['player_id']} has joined the table"
        elif out_id is TablePublicOutId.PLAYERREMOVED:
            mes = f"{kwargs['player_id']} was removed from the table"
        elif out_id is TablePublicOutId.NEWROUNDSTARTED:
            mes = f"new round was started"
        elif out_id is TablePublicOutId.ROUNDNOTINITIALIZED:
            mes = f"round is has not been initialized"
        else: return print(out_id)

        pubnub.publish().channel(channel_name).message(mes).pn_async(my_publish_callback)

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
