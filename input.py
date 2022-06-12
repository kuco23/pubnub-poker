import json

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from lib.cryptolib import pubkeyget, pubkeyserialized
import lib.config as cfg

pnconfig = PNConfiguration()
pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = cfg.PUBNUB_UUID
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL

def my_publish_callback(envelope, status):
    if status.is_error():
        print(envelope, status)

pubnub.subscribe().channels(channel_name).execute()
while True: 
    data = {'msg': input()}
    if data['msg'] == 'buyin': 
        data['pubk'] = pubkeyserialized(pubkeyget())
    pubnub.publish().channel(channel_name).message(
        json.dumps(data)).pn_async(my_publish_callback)
