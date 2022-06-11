import json

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from lib.cryptolib import decrypt, prvkeyget
import lib.config as cfg

pnconfig = PNConfiguration()

pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = cfg.PUBNUB_UUID
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL

class SubscribeHandler(SubscribeCallback):
    
  def status(self, pubnub, event):
      pass

  def presence(self, pubnub, presence):
      pass  # Handle incoming presence data

  def message(self, pubnub, message):
      data = json.loads(message.message)
      pub = message.publisher
      
      if pub == 'dealer':
        for d in data:
            if d['visibility'] == 'public': 
                msg = d['msg']
                print(f'{pub}: {msg}') 
            elif d['visibility'] == pnconfig.uuid:
                prv = prvkeyget()
                encr = d['msg']
                cards = decrypt(prv, encr)
                print(cards.decode())
      else: 
          msg = data['msg']
          print(f'{pub}: {msg}')
      
  def signal(self, pubnub, signal):
      pass # Handle incoming signals

pubnub.add_listener(SubscribeHandler())
pubnub.subscribe().channels(channel_name).execute()
