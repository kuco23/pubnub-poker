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
      pub = message.publisher
      if pub == 'dealer': return
      data = loads(message.message)
      
      if (iid := self.table.getInId(data['msg'])) is not None:

          if iid is TablePublicInId.BUYIN:
              pubk = pubkeydeserialized(data['pubk'])
              player = PubNubPlayer(self.table.id, pub, 100, pubk)
              data['player'] = player
              
          self.table.publicIn(pub, iid, data)
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
            if out['visibility'] == 'public': pass
            elif (pf := out.get('private_field')):
                player = self[out['player_id']]
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
    def getInId(msg):
        if msg in RoundPublicInId.__members__:
            return RoundPublicInId.__getitem__(msg)
        elif msg in TablePublicInId.__members__:
            return TablePublicInId.__getitem__(msg)
    
    @staticmethod 
    def unpackCards(cards):
        return [(s.value, r.value) for s, r in cards]
        
table = PubNubTable(0, 6, PlayerGroup([]), 100, 5, 10)
pubnub.add_listener(SubscribeHandler(table))
pubnub.subscribe().channels(channel_name).execute()
