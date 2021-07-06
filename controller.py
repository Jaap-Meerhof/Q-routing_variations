import threading

import traci
from tkinter import *
from tkinter import ttk
import time
import json
from sumolib import checkBinary
import os, sys
import multiprocessing.dummy as mp
import multiprocessing
from itertools import product
import random
import matplotlib.pyplot as plt

from view import TinkerGUI
DEEP = True
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

sumoBinary = checkBinary('sumo-gui') #-gui
net = "justin_backwards"
jsonextra = "_DRQ-R_2"
sumoCmd = [sumoBinary, "-c", "networks/" + net + "/" + net + ".sumocfg"]
SUMO_ROADNET_PATH = "networks/" + net + "/" + net + ".net.xml"

QROUTING = True

class Controller:
    STEPS = 30000
    VEHICLES_TO_ROUTE = "CHANGED_EDGE"
    ROUTING_STEP_PERIOD = 10
    road_net = None
    loops = 0
    num_arrived_vehicles = 0
    dist_per_vehicle = 0

    # LOOP_ERASED = False
    # BACK_TRACKING = False
    # NEGATIVE_REWARD = False
    # NEW_NEGATIVE_REWARD = True

    def __init__(self):
        pass

    def get_other_lane(self, name):
        if name.__contains__("-"):
            return name.replace("-", "")
        else:
            return "-" + name
    def getVehicleData(self, running_vehicle_ids):
        """
        Get the speed and the Edge ID of each vehicle active in the current simulation step.
        """
        data = {}

        for vehicle_id in running_vehicle_ids:
            # get the destination edge from the vehicle's preset route
            route_id = traci.vehicle.getRouteID(vehicle_id)
            route = traci.route.getEdges(route_id)
            source_edge_id = route[0]
            dest_edge_id = route[-1]

            status = {"edge_id": traci.vehicle.getRoadID(vehicle_id),
                      "speed": traci.vehicle.getSpeed(vehicle_id),
                      "source_edge_id": source_edge_id,
                      "dest_edge_id": dest_edge_id,
                      "preset_route": route}

            data[vehicle_id] = status
        return data

    def do_simulation(self):
        """
        do a simulation with the settings specified in the file
        :return:
        """
        import traci
        import sumolib
        from node import Node

        traci.start(sumoCmd)

        # init
        self.road_net = sumolib.net.readNet(SUMO_ROADNET_PATH)
        junctions = dict()

        for node in self.road_net.getNodes():  # initialize the nodes
            node_id = node.getID()
            junction = Node(node_id, junctions, self.road_net)
            junctions[node_id] = junction

        plot_x_steps = list()
        plot_y_arrived_vehicles = list()
        plot_y_route_length = list()
        plot_y_loops_made = list()
        plot_y_new_route_lengths = list()
        plot_y_n_arrived_vehicles = list()
        plot_vehicle_min_route = dict()
        plot_y_min_route = list()

        step = 0
        sim_vehicle_data = dict()
        travel_times = dict()
        vehicle_routes = dict()
        vehicle_destinations = dict()
        lenght_made_routes = list()

        percentage = 0
        while step < (self.STEPS * 5):
            # print(step)
            plot_x_steps.append(step)
            step += 1
            oldpercentage = percentage
            percentage = int((step * 100) / (self.STEPS * 5))
            if oldpercentage != percentage:
                print(str(percentage) + "% into simulation")

            running_vehicle_ids = traci.vehicle.getIDList()
            departed_vehicle_ids = traci.simulation.getDepartedIDList()
            arrived_vehicle_ids = traci.simulation.getArrivedIDList()
            data = self.getVehicleData(running_vehicle_ids)

            for vehicle_id in departed_vehicle_ids:
                sim_vehicle_data[vehicle_id] = {"edge_id": data[vehicle_id]["edge_id"]}
                if not travel_times.__contains__(vehicle_id):
                    travel_times[vehicle_id] = traci.simulation.getTime()
                # get IDs of vehicles that changed edge
            vehicles_changed_edge = []
            for vehicle_id in data:
                if data[vehicle_id]["edge_id"] != sim_vehicle_data[vehicle_id]["edge_id"] and not "J" in \
                                                                                                  data[vehicle_id][
                                                                                                      "edge_id"]:
                    vehicles_changed_edge.append(vehicle_id)
                    sim_vehicle_data[vehicle_id]["edge_id"] = data[vehicle_id]["edge_id"]
                # update current routes

                # saves the initial route's destination and sets the route taken so far as the route the car is
                # initially on
                if not vehicle_routes.keys().__contains__(vehicle_id):  # init a vehicle
                    route_id = traci.vehicle.getRouteID(vehicle_id)
                    route = traci.route.getEdges(route_id)
                    plot_vehicle_min_route[vehicle_id] = len(route)
                    source_edge_id = route[0]
                    if QROUTING:
                        vehicle_routes[vehicle_id] = [source_edge_id]
                    else:
                        vehicle_routes[vehicle_id] = route
                    destination_edge_id = route[-1]
                    destination_edge = self.road_net.getEdge(destination_edge_id)
                    destination_junction_id = destination_edge.getToNode().getID()
                    vehicle_destinations[vehicle_id] = destination_junction_id
                    traci.vehicle.setColor(vehicle_id, (
                        random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)))

            # determine vehicles that are going to be routed in this step
            vehicles_to_route = None
            if self.VEHICLES_TO_ROUTE == "CHANGED_EDGE":
                vehicles_to_route = vehicles_changed_edge
            elif self.VEHICLES_TO_ROUTE == "ONLY_DEPARTED":
                vehicles_to_route = departed_vehicle_ids
            elif self.VEHICLES_TO_ROUTE == "PERIODICAL_STEP":
                if step % self.ROUTING_STEP_PERIOD == 0:  # this will trigger when step = 0 as well
                    vehicles_to_route = []
                    for vehicle_id in data:
                        if not "n" in data[vehicle_id]["edge_id"]:
                            vehicles_to_route.append(vehicle_id)
                else:
                    vehicles_to_route = []
            else:
                assert False, "wrong ROUTE_VEHICLE value"

            if len(arrived_vehicle_ids) > 0:
                routes_this_sim = list()
                for vehicle_id in arrived_vehicle_ids:
                    edge_id = vehicle_routes[vehicle_id][-1]
                    time_start = travel_times[vehicle_id]
                    x = traci.simulation.getTime()
                    y = x - time_start
                    edge = self.road_net.getEdge(edge_id)
                    otheredge = self.road_net.getEdge(self.get_other_lane(edge_id))
                    toNode_id = edge.getToNode().getID()
                    fromNode_id = edge.getFromNode().getID()
                    route_so_far = vehicle_routes[vehicle_id]
                    junctions[fromNode_id].updateQTable(y, edge, toNode_id, route_so_far)
                    if DEEP: # fromNode_id should be start of road taken
                        start = self.road_net.getEdge(route_so_far[0]).getFromNode().getID()
                        junctions[toNode_id].updateQTable(y, otheredge, start, route_so_far) # REMOVE

                    plot_y_min_route.append(plot_vehicle_min_route[vehicle_id])
                    plot_vehicle_min_route.pop(vehicle_id)

                    route_so_far = vehicle_routes[vehicle_id]
                    if len(route_so_far) != len(set(route_so_far)):
                        total = 0
                        for item in set(route_so_far):
                            total = route_so_far.count(item)
                        self.loops += total
                    lenght_made_routes.append(len(route_so_far))
                    routes_this_sim.append(len(route_so_far))
                # plot average

                plot_y_new_route_lengths.append(sum(routes_this_sim)/len(routes_this_sim))
            else:
                if len(plot_y_new_route_lengths) == 0:
                    plot_y_new_route_lengths.append(0)
                else:
                    plot_y_new_route_lengths.append(plot_y_new_route_lengths[-1])

            if len(lenght_made_routes) == 0:
                plot_y_route_length.append(self.dist_per_vehicle)
            else:
                self.dist_per_vehicle = sum(lenght_made_routes) / len(lenght_made_routes)
                plot_y_route_length.append(self.dist_per_vehicle)

            # override the preset route of all just departed vehicles with q-routing routes
            new_route_so_far = 0
            if len(vehicles_to_route) > 0 and QROUTING:
                # self.dist_per_vehicle = 0
                new_dist_vehicles = 0
                for vehicle_id in vehicles_to_route:

                    new_route_so_far += len(vehicle_routes[vehicle_id])

                    source_edge_id = data[vehicle_id]["edge_id"]
                    dest_junction_id = vehicle_destinations[vehicle_id]
                    junctionID = self.road_net.getEdge(source_edge_id).getToNode().getID()
                    route = None

                    route = junctions[junctionID].get_route(source_edge_id,
                                                            vehicle_routes[vehicle_id], junctions,
                                                            dest_junction_id)
                    if route is None:
                        raise Exception('route is None!')
                    # update route with new found edge
                    old = vehicle_routes[vehicle_id]
                    old.append(route[0])
                    vehicle_routes[vehicle_id] = old

                    traci.vehicle.setRoute(vehicle_id, route)

                    # update Q_tables
                    current_time = traci.simulation.getTime()
                    travel_time_before = travel_times[vehicle_id]
                    travel_time = current_time - travel_time_before

                    route_so_far = vehicle_routes[vehicle_id]
                    traveled_edge_id = route_so_far[route_so_far.__len__() - 2]
                    traveled_edge = self.road_net.getEdge(traveled_edge_id)
                    other_edge = self.road_net.getEdge(self.get_other_lane(traveled_edge_id))

                    from_Node = junctions[traveled_edge.getFromNode().getID()]
                    to_Node = junctions[traveled_edge.getToNode().getID()]
                    # did i make a loop?

                    from_Node.updateQTable(travel_time, traveled_edge, dest_junction_id, route_so_far)
                    if DEEP: # dest_junction_id should be start
                        start = self.road_net.getEdge(route_so_far[0]).getFromNode().getID()
                        to_Node.updateQTable(travel_time, other_edge, start, route_so_far)

                    travel_times[vehicle_id] = traci.simulation.getTime()

            # send a status record for every RUNNING vehicle in this time step to the Stream Service
            # logger.info("sending status for running vehicles")
            # for vehicle in data.keys():
            #     if not "n" in data[vehicle][
            #         "edge_id"]:  # TODO: this is a hack, since getRoadId() not only returns edge IDs but also node IDs. review.
            #         pass
            #         # endpoint.send_status(vehicle_id=vehicle, edge_id=data[vehicle]["edge_id"], speed=data[vehicle]["speed"], dest_edge_id=data[vehicle]["dest_edge_id"])
            #         # c.incr('sent-vehicle-statuses')

            self.num_arrived_vehicles = self.num_arrived_vehicles + len(arrived_vehicle_ids)
            plot_y_arrived_vehicles.append(self.num_arrived_vehicles)

            #plot_y_n_arrived_vehicles.append(self.num_arrived_vehicles)

            traci.simulationStep()

            plot_y_loops_made.append(self.loops)

        # logger.info("simulation done.")
        traci.close()

        # yield {"status": "SIMULATION_DONE", "message":"Simulation done."}
        print("done")
        print("amount of loops = " + str(self.loops))
        dictionary = {
            "steps": plot_x_steps,
            "route_length": plot_y_route_length,
            "arrived_vehicles": plot_y_arrived_vehicles,
            "loops_made": plot_y_loops_made,
            "new_route_lengths": plot_y_new_route_lengths
        }
        json_object = json.dumps(dictionary, indent=4)

        with open("json/" + str(net) + jsonextra + ".json", "w") as outfile:
            outfile.write(json_object)

        # plt.plot(plot_x_steps, plot_y_route_length)
        # plt.twinx().set_ylabel('right Y label')
        # plt.show()


if __name__ == "__main__":
    # View =  threading.Thread(target=TinkerGUI())
    # View.start()

    controller = Controller()
    controller.do_simulation()

