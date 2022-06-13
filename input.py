from json import dumps
import re

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
    if status.is_error():
        print(envelope, status)

def translate(data):
    msg = data['msg']
    if cfg.INPUT_ROUND_FOLD.match(msg):
        data['msg'] = RoundPublicInId.FOLD.name
    elif cfg.INPUT_ROUND_CHECK.match(msg):
        data['msg'] = RoundPublicInId.CHECK.name
    elif cfg.INPUT_ROUND_CALL.match(msg):
        data['msg'] = RoundPublicInId.CALL.name
    elif (src := cfg.INPUT_ROUND_RAISE.search(msg)):
        data['raise_by'] = src.group('raise_by')
        data['msg'] = RoundPublicInId.RAISE.name
    elif cfg.INPUT_ROUND_ALLIN.match(msg):
        data['msg'] = RoundPublicInId.ALLIN.name
    elif cfg.INPUT_TABLE_STARTROUND.match(msg):
        data['msg'] = TablePublicInId.STARTROUND.name
    elif cfg.INPUT_TABLE_LEAVETABLE.match(msg):
        data['msg'] = TablePublicInId.LEAVETABLE.name
    elif cfg.INPUT_TABLE_BUYIN.match(msg): 
        data['msg'] = TablePublicInId.BUYIN.name
        data['pubk'] = pubkeyserialized(pubkeyget())

pubnub.subscribe().channels(channel_name).execute()
while True: 
    data = {'msg': input()}
    translate(data)
    pubnub.publish().channel(channel_name).message(
        dumps(data)).pn_async(my_publish_callback)
