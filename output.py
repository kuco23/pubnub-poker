from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from cryptolib import decrypt, prvkeyget

import config as cfg

pnconfig = PNConfiguration()

pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = cfg.PUBNUB_UUID
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL
private_start = f'---- private'
private_identifier = f'---- private {pnconfig.uuid} private -----'

class SubscribeHandler(SubscribeCallback):
    
  def status(self, pubnub, event):
      pass

  def presence(self, pubnub, presence):
      pass  # Handle incoming presence data

  def message(self, pubnub, message):
      mes, pub = message.message, message.publisher
      if mes.startswith(private_identifier):
        prv = prvkeyget()
        encr = mes[len(private_identifier):]
        cards = decrypt(prv, encr)
        print(cards.decode())
      elif not mes.startswith(private_start): 
          print(f'{pub}: {mes}') 
      
  def signal(self, pubnub, signal):
      pass # Handle incoming signals

pubnub.add_listener(SubscribeHandler())
pubnub.subscribe().channels(channel_name).execute()
