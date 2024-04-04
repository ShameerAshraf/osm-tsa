import networkx as nx
import osmnx as ox
import random
import math
from geopy import distance

ALPHA = 0.01
TEMPERATURE = 200
MAX_ITERATIONS = 180
LOCAL_ITERATIONS = 0


# adding speedlimits
def road_class_to_kmph(road_class):
    """
    Returns a speed limit value based on road class, 
    using typical Finnish speed limit values within urban regions.
    """
    if road_class == "motorway":
        return 100
    elif road_class == "motorway_link":
        return 80
    elif road_class in ["trunk", "trunk_link"]:
        return 60
    elif road_class == "service":
        return 30
    elif road_class == "living_street":
        return 20
    else:
        return 50


# do the math
def p_accept_new(t1, t2):
    
    global TEMPERATURE
    global LOCAL_ITERATIONS
    
    LOCAL_ITERATIONS += 1
    TEMPERATURE -= ALPHA * TEMPERATURE

    if LOCAL_ITERATIONS > MAX_ITERATIONS:
        return False 

    if t1 > t2:
        return True
    else:
        delta = t2 - t1
        if random.random() <= math.exp(- delta / TEMPERATURE):
            return True
        return False


# find direction of travel
def travel_headings(G, nodes, route):
    #route = cached_routes[208530977][208531022]

    route_headings = [0, 0, 0, 0]

    for i in range(0, len(route) - 1):
        source = route[i]
        dest = route[i+1]

        source_node = nodes.loc[nodes['id'] == source]
        source_lat =  source_node['lat'].item()
        source_lon = source_node['lon'].item()
        dest_node = nodes.loc[nodes['id'] == dest]
        dest_lat = dest_node['lat'].item()
        dest_lon = dest_node['lon'].item()

        edge_length = G[source][dest][0]["length"]

        WEST = EAST = NORTH = SOUTH = 0

        bearing = ox.bearing.calculate_bearing(source_lat, source_lon, dest_lat, dest_lon)
        angle = math.radians(bearing)

        if bearing < 90:
            EAST = edge_length * math.sin(angle)
            NORTH = edge_length * math.cos(angle)
            #print(f"north: {NORTH} east: {EAST} bearing: {bearing}")
        elif bearing > 270:
            WEST = edge_length * math.cos(angle - (3*math.pi/2))
            NORTH = edge_length * math.sin(angle - (3*math.pi/2))
            #print(f"north: {NORTH} west: {WEST} bearing: {bearing}")
        elif bearing > 180 and bearing < 270:
            WEST = edge_length * math.sin(angle - math.pi)
            SOUTH = edge_length * math.cos(angle - math.pi)
            #print(f"south: {SOUTH} west: {WEST} bearing: {bearing}")
        elif bearing > 90 and bearing < 180:
            EAST = edge_length * math.cos(angle - (math.pi/2))
            SOUTH = edge_length * math.sin(angle - (math.pi/2))
            #print(f"south: {SOUTH} east: {EAST} bearing: {bearing}")
        else:
            match bearing:
                case 0 | 360:
                    NORTH = edge_length
                case 90:
                    EAST = edge_length
                case 180:
                    SOUTH = edge_length
                case 270:
                    WEST = edge_length
            #print(f"never: {NORTH} eat: {EAST} slimy: {SOUTH} worms: {WEST} edge length: {edge_length}")

        route_headings = [x + y for x, y in zip(route_headings, [NORTH, EAST, SOUTH, WEST])]

    return route_headings


# cache length travelled in each direction
def build_cache_direction(G, nodes, cached_routes):
    cached_travel_direction = dict()

    for source, possible_endpoints in cached_routes.items():
        cached_travel_direction[source] = dict()
        for destination, path in possible_endpoints.items():
            path_headings = travel_headings(G, nodes, path)
            
            cached_travel_direction[source][destination] = path_headings

    return cached_travel_direction


# cache routes from source to all destinations
# cache has paths[source][destination] = route[nodes]
def build_cache_routes(G, random_node_ids, algo, nodes):
    # heuristic is prioritizing less distance too much, add speedlimit to improve
    # longitude is 2nd arg
    def h1(a, b):
        nodes.loc[nodes['id'] == a]
        locationa = (nodes.loc[nodes['id'] == a]['lat'].item(), nodes.loc[nodes['id'] == a]['lon'].item())
        locationb = (nodes.loc[nodes['id'] == b]['lat'].item(), nodes.loc[nodes['id'] == b]['lon'].item())
        heuristic = distance.distance(locationa, locationb).m
        return heuristic
    
    cached_routes = dict()

    for u in range(0, len(random_node_ids)):
        cached_routes[random_node_ids[u]] = dict()
        for v in range(0, len(random_node_ids)):
            if u == v:
                continue
            
            if algo == "w":
                route = nx.shortest_path(G, random_node_ids[u], random_node_ids[v], weight="travel_time_seconds")
            elif algo == "a":
                route = nx.astar_path(G, random_node_ids[u], random_node_ids[v], heuristic=h1, weight="travel_time_seconds")
            else:
                route = nx.shortest_path(G, random_node_ids[u], random_node_ids[v], weight="travel_time_seconds")
            # store cached_routes
            cached_routes[random_node_ids[u]][random_node_ids[v]] = route

    return cached_routes


# swap edges in route, check if total length has decreased
def swap_if_less(G, routes, index_1, index_2, total_travel_time):

    if LOCAL_ITERATIONS > MAX_ITERATIONS:
        print("Max iterations reached")
        return routes, total_travel_time, False

    print(f"Old Total Travel Time: {total_travel_time}")

    # create copy of routes to modify and check new travel times
    new_routes = list(routes)
    
    source_1 = new_routes[index_1][0]
    dest_1 = new_routes[index_1][len(new_routes[index_1]) - 1]

    source_2 = new_routes[index_2][0]
    dest_2 = new_routes[index_2][len(new_routes[index_2]) - 1]

    # get new paths from 4d array??

    # todo: reverse either section of loop to find shorter routes "outside" the edges first
    # reverse edges in between
    new_pos = 0
    for i in range(index_1 + 1, index_2):
        temp = nx.shortest_path(G, routes[i][len(routes[i]) - 1], routes[i][0])
        travel_time = nx.path_weight(G, temp, "travel_time_seconds")
        print(f"travel_time_{i}: {travel_time}")
        new_routes[index_2 - 1 - new_pos] = temp
        new_pos += 1

    new_1 = nx.shortest_path(G, source_1, source_2, weight="travel_time_seconds")
    travel_time_1 = nx.path_weight(G, new_1, "travel_time_seconds")
    print(f"travel_time_{index_1}: {travel_time_1}")

    new_2 = nx.shortest_path(G, dest_1, dest_2, weight="travel_time_seconds")
    travel_time_2 = nx.path_weight(G, new_2, "travel_time_seconds")
    print(f"travel_time_{index_2}: {travel_time_2}")

    new_routes[index_1] = new_1
    new_routes[index_2] = new_2

    # check travel time of new_routes
    new_total_travel_time = 0
    for j in range(0, len(new_routes)):
        travel_time = nx.path_weight(G, new_routes[j], "travel_time_seconds")
        print(f"travel_time_{j}: {travel_time}")
        new_total_travel_time += travel_time

    print(f"New Total Travel Time: {new_total_travel_time}")

    # todo: work on function to check if route should be modified
    modifying_route = p_accept_new(total_travel_time, new_total_travel_time)

    if modifying_route:
        return new_routes, new_total_travel_time, modifying_route

    return routes, total_travel_time, False
