import json
import matplotlib.pyplot as plt
import numpy as np
from deprecated import deprecated
from os import listdir
from os.path import isfile, join
import random as r



class Plotter:

    def __init__(self):
        pass

    def getSingleGraph(self, path, title, path_to_save, param, paramtitle):
        json_object = self.getJSON(path)
        title = title
        plot_x_steps = json_object["steps"]
        plot_y_arrived_vehicles = json_object["arrived_vehicles"]
        plot_y_route_length = json_object["route_length"]
        plot_y_loops_made = json_object["loops_made"]

        y_mean = [np.mean(plot_y_route_length)] * len(plot_x_steps)

        fig, ax = plt.subplots()
        ax.set_title(title)
        # z = np.polyfit(plot_x_steps, plot_y_route_length, 1)
        # p = np.poly1d(z)
        # ax.set_yscale("log")

        newlist = self.weightedAverage(json_object[param], 1)
        ax.plot(plot_x_steps, newlist, color="red")  # , marker="o"
        ax.set_xlabel("Simulation Steps")
        #ax.set_ylabel(paramtitle, color="black")
        #ax.plot(plot_x_steps, y_mean, color="red", linestyle='--')

        # ax2 = ax.twinx()
        # ax2.plot(plot_x_steps, plot_y_loops_made, color="blue")
        # ax2.set_ylabel(paramtitle, color="blue")

        #
        # ax3 = ax2.twinx()
        # ax3.plot(plot_x_steps, y_mean, label="mean", linestyle='--')

        plt.show()

        fig.savefig(path_to_save,
                    format="jpeg",
                    dpi=100,
                    bbox_inches='tight')

    def getmultiplegraphs(self, path_to_save, param, yname, N, markerinterval):

        path_list = [f for f in listdir("json") if isfile(join("json", f))]
        for i, path in enumerate(path_list):
            path_list[i] = "json/" + path

        json_objects = list()
        colorlist = [ "darkred", "darkkhaki", "red", "b", "g", "orange", "magenta", "black", "lime"]
        markerlist = ['*',  '|', 'o', 's', 'v', 'd', 'x', 'h']
        for path in path_list:
            json_objects.append(self.getJSON(path))

        x = json_objects[0]["steps"]

        fig, ax = plt.subplots()
        ax.set_title(yname)
        for i, json_object in enumerate(json_objects):
            name = self.getName(path_list[i])
            if N == 1:
                newlist = json_object[param]
            else:
                newlist = self.ownAverage(json_object[param], N)

            #newlist = self.weightedAverage(json_object[param], 1)
            print("last average of " + name + "is: " + str(newlist[-1]))
            ax.plot(x, newlist, color=colorlist[i],
                    label=name, marker=markerlist[i],
                    markevery= [r.randint(markerinterval[0], markerinterval[1])], markersize=8)  # , marker="o" 20000, 30000  80000, 120000
        ax.legend(loc='best')
        ax.set_xlabel("Simulation Steps")
        #ax.set_ylabel(yname, color="black")
        #ax.grid()

        plt.show()

        fig.savefig(path_to_save,
                    format="jpeg",
                    dpi=1200,
                    bbox_inches='tight')

    def getName(self, path):
        path = path.replace("json/justin_backwards_", "")
        path = path.replace(".json", "")
        return path

    def ownAverage(self, plot, N):
        newPlot = list()
        for i, value in enumerate(plot):
            up  = i + N//2
            min = i - N//2
            if min < 0:
                min = 0
            new = plot[min:up]
            average = sum(new)/len(new)
            newPlot.append(average)
        return newPlot

    def weightedAverage(self, plot, N):
        lastN = []
        mylist = plot
        newlist = []

        for i in range(0, len(mylist)):
            lastN.append(mylist[i])
            if i % N == N - 1:
                average = sum(lastN) / N
                for i in range(0, N):
                    newlist.append(average)
                lastN = []
        for i in range(0, len(lastN)):
            average = sum(lastN) / N
            newlist.append(average)
        return newlist

    @deprecated
    def movingAverage(self, plot, N):
        cumsum, moving_aves = [0], []

        for i, x in enumerate(plot, 1):
            cumsum.append(cumsum[i - 1] + x)
            if i >= N:
                moving_ave = (cumsum[i] - cumsum[i - N]) / N
                moving_aves.append(moving_ave)

    def getJSON(self, path):
        with open(path, 'r') as openfile:
            return json.load(openfile)

    def find(self, path):
        return "json/justin_backwards_" + path + ".json"


if __name__ == '__main__':
    p = Plotter()

    #p.getSingleGraph(p.find("standard"),
    #                       "Arrived Vehicles", "plots/final_standard_arrived.jpeg", param="arrived_vehicles", paramtitle="Arrived Vehicles")
    #p.getmultiplegraphs("plots/final_all_new.jpeg", param="new_route_lengths", yname="Weighted Average Vehicle Route Lenght In Roads Taken", N=20000, markerinterval=[20000, 30000])
    p.getmultiplegraphs("plots/final_all_loops_jap.jpeg", param="loops_made", yname="Loops Made", N=1, markerinterval=[80000, 120000])
    #p.getmultiplegraphs([p.find("standard")], "Vehicles Arrived", "plots/final_all_vehicles.jpeg", param="arrived_vehicles", yname="Arrived Vehicles", N=1)
    p.getmultiplegraphs("plots/final_all_jap.jpeg", param="route_length", yname="Average Vehicle Route Length In Roads Taken", N=1, markerinterval=[20000, 30000])
    pass
