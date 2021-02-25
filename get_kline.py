from binance.client import Client
from datetime import datetime
import json, sys, time

API_KEY = 'DqKxvi5wm9oJgx6ksXl5ZpsNXMWDgrDNQxaYytsj1kBy1eODboHxmfaG15WFCpXS'
API_SECRET = 'LMrXojyBMuSHRwQouT7vAAFaL34ht1z8AsvebdNBidbsBdUoqfllMEcTR41FTOUK'

DATA_TIME_INTVAL = Client.KLINE_INTERVAL_1MINUTE
DATA_TIME_ORIG = '2021-02-21 00:00:00'

COINPAIR = 'BNBBUSD'

client = Client(API_KEY, API_SECRET)

print('getting klines')

orig_time = int(datetime.fromisoformat(DATA_TIME_ORIG).timestamp())
data = []

while orig_time < datetime.today().timestamp():
    candles = client.get_klines(symbol = COINPAIR, limit = 1000, \
                                interval = DATA_TIME_INTVAL, \
                                startTime = int(orig_time) * 1000)
    time.sleep(0.2)

    t0 = datetime.fromtimestamp(candles[0][0] // 1000)
    tn = datetime.fromtimestamp(candles[-1][0] // 1000)
    assert(t0.timestamp() == orig_time)
    orig_time = tn.timestamp() + 60 # FIXME: use DATA_TIME_INTVAL

    print('DATA FROM: {} to: {} ({} entries)'.format(t0.strftime('%Y-%m-%d %H:%M'), \
                                                     tn.strftime('%Y-%m-%d %H:%M'),
                                                     len(candles)))

    data += candles

with open(sys.argv[1], 'w') as outfile:
    json.dump(data, outfile)
