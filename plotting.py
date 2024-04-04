# todo: define on click function(s)

# todo: define getting nodes from clicks

# create route_colors for number of points
def create_roc(num_of_points):
    colors = ["r", "g", "b"]
    route_colors = []
    for x in range(0, num_of_points, 3):
        for x in colors: route_colors.append(x)
    return route_colors[:num_of_points]

# create route_colors for number of points with color
def create_roc_with(num_of_points, color):
    route_colors = []
    for x in range(0, num_of_points):
        route_colors.append(color)

# create route_colors for route with swapped edges
def create_roc_swapped(num_of_points, index1, index2):
    route_colors = []
    for x in range(0, num_of_points):
        route_colors.append("r")
    route_colors[index1] = "b"
    route_colors[index2] = "b"
    for i in range(index1 + 1, index2):
        route_colors[i] = "y"
    return route_colors