import numpy as np
import sumolib

import random

SUMO_ROADNET_PATH = "net.net.xml"
ETA = 0.5
JAAP = False


class Node:
    id = -1
    outgoing_junctions = None
    road_net = None
    outgoing_edges = None
    nodes = None
    node = None
    LOOP_ERASED = False
    BACK_TRACKING = False
    NEGATIVE_REWARD = False
    NEW_NEGATIVE_REWARD = False
    # qtable = {neighbour : {destination, value}}
    qTable = {}

    def getID(self):
        return self.id

    def __init__(self, id, junctions, road_net, loop=False, negative=True,  new_negative=False):
        self.id = id
        self.road_net = road_net
        self.junctions = junctions
        self.node = self.road_net.getNode(self.id)
        self.nodes = self.road_net.getNodes()
        self.outgoing_edges = self.node.getOutgoing()
        self.LOOP_ERASED = loop
        self.NEGATIVE_REWARD = negative
        self.NEW_NEGATIVE_REWARD = new_negative
        # self.outgoing_nodes = self.outgoing_edges.getToNode().getID()

        self.initQTable()

    def initQTable(self):
        node_outgoing_edges = self.outgoing_edges
        self.qTable = dict()
        for junction_outgoing_edge in self.outgoing_edges:
            # nei_node_id = junction_outgoing_edge.getToNode().getID()
            self.qTable[junction_outgoing_edge.getID()] = dict()

            for dest_node in self.nodes:
                self.qTable[junction_outgoing_edge.getID()][dest_node.getID()] = np.random.uniform(10 ** (-20),
                                                                                                   10 ** (-16))

    def updateQTable(self, travel_time, taken_edge, destination_id, route_so_far):
        severety = route_so_far.count(taken_edge.getID())

        node_end_road = self.junctions[taken_edge.getToNode().getID()]

        old = self.qTable[taken_edge.getID()][destination_id]
        if JAAP:
            if node_end_road.getID() == destination_id:
                t = 0
            else:
                t = node_end_road.get_best_cost(destination_id)
            new = old + ETA * ((travel_time + t) - old)
            self.qTable[taken_edge.getID()][destination_id] = new
        else:
            for node in self.road_net.getNodes():
                destination_id = node.getID()

                old = self.qTable[taken_edge.getID()][destination_id]
                if node_end_road.getID() == destination_id:
                    t = 0
                else:
                    t = node_end_road.get_best_cost(destination_id)
                new = old + ETA * ((travel_time + t) - old)
                self.qTable[taken_edge.getID()][destination_id] = new

        if self.NEW_NEGATIVE_REWARD and taken_edge.getID() in route_so_far:
            self.punish(taken_edge.getID(), destination_id, severety)

    def get_route(self, source_edge_id, route_so_far, other_Nodes, original_destination_junction):
        route_so_far = list(route_so_far)
        route = list()
        route.insert(0, source_edge_id)
        best_edge = self.road_net.getEdge(source_edge_id)
        loop_ids = list()
        loop_junctions = list()
        while best_edge.getToNode().getID() != original_destination_junction\
                and len(route) < (len(self.junctions) * 2):
            next_node = best_edge.getToNode()
            junction = self.junctions[next_node.getID()]
            best_edge_list = junction.get_best_edge(original_destination_junction)  # returns sorted list of tuples (edge, value)
            #best_edge = best_edge_list[0][0]

            best = list()
            best_cost = best_edge_list[0][1]
            for tup in best_edge_list:
                if tup[1] > best_cost:
                    break
                best.append(tup[0])
            best_edge = np.random.choice(best)

            if self.BACK_TRACKING:
                pass

            if self.LOOP_ERASED:
                new_loop_ids = None
                if (best_edge.getToNode().getID()) in loop_junctions:
                    best_edge = random.choice(best_edge_list)[0]
                # if best_edge.getID() in loop_ids:
                #     best_edge = random.choice(best_edge_list)[0]
                elif best_edge.getID() in route or best_edge.getID() in route_so_far:  # try find a second best
                    found_alternative = False
                    for i in range(1, len(best_edge_list)):
                        other_edge = best_edge_list[i][0]
                        if not (other_edge.getID() in route) and not (other_edge.getID() in route_so_far):
                            best_edge = other_edge
                            found_alternative = True
                            break
                    if not found_alternative:
                        if best_edge.getID() in route_so_far:
                            pass #best edge is fine we will make a loop
                        else:
                            route, new_loop_ids = self.delete_until(route, best_edge.getID())
                            for id in new_loop_ids:
                                #self.road_net.getEdge(id)
                                if id not in loop_ids:
                                    loop_ids.append(id)
                                junctionid = self.road_net.getEdge(id).getFromNode().getID()
                                if junctionid not in loop_junctions:
                                    loop_junctions.append(junctionid)
            if self.NEGATIVE_REWARD:
                if best_edge.getID() in route:
                    route = self.negative_reward(route, best_edge.getID(), other_Nodes, destination_node_id=original_destination_junction)
            route.append(best_edge.getID())
        return route

    def get_best_edge(self, dest_junction_id):
        min_cost = np.inf
        best_edge_list = []
        best_nei_edge = None
        for junction_outgoing_edge in self.outgoing_edges:
            # nei_node_id = junction_outgoing_edge.getToNode().getID()
            cost = self.qTable[junction_outgoing_edge.getID()][dest_junction_id]
            best_edge_list.append((junction_outgoing_edge, cost))
        best_edge_list.sort(key=lambda a: a[1])
        return best_edge_list

    def get_best_cost(self, destination_id):
        min = np.inf
        for outEdge in self.outgoing_edges:
            cost = self.qTable[outEdge.getID()][destination_id]
            if cost < min:
                min = cost
        if min == np.inf:
            raise Exception("get_best_cost in node.py could not find a better value than np.inf")
        return min

    def delete_until(self, route, edge_id):
        loop_edges_id = list()
        #loop_edges_id.append(route[-1])
        for i in range(len(route) - 1, -1, -1):
            route_edge = route[i]
            route.pop(i)
            loop_edges_id.append(route_edge) #maybe behind return?
            if route_edge == edge_id:
                #loop_edges_id.append(route_edge)
                return route, loop_edges_id
        return route, loop_edges_id

    def negative_reward(self, route, best_id, other_Nodes, destination_node_id):
        original_length = len(route)
        for i in range(len(route) - 1, -1, -1):
            route_edge_id = route[i]
            route.pop(i)
            route_edge = self.road_net.getEdge(route_edge_id)
            from_Node = other_Nodes[route_edge.getFromNode().getID()]
            #if i == original_length - 2:
            from_Node.punish(route_edge_id, destination_node_id, 0)
            if route_edge_id == best_id:
                return route

        return route

    def punish(self, route_edge_id, destination_node_id, severety=0):
        old_q_value = self.qTable[route_edge_id][destination_node_id]
        new_q_value = (old_q_value * 1.05) + (2*severety)
        max = self.get_max_q_value(destination_node_id)
        if new_q_value > max:
            new_q_value = max
        self.qTable[route_edge_id][destination_node_id] = new_q_value

    def get_max_q_value(self, destination_node_id):
        max = -np.inf
        for route_edge_id in self.qTable.keys():
            cost = self.qTable[route_edge_id][destination_node_id]
            if cost > max:
                max = cost
        return max
