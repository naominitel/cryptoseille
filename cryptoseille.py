from binance.client import Client
from datetime import datetime
import json, sys

with open(sys.argv[1]) as infile:
    candles = json.load(infile)

class Diff:
    # a diff between two bars of the curve
    # open: diff between the start values of the bars
    # close: diff between the final values of the bars
    # high: diff between the max value of the bars' amplitude
    # low: diff between the min value of the bars' amplitude
    # vol: the volume (in currency) of transaction of the bar's timespan
    # trades: number of trades during the bar's timespan
    def __init__(self, present, past):
        self.time   = datetime.fromtimestamp(present[0] // 1000)
        self.open   = (float(present[1]) - float(past[1])) * 100 / float(past[1])
        self.high   = (float(present[2]) - float(past[2])) * 100 / float(past[2])
        self.low    = (float(present[3]) - float(past[3])) * 100 / float(past[3])
        self.close  = (float(present[4]) - float(past[4])) * 100 / float(past[4])
        self.vol    = float(present[7])
        self.trades = present[8]

data = []
diff_min = Diff(candles[1], candles[0])
diff_max = Diff(candles[1], candles[0])

for i in range(1, len(candles)):
    d = Diff(candles[i], candles[i-1])
    data.append(d)

    print('{}: OPEN: {:+f}%, CLOSE: {:+f}%, HIGH: {:+f}%, LOW: {:+f}%, VOL: {}, TRADES: {}' \
            .format(d.time.strftime('%Y-%m-%d %H:%M'), \
            d.open, d.close, d.high, d.low, d.vol, d.trades))

    diff_min.open = min(diff_min.open, d.open)
    diff_min.close = min(diff_min.close, d.close)
    diff_min.high = min(diff_min.high, d.high)
    diff_min.low = min(diff_min.low, d.low)
    diff_min.vol = min(diff_min.vol, d.vol)
    diff_min.trades = min(diff_min.trades, d.trades)

    diff_max.open = max(diff_max.open, d.open)
    diff_max.close = max(diff_max.close, d.close)
    diff_max.high = max(diff_max.high, d.high)
    diff_max.low = max(diff_max.low, d.low)
    diff_max.vol = max(diff_max.vol, d.vol)
    diff_max.trades = max(diff_max.trades, d.trades)

print('OPEN:   MIN: {:+f}%, MAX: {:+f}%'.format(diff_min.open, diff_max.open))
print('CLOSE:  MIN: {:+f}%, MAX: {:+f}%'.format(diff_min.close, diff_max.close))
print('HIGH:   MIN: {:+f}%, MAX: {:+f}%'.format(diff_min.high, diff_max.high))
print('LOW:    MIN: {:+f}%, MAX: {:+f}%'.format(diff_min.low, diff_max.low))
print('VOL:    MIN: {:+f}, MAX: {:+f}'.format(diff_min.vol, diff_max.vol))
print('TRADES: MIN: {:+f}, MAX: {:+f}'.format(diff_min.trades, diff_max.trades))

percentiles=[]
ncentiles = 10

for i in range(0, ncentiles):
    percentiles.append(0)

for d in data:
    r = diff_max.open - diff_min.open
    percentile = int((d.open - diff_min.open) * 100 / r) // (100 // ncentiles)
    percentile = min(percentile, ncentiles - 1)
    percentiles[percentile] += 1

for i in range(0, ncentiles):
    r = ((diff_max.open - diff_min.open) / (100 // ncentiles))
    lo = diff_min.open + i * r
    hi = diff_min.open + (i + 1) * r
    prob = percentiles[i] / len(data)
    print('percentile {}: {} values, prob = {} (range: {} -> {})'.format(i, percentiles[i], prob * 100, lo, hi))


