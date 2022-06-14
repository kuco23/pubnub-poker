from json import dumps

from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pokerlib.pokerlib.enums import *

from lib.cryptolib import pubkeyget, pubkeyserialized
import lib.config as cfg

pnconfig = PNConfiguration()
pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = cfg.PUBNUB_UUID
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL

def my_publish_callback(envelope, status):
    if status.is_error(): print(envelope, status)

def translateDealerInput(data):
    msg = data['msg']
    if cfg.INPUT_ROUND_FOLD.match(msg):
        data['cmd'] = RoundPublicInId.FOLD.name
    elif cfg.INPUT_ROUND_CHECK.match(msg):
        data['cmd'] = RoundPublicInId.CHECK.name
    elif cfg.INPUT_ROUND_CALL.match(msg):
        data['cmd'] = RoundPublicInId.CALL.name
    elif (src := cfg.INPUT_ROUND_RAISE.search(msg)):
        data['raise_by'] = int(src.group('raise_by'))
        data['cmd'] = RoundPublicInId.RAISE.name
    elif cfg.INPUT_ROUND_ALLIN.match(msg):
        data['cmd'] = RoundPublicInId.ALLIN.name
    elif cfg.INPUT_TABLE_BUYIN.match(msg): 
        data['cmd'] = TablePublicInId.BUYIN.name
        data['pubk'] = pubkeyserialized(pubkeyget())
    elif cfg.INPUT_TABLE_STARTROUND.match(msg):
        data['cmd'] = TablePublicInId.STARTROUND.name
    elif cfg.INPUT_TABLE_LEAVETABLE.match(msg):
        data['cmd'] = TablePublicInId.LEAVETABLE.name

pubnub.subscribe().channels(channel_name).execute()
while True: 
    data = {'msg': input()}
    translateDealerInput(data)
    pubnub.publish().channel(channel_name).message(
        dumps(data)).pn_async(my_publish_callback)
