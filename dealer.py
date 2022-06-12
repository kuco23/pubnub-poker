from json import loads, dumps 

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from pokerlib.pokerlib import Player, PlayerGroup, Table
from pokerlib.pokerlib.enums import *
from lib.cryptolib import encrypt, pubkeydeserialized
import lib.config as cfg


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

  def message(self, pubnub, message):
      data = loads(message.message)
      pub = message.publisher
      if pub == 'dealer': return
      
      if data['msg'] == 'buyin':
          pubk = pubkeydeserialized(data['pubk'])
          player = PubNubPlayer(self.table.id, pub, 100, pubk)
          if player not in self.table: self.table += [player]
      
      ret = self.table.translate(data['msg'])
      if ret is not None:
          cmd, val = ret
          self.table.publicIn(pub, cmd, raise_by=val)
    
      self.table.sendQueuedMessages()

def my_publish_callback(envelope, status):
    if status.is_error():
        print(envelope, status)
    else: print(envelope, 'sent')

class PubNubPlayer(Player):
    def __init__(self, table_id, name, money, pubk):
        self.pubk = pubk
        super().__init__(table_id, name, name, money)

class PubNubTable(Table):
    
    def __init__(self, *args):
        self.message_queue = []
        super().__init__(*args)
    
    def sendQueuedMessages(self):
        messages = self.encodeMessages()
        if messages: 
            pubnub.publish().channel(channel_name).message(
                messages).pn_async(my_publish_callback)
        self.message_queue.clear()
    
    def encodeMessages(self):
        messages = []
        for out in self.message_queue:
            if out['visibility'] == 'public':
                messages.append(out)
            else:
                player = self[out['player_id']]
                pf = out['private_field']
                out[pf] = encrypt(player.pubk, str(out[pf]))
                messages.append(out)
        return dumps(messages)
            
    def privateOut(self, player_id, out_id, **kwargs):
        if out_id is RoundPrivateOutId.DEALTCARDS:
            kwargs['cards'] = self.unpackCards(kwargs['cards'])
            kwargs['private_field'] = 'cards'
        kwargs['out_id'] = out_id.name
        kwargs['player_id'] = player_id
        kwargs['visibility'] = player_id
        self.message_queue.append(kwargs)
    
    def publicOut(self, out_id, **kwargs):
        if out_id is RoundPublicOutId.NEWTURN:
            kwargs['board'] = self.unpackCards(kwargs['board'])
            kwargs['turn'] = kwargs['turn'].value
        elif out_id is RoundPublicOutId.PUBLICCARDSHOW:
            kwargs['cards'] = self.unpackCards(kwargs['cards'])
        elif out_id is RoundPublicOutId.DECLAREFINISHEDWINNER:
            kwargs['cards'] = self.unpackCards(kwargs['cards'])
            kwargs['hand'] = self.unpackCards(kwargs['hand'])
            kwargs['handname'] = kwargs['handname'].value
        kwargs['out_id'] = out_id.name 
        kwargs['visibility'] = 'public'
        self.message_queue.append(kwargs)

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
    def unpackCards(cards):
        return [(s.value, r.value) for s, r in cards]
        
    
table = PubNubTable(0, 6, PlayerGroup([]), 100, 5, 10)
pubnub.add_listener(SubscribeHandler(table))
pubnub.subscribe().channels(channel_name).execute()
