import pyrosm
import os
import matplotlib.pyplot as plt
import osmnx as ox
import networkx as nx
import pandas as pd
import random

from pdb import set_trace as qwe

from multiprocessing import Process

from routes import *
from plotting import *

POINTS_IN_ROUTE = 5

def route_verifier(routes):
    for i in range(0, len(routes) - 1):
        if routes[i][len(routes[i]) - 1] != routes[i+1][0]:
            print(f"Error in comparing {i} and {i+1}")
            return False

    if routes[len(routes) - 1][len(routes[len(routes) - 1]) - 1] != routes[0][0]:
            print(f"Error in comparing last and first")
            return False

    return True


def plot_async(G, routes, route_colors, travel_time):
    fig, ax = ox.plot_graph_routes(G, routes, 
    route_colors=route_colors, 
    route_linewidth=6, node_size=0,
    show=False, close=False)

    fig.suptitle(f"Travel time: {travel_time} seconds")
    plt.show()

def plot_async_single(G, route):
    fig, ax = ox.plot_graph_route(G, route, show=False, close=False)
    fig.suptitle(f"Single route for verification")
    plt.show()

def main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    TARGET_FILE = "micro-Toronto.osm.pbf"

    print(os.path.join(dir_path, TARGET_FILE))

    # Initialize the OSM object 
    osm = pyrosm.OSM(TARGET_FILE)

    nodes, edges = osm.get_network(network_type="driving", nodes=True)

    # Plot the data
    #ax = edges.plot(figsize=(10,10), color="gray", lw=1.0)
    #ax = nodes.plot(ax=ax, color="red", markersize=2)

    # Zoom in to take a closer look
    #ax.set_xlim([24.9375, 24.945])
    #ax.set_ylim([60.17, 60.173])

    # Separate rows with / without speed limit information 
    mask = edges["maxspeed"].isnull()
    edges_without_maxspeed = edges.loc[mask].copy()
    edges_with_maxspeed = edges.loc[~mask].copy()

    # Apply the function and update the maxspeed
    edges_without_maxspeed["maxspeed"] = edges_without_maxspeed["highway"].apply(road_class_to_kmph)
    #edges_without_maxspeed.head(5).loc[:, ["maxspeed", "highway"]]

    # merge with/without speed
    edges = pd.concat([edges_with_maxspeed, edges_without_maxspeed])
    edges["maxspeed"] = edges["maxspeed"].astype(int)

    #visualize maxspeed on map
    #ax = edges.plot(column="maxspeed", figsize=(10,10), legend=True)

    # assign travel time for edges
    edges["travel_time_seconds"] = edges["length"] / (edges["maxspeed"]/3.6)

    # create G
    G = osm.to_graph(nodes, edges, graph_type="networkx")

    # generate random points, get nearest nodes
    random_points = ox.utils_geo.sample_points(G, POINTS_IN_ROUTE)
    random_node_ids = ox.distance.nearest_nodes(G, random_points.x.values, random_points.y.values)

    # cache has paths[source][destination] = route[nodes]
    # time both ways of creating cache

    # time_1_w
    cached_routes = build_cache_routes(G, random_node_ids, "w", nodes)
    # time_2_w

    # time_1_a
    cached_astar = build_cache_routes(G, random_node_ids, "a", nodes)
    # time_2_a

    # create cache_travel_direction = [source][destination] = [NORTH, EAST, SOUTH, WEST]
    cached_travel_w = build_cache_direction(G, nodes, cached_routes)
    cached_travel_a = build_cache_direction(G, nodes, cached_astar)

    routes, total_travel_time = create_path(G, cached_routes, random_node_ids)

    #route_headings = cached_travel_direction[source][dest]
    #print(route_headings)

    route_colors = create_roc(POINTS_IN_ROUTE)

    # plot routes
    draw = Process(target=plot_async, args=(G, routes, route_colors, total_travel_time))
    draw.start()

    loop = True
    while loop:

        qwe()

        #in_string = input("Enter any index to continue OR quit to quit\n")
        #if in_string == "quit":
        #    break

        #draw async
        #draw = Process(target=plot_async, args=(G, cached_routes, random_node_ids[index_1]))
        if loop:
            draw = Process(target=plot_async, args=(G, routes, route_colors, total_travel_time))
            draw.start()


    print("\n ### CLOSE ALL GRAPH WINDOWS ###\n")
    draw.join()

if __name__ == '__main__':
    main()