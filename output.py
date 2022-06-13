from json import loads 

from pubnub.callbacks import SubscribeCallback
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

from pokerlib.pokerlib.enums import *

from lib.cryptolib import decrypt, prvkeyget
import lib.config as cfg


pnconfig = PNConfiguration()
pnconfig.subscribe_key = cfg.PUBNUB_SUBSCRIBEKEY
pnconfig.publish_key = cfg.PUBNUB_PUBLISHKEY
pnconfig.uuid = cfg.PUBNUB_UUID
pubnub = PubNub(pnconfig)

channel_name = cfg.PUBNUB_POKERCHANNEL

class SubscribeHandler(SubscribeCallback):
    
    def message(self, pubnub, message):
        msg = message.message
        pub = message.publisher
        
        if pub == 'dealer':
            for d in loads(msg):
                
                if d['visibility'] == 'public': pass
                elif d['visibility'] == cfg.PUBNUB_UUID:
                    if (pf := d.get('private_field')):
                        prv = prvkeyget()
                        d[pf] = decrypt(prv, d[pf])
                else: continue
                
                self.formatPokerData(d)
                msg = self.processDealerMessage(d)
                print(f'{pub}: {msg}')      
        else: 
            try:
                data = loads(msg)
                print(f"{pub}: {data['msg']}")
            except Exception as e: print(e)

    @classmethod
    def formatPokerData(cls, data):
        out_id = data['out_id']
        if out_id == RoundPublicOutId.NEWTURN.name:
            data['board'] = cls.cardrepr(data['board'])
            data['turn'] = cfg.REPR_POKER_TURN[data['turn']]
        elif out_id == RoundPublicOutId.PUBLICCARDSHOW.name:
            data['cards'] = cls.cardrepr(data['cards'])
        elif out_id == RoundPublicOutId.DECLAREFINISHEDWINNER.name:
            data['cards'] = cls.cardrepr(data['cards'])
            data['hand'] = cls.cardrepr(data['hand'])
            data['handname'] = cfg.REPR_POKER_HAND[data['handname']]
        elif out_id == RoundPrivateOutId.DEALTCARDS.name:
            data['cards'] = cls.cardrepr(eval(data['cards']))

    @staticmethod
    def processDealerMessage(data):
        out_id = data['out_id']
        if out_id in RoundPublicOutId.__members__:
            msg = getattr(cfg, 'OUTPUT_ROUND_PUBLIC_' + out_id)
        elif out_id in RoundPrivateOutId.__members__:
            msg = getattr(cfg, 'OUTPUT_ROUND_PRIVATE_' + out_id)
        elif out_id in TablePublicOutId.__members__:
            msg = getattr(cfg, 'OUTPUT_TABLE_PUBLIC_' + out_id)
        else: return print('error', out_id)
        return msg.format(**data)

    @staticmethod
    def cardrepr(cards):
        return ' '.join([
            cfg.REPR_POKER_RANK[int(r)] + 
            cfg.REPR_POKER_SUIT[int(s)] 
            for r, s in cards
        ])

pubnub.add_listener(SubscribeHandler())
pubnub.subscribe().channels(channel_name).execute()
