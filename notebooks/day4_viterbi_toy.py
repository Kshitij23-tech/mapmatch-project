import numpy as np

d = np.array([[4, 9], [6, 7], [8, 5], [3, 10]])     # metres from each point to (main road, service road)
sigma, switch_cost = 5.0, 3
emit = -0.5 * (d / sigma) ** 2
score = emit[0].copy()
back = []
for t in range(1, len(d)):
    stay = score
    move = score[::-1] - switch_cost                 # arrive from the other road, pay the switch cost
    prev = np.where(stay >= move, [0, 1], [1, 0])    # best previous road for each current road
    score = np.maximum(stay, move) + emit[t]
    back.append(prev)
state = int(np.argmax(score))
path = [state]
for prev in reversed(back):
    state = int(prev[state])
    path.append(state)
print("viterbi:", path[::-1], " nearest:", d.argmin(axis=1).tolist())