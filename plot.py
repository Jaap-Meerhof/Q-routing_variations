import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Opening JSON file
with open('justin_backwards_normal.json', 'r') as openfile:
    # Reading from json file
    json_object = json.load(openfile)
title = "normal justin"
plot_x_steps = json_object["steps"]
plot_y_arrived_vehicles = json_object["arrived_vehicles"]
plot_y_route_length = json_object["route_length"]
plot_y_loops_made = json_object["loops_made"]
y_mean = [np.mean(plot_y_route_length)] * len(plot_x_steps)

N = 1

cumsum, moving_aves = [0], []

for i, x in enumerate(plot_y_route_length, 1):
    cumsum.append(cumsum[i - 1] + x)
    if i >= N:
        moving_ave = (cumsum[i] - cumsum[i - N]) / N
        moving_aves.append(moving_ave)

lastN = []
mylist = plot_y_route_length
newlist = []

for i in range(0, len(mylist)):
    lastN.append(mylist[i])
    if i % N == N-1:
        average = sum(lastN)/N
        for i in range(0, N):
            newlist.append(average)
        lastN = []
for i in range(0, len(lastN)):
    average = sum(lastN) / N
    newlist.append(average)


fig, ax = plt.subplots()
ax.set_title(title)
z = np.polyfit(plot_x_steps, plot_y_route_length, 1)
p = np.poly1d(z)
#ax.set_yscale("log")

ax.plot(plot_x_steps, newlist, color="red")  # , marker="o"
ax.set_xlabel("SUMO steps")
ax.set_ylabel("average vehicle route on arrival", color="red")
ax.plot(plot_x_steps, y_mean, color="red", linestyle='--')

ax2 = ax.twinx()
ax2.plot(plot_x_steps, plot_y_loops_made, color="blue")
ax2.set_ylabel("amount of loops in final routes", color="blue")

#
# ax3 = ax2.twinx()
# ax3.plot(plot_x_steps, y_mean, label="mean", linestyle='--')

plt.show()
fig.savefig('plots/negative_2.jpeg',
            format="jpeg",
            dpi=100,
            bbox_inches='tight')
