from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from cryptolib import pubkeyget, pubkeyserialized

import config as cfg

pnconfig = PNConfiguration()

pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = cfg.PUBNUB_UUID
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL

def my_publish_callback(envelope, status):
    if status.is_error():
        print(status)

pubnub.subscribe().channels(channel_name).execute()
while True: 
    cmd = input()
    if cmd == 'send public key':
        pbk = pubkeyserialized(pubkeyget())
        cmd = 'pubkey' + pbk
    pubnub.publish().channel(channel_name).message(
        cmd).pn_async(my_publish_callback)
