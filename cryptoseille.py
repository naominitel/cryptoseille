import json, sys, math
from hmmlearn import hmm

with open(sys.argv[1]) as infile:
    candles = json.load(infile)

# parse and convert data to 3D vectors and find min and max
# of the value range
# component 0: % change of the price (close - open) / open
# component 1: % amplitude high (high - open) / open (>= 0)
# component 2: % amplitude low (open - low) / open (>= 0)
data = []
min_ = [0, 0, 0]
max_ = [0, 0, 0]
for bar in candles:
    open = float(bar[1])
    high = float(bar[2])
    low = float(bar[3])
    close = float(bar[4])

    frac_change = (close - open) / open * 100
    frac_high = (high - open) / open * 100
    frac_low = (open - low) / open * 100

    max_[0] = max(max_[0], frac_change)
    max_[1] = max(max_[1], frac_high)
    max_[2] = max(max_[2], frac_low)
    min_[0] = min(min_[0], frac_change)
    min_[1] = min(min_[1], frac_high)
    min_[2] = min(min_[2], frac_low)

    # print("data: franc_change: {}, frac_high: {}, frac_low: {}" \
    #         .format(frac_change, frac_high, frac_low))
    data.append([ frac_change, frac_high, frac_low ])

model = hmm.GMMHMM(n_components = 4, covariance_type='full', \
                   n_iter = 100, n_mix = 5, algorithm="map")
model.fit(data[:3000], [3000])

print(model.monitor_)
print(model.monitor_.converged)
print(model.score(data[:3000], [3000]))
print(model.monitor_)
print(model.monitor_.converged)

print("=== inferred hmm params:")
print(" states: {}".format(model.n_components))
print(" gaussian mix components: {}".format(model.n_mix))
print(" data dimentions: {}".format(model.n_features))

print("=== per-state weights of mix components:")
print(model.weights_)
print("=== per-state/mix means of gaussian components:")
print(model.means_)
print("=== per-state/mix covariance of gaussian components:")
print(model.covars_)

#exit(0)

# possible values intervals that we try to test the
# model with to predict the future values
step_change = (max_[0] - min_[0]) / 10
step_high = (max_[1] - min_[1]) / 10
step_low = (max_[2] - min_[2]) / 10
futures = []
for i in range(0, 10):
    change = min_[0] + i * step_change
    for j in range(0, 10):
        high = min_[1] + j * step_high
        for k in range(0, 10):
            low = min_[2] + k * step_low
            futures.append([ change, high, low ])

# test data: for every 10 days window sequence of data
# try to predict the 11th day value by computing the max
# log-likelihood of the 11-day sequence for any possible
# 11th value from futures
# don't use training data:
test_data = data[3000:]
for i in range(0, 100):
    # 10 = days of the data window
    data_seq = test_data[i:i+10]

    max_ll = 0
    best_guess = []
    for f in futures:
        seq = data_seq + [f]
        ll = model.score(seq, [len(seq)])
        #print("test with {}: {}".format(f, ll))
        if ll > max_ll:
            max_ll = ll
            best_guess = f

    # compare with actual value
    obs = test_data[i + 10]
    print("guess: {}, actual: {}, ll={}".format(best_guess, obs, max_ll))
