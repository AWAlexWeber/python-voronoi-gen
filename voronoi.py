import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d
from scipy.spatial import Delaunay
from collections import defaultdict
import itertools
import random
import math
from biome import Biome
from rock import RockDatabase
from rock import RockLayer
from ocean import Ocean
from mountain_range import MountainRange
from mountain_range import Mountain
from wind import Wind
import noise

# Debug variable
# Debug variable can be changed to speficy exact amount of verbosity
# 1 is the highest, incresing values decrease the verbosity
# Lowest, as of now, is 2
debug = 0
debug_display = 0
status = 1

# Variables controlling oceanic generation
ocean_size_threshold = 1
ocean_merge_threshold = 15

# Variables for controlling elevation generation
water_height_limit = 15

# This value controls how powerful the tectonic plate adjustment is
# A lower value results in a less powerful heights from tectonic plate collision
tectonic_elevation_multiplier = 2.5
immune_threshold = 85

# Mountain growth variables
mountain_offset_angle = 20
mountain_offset_adjustment_angle = 45
mountain_strength_decay = 0.05
mountain_strength_limit = 0.1
mountain_failure_index = 5
max_mountain_neighbor = 2

# Value that controls the elevation control of our mountains
# Lower value makes mountains not as important
mountain_adjustment_strength = 0.4

# Building the rock database since it is used
rockDatabase = RockDatabase()
defaultRock = rockDatabase.defaultRock

# Cycle limits
temp_lower_cycle_limit = 0.5
temp_upper_cycle_limit = 1.5

temp_lower_amplitude = 0.6
temp_upper_amplitude = 1.4

# This is the temperature base level
# Note that we evaluate on a 100-based scale, so this number can, at most, be 100
# A lower number means the average temperature of the world is lower, vice versa applies
# Range is 0 - 100, lower = cooler planet, higher = hotter
temp_base_level = 50

# Modifier that is used to control amplitude
# Higher value means a smaller amplitude
temp_height_division_factor = 16

# Trending factor that lets us control the temperature of the oceans
# Value == 1 is no trend
# Greater than 1 is a downward trend
# Below 1 is an upward trend
ocean_temp_downward_trend = 1.1

# Humidity options
humidity_threshold = 2

# Source threshold, used during random number generation
# This is an absolute value !!! Check before you change (relative to the random number gen)
humidity_source_threshold = 15000

# Fraction defining chance to be a humidity source
humidity_source_chance = (2, 10)

# Ocean wind variables
# Variance in value, in degrees
ocean_wind_variance = 25
ocean_wind_chance = (1, 10)

# Degree of tolerance for selecting adjacent wind to blow into
wind_range = 35
wind_loss_strength = 15
wind_strength_limit = 10
wind_gen_count = 100

# Factor that the difference between regions has on the new wind strength
# It is a numeric percentage
wind_difference_factor = 1.4


# PI variable
PI = 3.14159

# Class maintains the following set of variables
# width, height, count, relaxation_count, random_points, voronoi_points
# This class provides all of the tools to generate a relaxed Voronoi graph of points
class VoronoiWrapper:

    def __init__(self, width, height, count, relaxation_count=0, SEED="None"):

        # We initialiez all the data
        self.width = width
        self.height = height
        self.count = count
        self.relaxation_count = relaxation_count
        self.ocean_set = {}

        # Setting seed
        self.seed = SEED

        # Now we generate the function
        self.generate()

        # Now to run the minimization function on the points
        self.maxmin()

        if (debug >= 2):
            print ("Points: ")
            print (self.random_points)
            print ("Point-Regions by index")
            print (self.voronoi_points.point_region)
            print ("Regions by vertex index")
            print (self.voronoi_points.regions)
            print("Indexes")
            print (self.voronoi_points.vertices)
            print("Voronoi-Held Points")
            print (self.voronoi_points.points)

        # Displaying if debug
        if (debug_display): self.display()

        # Now to run lloyds relaxation
        for x in range(0,self.relaxation_count):
            if status:
                print("Running Lloyds # " + str(x))

            self.lloyds_relaxation()
            self.maxmin()

        # Running neighbors and finalize the connections
        self.genFinalSystem()

        # Displaying if debug
        if (debug_display): self.display()

    def maxmin(self):
        # This function is desgined to take all the voronoi co-ordinates that have
        # positions > or < width/height
        # Counting verticies
        vert_count = 0

        if status:
            print("MaxMin Running")

        for vert in self.voronoi_points.vertices:
            # Checking height and width of first
            x = vert[0]
            if (self.width < x):
                x = self.width
            elif (x < 0):
                x = 0

            y = vert[1]
            if (self.height < y):
                y = self.height
            elif (y < 0):
                y = 0

            # Adjusting
            if (debug == 1): print("Changing ", end = "")
            if (debug == 1): print (vert, end = ", to ")
            if (debug == 1): print((x,y), end="\n")

            self.voronoi_points.vertices[vert_count] = (x,y)
            vert_count+=1

        if status:
            print ("MaxMin Complete")

    def generate(self):

        # First we will generate a list of random points
        self.random_points = []

        # Setting seed
        if (self.seed != "None"):
            np.random.seed(self.seed)

        # Generating self.count number of points
        for x in range(0,self.count):

            if (status):
                if x == self.count / 4:
                    print("Point Generation: 25% Completed")
                if x == self.count / 2:
                    print("Point Generation: 50% Completed")

            # Generating a random point
            xpos = np.random.randint(0,self.width)
            ypos = np.random.randint(0,self.height)

            # After we have generated a point, we add it into self.random_points for use with voronoi
            self.random_points.append((xpos,ypos))

        if status:
            print("Point Generation: Complete")
        # Now we will generate the Voronoi graph
        self.voronoi_points = Voronoi(self.random_points)

        if status:
            print("Voronoi Generation Complete")

    # Outdated functionality that is now handled within genFinalSystem

    # def determine_region_neighbors(self):
    #     # Using the previously determined voronoi data, we will now assign neighbors
    #     # This will create a new list object that references neighbors by region index
    #     if (debug): print("Generating region-based neighbors")

    def lloyds_relaxation(self):
        # Function for running lloyds relaxation
        # Functions by taking the center of the polygon, making the point the center, then re-running the Voronoi

        # Beginning the lloyd relaxation process
        # First, lets iterate on every region
        # Unfortunately, we DO need to count the regional index
        # This is for grabbing points when we have -1 vertices
        region_count = 0

        # Array to change points to
        new_array = []

        # Empty flag to identify empty regions
        emptyFlag = 0

        for region in self.voronoi_points.regions:

            if not region:
                # Empty region, skipping
                # We will need to set the empty flag on to ensure correct identification of points
                emptyFlag = 1

                continue

            # Non empty region
            # Now to iterate on all points
            # X, Y will track the total X, Y, while count is number of verticies
            x = 0
            y = 0
            count = 0

            if (debug == 1): print ("\nNow analyzing region: ", end = "")
            if (debug == 1): print (region)
            if (debug == 1): print ("Our points: " )

            for point_index in region:
                # Incrementing the count
                count += 1

                # First we will check, is the point_index -1 ?
                if point_index == -1:

                    # Okay lets do some basic math and figure out what to apply for this...
                    # First lets get the regional point, need this to calculate it

                    # Voronoi is dumb and puts matching position into region_point
                    # Finding the index of our region count
                    if (debug == 1): print("non-zero, searching for regional index of " + str(region_count + emptyFlag), end = ", ")
                    point_regional_index = np.where(self.voronoi_points.point_region==(emptyFlag + region_count))[0][0]
                    if (debug == 1): print("which is " + str(point_regional_index), end =") ")
                    center = self.voronoi_points.points[point_regional_index]

                    # Okay, we have obtained the center
                    # Now to determine whether to adjust X, Y or both
                    if (debug == 1): print ("(-1,-1), (",end="")
                    if (debug == 1): print (center[0], end = ",")
                    if (debug == 1): print (center[1], end = ")")

                    if (center[0] > (0.5 * self.width)):
                        x += self.width
                        if (debug == 1): print("+width",end="")

                    if (center[1] > (0.5 * self.height)):
                        y += self.height
                        if (debug == 1): print("+height", end="")

                    continue

                # Not a -1 verice
                # Lets grab the point from the indexes
                point = self.voronoi_points.vertices[point_index]
                if (debug == 1): print(point, end = ",")

                # We have grabbed the vertice, lets add to x and y
                x += point[0]
                y += point[1]

            # Fantastic, we have counted the points and the X,Y values
            # Generating final results

            x = x / count
            y = y / count

            # Now lets insert this into the secondary array
            if (debug == 1): print("\nFinal: ", end = "(")
            if (debug == 1): print(x, end=",")
            if (debug == 1): print(y, end=")\n\n")

            new_array.append((x,y))

            # Incrementing regional count
            region_count += 1

        # Alright, we have generated a new array!
        # Lets send it off

        if (debug == 1): print(self.random_points)
        if (debug == 1): print(new_array)

        # Now to adjust our random points to new array and then regen the voronoi
        self.random_points = new_array
        self.voronoi_points = Voronoi(self.random_points)

    def display(self):

        # Plotting it first
        if status:
            print("Draw: Plotting display")
        voronoi_plot_2d(self.voronoi_points)

        if status:
            print("Draw: Colorizing")
        # colorize
        for region in self.voronoi_points.regions:
            if not -1 in region:
                polygon = [self.voronoi_points.vertices[i] for i in region]
                plt.fill(*zip(*polygon))

        if status:
            print("Draw: Showing")

        plt.show()

    def genFinalSystem(self):

        #print(self.voronoi_points.regions)
        #print(self.voronoi_points.vertices)
        #print(self.voronoi_points.points)
        #print(self.voronoi_points.point_region)

        # Overall idea
        # Point_region contains the mapping of index to regions
        # This lets us determine which region is which index

        # Construct a duplicate of regions, but remove the empty set
        # Iterate on every value in point_region
        # Grab the vertices from every value within the respective region

        # point_region contains a mapping of index -> region that represents that index
        # This value, our relative_index keeps track of where we are within point_region
        # Remember, point region goes from 0 to max regions BUT it can be out of order!
        # And we need the in-order to get the center value

        # Newer, also broken system

        # voronoi_output = {}
        # point_region_counter = 0
        # for point in self.voronoi_points.point_region:
        #
        #     #print("Building point with index of " + str(point))
        #     # Grabbing the respective region
        #
        #     respective_region = self.voronoi_points.regions[point]
        #     #print("Our region is " + str(respective_region))
        #
        #     # Grabbing the center for this indexed value
        #     region_center = self.voronoi_points.points[point_region_counter]
        #     #print("Our center is " + str(region_center))
        #
        #     # Building the voronoi object
        #     # Point represents the value we are on in point_region
        #     # Region center is our center
        #     tmp_voronoi = VoronoiRegion(region_center, point)
        #
        #     # Assigning the point list. Note, we are going to simply take the given value
        #     tmp_voronoi.vertex_list_index = respective_region
        #
        #     # Determining our vertex list of indices
        #     # This requires us to actually iterate on the values
        #     vertex_list_value = []
        #     for point_vertex in respective_region:
        #         if point_vertex != -1:
        #             vertex_list_value.append(self.voronoi_points.vertices[point_vertex])
        #
        #     #print(vertex_list_value)
        #     tmp_voronoi.vertex_list_value = vertex_list_value
        #
        #     # Incrementing our point_region counter
        #     point_region_counter = point_region_counter + 1
        #
        #     voronoi_output[point] = tmp_voronoi
        #
        # # Finding the index of the empty set
        # count = 0
        # for point_region in self.voronoi_points.regions:
        #     if len(point_region) <= 0:
        #         break
        #     count = count + 1
        #
        # # Fixing the empty set problem
        # fixed_voronoi_output = [None] * len(self.voronoi_points.point_region)
        # #print("Fixing empty set problem with value of " + str(count))
        # for key in voronoi_output:
        #     region = voronoi_output[key]
        #
        #     new_key = key
        #     if new_key > count:
        #         new_key = new_key - 1
        #
        #     fixed_voronoi_output[new_key] = region
        #
        # #print(fixed_voronoi_output)
        # self.voronoi = fixed_voronoi_output

        # Old broken system

        # First we are going to generate the Voronoi Region Hashtable List
        # The key will be a tuple representing the center
        voronoiRegionList = []

        # Iterating on all regions and creating them

        # Keeping track of what index we have iterated on
        count = 0

        # Keeping track of whether or not we have reached the [] index...
        invalid_index_flag = 0

        for x in self.voronoi_points.points:

            # Creating the new empty object
            tmpRegion = VoronoiRegion(x, count)

            # Getting the current region object
            point_region_index = self.voronoi_points.point_region[count + invalid_index_flag]
            current_region = self.voronoi_points.regions[point_region_index]

            if current_region == []:
                invalid_index_flag = 1
                point_region_index = self.voronoi_points.point_region[count + invalid_index_flag]
                current_region = self.voronoi_points.regions[point_region_index]

            # Getting a proper edge
            if -1 in current_region:
                tmpRegion.edge = 1

            # We have obtained the 'current region'
            # Now we need to take this information and grab all of the vertex information

            vertex_list_value = []
            for point in current_region:
                if point != -1:
                    vertex_list_value.append(self.voronoi_points.vertices[point])

            # Assigning the values to current_region
            tmpRegion.vertex_list_value = vertex_list_value
            tmpRegion.vertex_list_index = self.voronoi_points.regions[count + invalid_index_flag]

            # Appending the object to the list
            voronoiRegionList.append(tmpRegion)

            # Incrementing count
            count = count + 1

        # Assigning the list to ourselves
        self.voronoi = voronoiRegionList

        # Secondly we are going to calculate all of the neighbors

        # Using Delaunay to generate the neighbors from our random points
        tri = Delaunay(self.random_points)
        neiList = defaultdict(set)
        for p in tri.vertices:
            for i, j in itertools.combinations(p, 2):
                neiList[i].add(j)
                neiList[j].add(i)

        #print(neiList)

        if debug:
            print("Printing the neighbor information")
            print("Our vertex set: ")
            print(self.voronoi_points.points)

        # Tracking index
        index = 0

        for key in sorted(neiList.items()):
            # Lets assign the points
            neighbors_index = key[1]

            # Assigning neighbors index
            self.voronoi[index].neighbors_index = neighbors_index
            self.voronoi[index].index = index

            # Incrementing count
            index = index + 1

        #self.debug_region()

        # Finally, regenerating the centers
        for v in self.voronoi:
            # Determining the center
            x = 0
            y = 0
            count = 0

            for point in v.vertex_list_value:
                count = count + 1
                x = x + point[0]
                y = y + point[1]

            x_center = x / count
            y_center = y / count
            v.center = (x_center, y_center)

        #self.debug_region()

    # This function will load all the shape-based biomes
    # Effectively determining what is water and what is not
    def gen_shape_land(self, shapeList):
        if (status):
            print("Generating shapelist based land")

        voronoi_count = len(self.voronoi)
        count = 0

        for voronoi in self.voronoi:
            count = count + 1

            if (count == 1 * (round(voronoi_count) / 4)):
                print("Land Generation: 25% Complete")
            elif (count == 2 * (round(voronoi_count) / 4)):
                print("Land Generation: 50% Complete")
            elif (count == 3 * (round(voronoi_count) / 4)):
                print("Land Generation: 75% Complete")

            # Checking if the positional data has already been set
            if (voronoi.biome.biome_index == 2):
                continue

            for shape in shapeList:
                points = shape.vertex_list

                if (check_point_within_polygon(voronoi.center[0], voronoi.center[1], points)):
                    # Reloading the index to land
                    voronoi.biome.reload_index(2)

                    # Updating this voronois overlap region
                    voronoi.shape_list.append(shape.shape_index)


    # This function will load all the shape-based biomes
    # Effectively determining what is water and what is not
    def gen_shape_water(self, shapeList):
        if (status):
            print("Generating shapelist based water")

        voronoi_count = len(self.voronoi)
        count = 0

        for voronoi in self.voronoi:
            count = count + 1

            if (count == 1 * (round(voronoi_count) / 4) ):
                print("Water Generation: 25% Complete")
            elif (count == 2 * (round(voronoi_count) / 4) ):
                print("Water Generation: 50% Complete")
            elif (count == 3 * (round(voronoi_count) / 4) ):
                print("Water Generation: 75% Complete")

            # Checking if the positional data has already been set
            if (voronoi.biome.biome_index == 1):
                continue

            for shape in shapeList:
                points = shape.vertex_list

                if (check_point_within_polygon(voronoi.center[0], voronoi.center[1], points)):
                    voronoi.biome.reload_index(1)

                    # Updating this voronois overlap region
                    voronoi.shape_list.append(shape.shape_index)


    # Function for generating the voronoi tectonic stone type from the tectonic plate values
    def genRegionRock(self, shapeList):
        for voronoi in self.voronoi:

            if len(voronoi.shape_list) <= 0:
                # No given shapes...
                voronoi.rock_layer = RockLayer(defaultRock)

            elif len(voronoi.shape_list) == 1:
                # Simply use the given one
                shape_object = shapeList[voronoi.shape_list[0]]

                if shape_object.tectonic == 1:
                    new_rock_layer = RockLayer(shapeList[voronoi.shape_list[0]].base_rock)
                    voronoi.rock_layer = new_rock_layer

                else:
                    # Not tectonic? Shit I don't know what to do here, guess its part of the non-tectonic group
                    # Meaning we will use the default option here
                    #print("Assigning non-tectonic region")
                    new_rock_layer = RockLayer(defaultRock)
                    voronoi.rock_layer = new_rock_layer

            else:
                # Generating a random index
                # Assembling list of all the tectonic options, and randomly selecting from them
                tectonic_list = []

                for shape in voronoi.shape_list:
                    if shapeList[shape].tectonic:
                        tectonic_list.append(shapeList[shape])

                # Checking if none of them were tectonic first
                if len(tectonic_list) <= 0:
                    voronoi.rock_layer = RockLayer(defaultRock)

                else:
                    randomIndex = random.randrange(0, len(tectonic_list))
                    new_rock = tectonic_list[randomIndex].base_rock
                    new_rock_layer = RockLayer(new_rock)
                    voronoi.rock_layer = new_rock_layer

    # Function for making one pass on averaging the base heights
    def gen_voronoi_heightmap_average(self, noise, strength):
        print("Performing heightmap averaging function")

        # We have two input parameters, noise and strength
        # Strength is used to determine the amount of power we want to give our averaging tool
        # For example, if our neighboring average is 90 and we are 80, the difference is 10
        # Strength is a multiplier that determines how much we are going to move towards the average

        # Noise is a random variance always applied, between [-noise,noise]

        new_heightmap_list = []

        for region in self.voronoi:

            # Checking if we are an immune region
            if region.elevation > immune_threshold:
                #print("HIT IMMUNE THRESHOLD")
                new_region_elevation = region.elevation
                new_region_elevation = new_region_elevation + random.randrange(-noise, noise)

                biome_type = region.biome.land_type
                if (biome_type == "Water"):
                    # Checking upper/lower bounds
                    if (new_region_elevation > water_height_limit):
                        new_region_elevation = water_height_limit
                if (biome_type == "Land"):
                    if (new_region_elevation <= water_height_limit):
                        new_region_elevation = water_height_limit + 1

                if (region.elevation <= 0):
                    new_region_elevation = 1

                new_heightmap_list.append(new_region_elevation)
                continue

            # Getting the neighboring elevation
            neighbor_elevation = 0
            neighbor_count = len(region.neighbors_index)
            for neighbor in region.neighbors_index:
                neighbor_elevation = neighbor_elevation + self.voronoi[neighbor].elevation

            # Determining the average
            neighbor_elevation_average = neighbor_elevation / neighbor_count

            # Now we calculate the difference
            neighbor_elevation_difference = neighbor_elevation_average - region.elevation

            # Using our strength
            neighbor_elevation_adjustment = neighbor_elevation_difference * strength

            if (debug):
                print("Neighboring average of " + str(neighbor_elevation_average) + ", ours is " + str(region.elevation) + " with difference of " + str(neighbor_elevation_difference) + ". Adjusting by " + str(neighbor_elevation_adjustment))
            new_region_elevation = region.elevation + round(neighbor_elevation_adjustment)

            # Getting our noise in
            new_region_elevation = new_region_elevation + random.randrange(-noise, noise)

            # Finally, making some sanity checks over here
            biome_type = region.biome.land_type
            if (biome_type == "Water"):
                # Checking upper/lower bounds
                if (new_region_elevation > water_height_limit):
                    new_region_elevation = water_height_limit
            if (biome_type == "Land"):
                if (new_region_elevation <= water_height_limit):
                    new_region_elevation = water_height_limit + 1

            if (region.elevation <= 0):
                new_region_elevation = 1

            new_region_elevation = round(new_region_elevation)
            new_heightmap_list.append(new_region_elevation)

        # Now that we've build the new heightmaps lets assign
        count = 0
        for region in self.voronoi:

            region.elevation = new_heightmap_list[count]
            count = count + 1

    # Function for building cool mountain ranges
    # Hopefully this ends up being somewhat realistic, because god knows how many times this doesnt work
    def gen_mountain_ranges(self, mountain_range_count, mountain_height_noise, mountain_range_length_dimension):

        print("Building mountain ranges")
        # Building the mountain set
        mountain_set = {}

        # Building a set of all land tiles
        # Our land key set tracks all of the indexes we have used so we can randomly select one
        # Since we cannot randomly select on a dictionary (in this case land_set)
        land_key_set = []
        land_set = {}

        # Iterating on all regions, if its land putting it into land_set
        for region in self.voronoi:
            if region.biome.land_type == "Land":
                land_set[region.index] = region
                land_key_set.append(region.index)

        # First we will select our root mountain points
        for count in range(0,mountain_range_count):

            if len(land_key_set) <= 0:
                break

            random_index = random.randrange(0, len(land_key_set))
            mountain_root = land_set[land_key_set[random_index]]
            land_key_set.pop(random_index)

            # Selecting a random, non-oceanic tile to be used.
            # Selecting a random angle
            random_angle = random.randrange(0, 360)
            mountain_set[count] = MountainRange(count, mountain_root, random_angle)

        # Okay we've built our mountain set
        # Lets begin growing each mountain
        # This will be done by iterating on each tile currently in the mountain, check its growth status
        # Grown tiles will be ignroed, not grown tiles will grow in their growth direction
        # Hitting water, etc will change the growth direction
        mountain_failure = 0
        while 1 == 1:

            print("Growing mountains")

            # Flag to track mountain growth
            # When we no longer grow anything, its time to stop
            did_grow_mountain = 0

            # Iterating on all mountains
            for mountain_range_index in mountain_set:
                mountain_range = mountain_set[mountain_range_index]

                # Now iterating on all possible tiles that have not been grown yet
                mountain_growth_set = []

                print(len(mountain_range.mountains))
                for mountain_index in mountain_range.mountains:
                    # print("Iterating on mountain with index of " + str(mountain_index))
                    mountain = mountain_range.mountains[mountain_index]
                    mountain_center = mountain.region.center

                    if mountain.grown:
                        continue

                    # Checking for strength decay
                    if mountain.mountain_strength < mountain_strength_limit:
                        mountain.grown = 1
                        continue

                    else:

                        # Time to grow this mountain
                        # Setting us to grown

                        neighbor_set = mountain.region.neighbors_index

                        # We need to pick 1 (or more) that succesfully grows us
                        neighbor_angle_set = {}
                        unfixed_neighbor_angle_set = {}
                        neighbor_mountain_count = 0
                        for neighbor_index in neighbor_set:
                            neighbor = self.voronoi[neighbor_index]

                            # If neighbor is ourselves, skipping
                            if neighbor.index == mountain.region.index:
                                continue

                            # If its an ocean, stop
                            if neighbor.biome.land_type == "Water":
                                continue

                            # Dont grow to ourselves...
                            if neighbor.is_mountain:
                                neighbor_mountain_count = neighbor_mountain_count + 1

                            if neighbor_mountain_count > max_mountain_neighbor:
                                break

                            # Okay lets get the angle from the center of our growth mountain to us...
                            center = neighbor.center

                            # Calculating angle
                            delta_x = mountain_center[0] - center[0]
                            delta_y = mountain_center[1] - center[1]
                            theta_radians = math.atan2(delta_y, delta_x)

                            degree = theta_radians * 180 / PI

                            # If its left of us, we need to add 90
                            unfixed_degree = degree
                            if center[0] < mountain_center[0]:
                                unfixed_degree = 180 - unfixed_degree

                            # If we are underneath than we need to also make some adjustments
                            if center[1] > mountain_center[1]:
                                unfixed_degree = 360 - (180 + unfixed_degree)

                            unfixed_neighbor_angle_set[neighbor.index] = unfixed_degree

                            # Fixing angles less than 0, since we are scrubs
                            if degree < 0:
                                degree = degree + 360

                            # We also care more about reacing 180 degrees as well, so lets subtract 180 for values > 180
                            if degree > 360:
                                degree = degree - 360

                            neighbor_angle_set[neighbor.index] = degree


                        # Checking if any are close enough...
                        for neighbor_index in neighbor_angle_set:
                            growth_angle = mountain.growth_angle
                            growth_range_min = growth_angle - mountain_offset_angle
                            growth_range_max = growth_angle + mountain_offset_angle

                            # Checking for funky stuff
                            neighbor = self.voronoi[neighbor_index]
                            neighbor_angle = neighbor_angle_set[neighbor_index]
                            unfixed_neighbor_angle = int(round(unfixed_neighbor_angle_set[neighbor.index]))

                            growth_flag = 0

                            # Checking for values
                            if growth_range_max > 360:
                                # Checking for beyond the range
                                growth_range_max = growth_range_max - 180
                                if neighbor_angle > 0 and neighbor_angle < growth_range_max:
                                    growth_flag = growth_flag + 1

                            else:
                                if neighbor_angle > growth_angle and neighbor_angle < growth_range_max:
                                    growth_flag = growth_flag + 1

                            # Checking for values
                            if growth_range_min < 0:
                                # Checking for beyond the range
                                growth_range_max = growth_range_max + 180
                                if neighbor_angle < 180 and neighbor_angle > growth_range_min:
                                    growth_flag = growth_flag + 1

                            else:
                                if neighbor_angle < growth_angle and neighbor_angle > growth_range_min:
                                    growth_flag = growth_flag + 1

                            if growth_flag > 0:
                                # Adding this mountain to the mountain set
                                growth_angle = mountain.growth_angle
                                new_mountain_tile = Mountain(neighbor, growth_angle, mountain_range, mountain.mountain_strength - mountain_strength_decay)
                                mountain_growth_set.append(new_mountain_tile)
                                neighbor.is_mountain = 1
                                mountain.grown = mountain.grown + 1

                            # We did not grow! Time to make our growth angle a little weirder...
                            else:
                                # Growth angle adjustment
                                growth_angle = mountain.growth_angle
                                growth_range_min = growth_angle - mountain_offset_adjustment_angle
                                growth_range_max = growth_angle + mountain_offset_adjustment_angle
                                new_growth_angle = random.randrange(growth_range_min, growth_range_max)

                                # Fixing boundary problems
                                if new_growth_angle < 0:
                                    new_growth_angle = new_growth_angle + 360

                                if new_growth_angle > 360:
                                    new_growth_angle = new_growth_angle - 360

                                mountain.growth_angle = int(round(new_growth_angle))


                if len(mountain_growth_set) > 0:
                    for new_mountain in mountain_growth_set:
                        # Growing the mountains
                        mountain_range.mountains[new_mountain.mountain_index] = new_mountain
                        did_grow_mountain = 1
                else:
                    # If we are a new mountain range, lets just fucking randomize our range
                    if len(mountain_range.mountains) <= 1:
                        print("Randomizing mountain angles")
                        random_angle = random.randrange(0, 360)
                        mountain_range.base_growth_angle = random_angle

                        for mountain_index in mountain_range.mountains:
                            mountain_range.mountains[mountain_index].growth_angle = random_angle



            if did_grow_mountain == 0:
                print("Mountain growth failed")
                mountain_failure = mountain_failure + 1

            if mountain_failure > mountain_failure_index:
                break

        # Fixing mountain sizes
        # A very thin, weak mountain should not have a strength of bilions
        for mountain_range_index in mountain_set:
            mountain_range = mountain_set[mountain_range_index]
            min_strength = 100

            for mountain_tile_index in mountain_range.mountains:
                mountain = mountain_range.mountains[mountain_tile_index]

                if mountain.mountain_strength < min_strength:
                    min_strength = mountain.mountain_strength

            for mountain_tile_index in mountain_range.mountains:
                mountain = mountain_range.mountains[mountain_tile_index]
                mountain.mountain_strength = mountain.mountain_strength + mountain_strength_limit - min_strength

            for mountain_tile_index in mountain_range.mountains:
                mountain = mountain_range.mountains[mountain_tile_index]

                for neighbors_index in mountain.region.neighbors_index:
                    neighbor = self.voronoi[neighbors_index]
                    if neighbor.is_mountain:
                        continue

                    else:
                        mountain = mountain_range.mountains[mountain_tile_index]

                        absolute_strength = int(round( (mountain.mountain_strength - mountain_strength_limit) * 100))

                        neighbor.elevation = absolute_strength



        # Now to make those adjustments to the heightmap
        # Again, the mountain ranges are relative adjustments
        # The adjustment factor will be added to the height
        # The absolute_strength will be the mountains strength * 100
        # Adjustment factor will be the difference between the current strength and 100, / 100 * absolute_strength

        for mountain_range_index in mountain_set:
            mountain_range = mountain_set[mountain_range_index]

            for mountain_tile_index in mountain_range.mountains:
                mountain = mountain_range.mountains[mountain_tile_index]

                absolute_strength = int(round(mountain.mountain_strength * 100))
                relative_value = 100 - mountain.region.elevation
                relative_adjustment_value = relative_value / 100
                adjustment_value = relative_adjustment_value * absolute_strength
                adjustment_value = adjustment_value * mountain_adjustment_strength

                mountain.region.elevation = mountain.region.elevation + adjustment_value

        # Finished!
        self.mountain_set = mountain_set
        print("Finished building mountain ranges")

    # Function for generating the voronoi heightmap...
    def gen_voronoi_base_height(self, height_noise, shape_list_size):
        print("Generating voronoi heightmap")

        # Functionally this will process things in the following manner
        # We will iterate on all voronoi regions, and assign them a height based on the following
        # their number of shapes in the shapelist / total number of shapes * 100 + random number between -/+ height_noise

        # There will be a limit however: water biomes will have a limit of being between [0,15]
        # land biomes will have a limit between [15,99]

        for region in self.voronoi:

            # Getting the shape list count
            num_shape = len(region.shape_list)
            mult = tectonic_elevation_multiplier * num_shape / shape_list_size

            if (mult >= 1):
                mult = 1

            val = 100 * mult

            # Limit checking, this will happen twice
            biome_type = region.biome.land_type
            if (biome_type == "Water"):
                # Checking upper/lower bounds
                if (val > water_height_limit):
                    val = water_height_limit
            if (biome_type == "Land"):
                if (val <= water_height_limit):
                    val = water_height_limit + 1

            # Applying our noise
            val = val + random.randrange(-height_noise, height_noise)

            if (val <= 0):
                val = 1

            # Applying the rock layer based height modification
            rock_value = region.rock_layer.rock_layer_list[0].rock_hardness
            rock_value = math.sqrt(rock_value)

            # Adding the minimum value to help increase variance
            rock_value = rock_value + 0.1

            val = rock_value * val
            val = round(val)

            # Making the adjustments a second time
            # Limit checking, this will happen twice
            biome_type = region.biome.land_type
            if (biome_type == "Water"):
                # Checking upper/lower bounds
                if (val > water_height_limit):
                    val = water_height_limit
            if (biome_type == "Land"):
                if (val <= water_height_limit):
                    val = water_height_limit + 1

            region.elevation = val

    def gen_experimental_weathering(self):
        print("Performing experimental weathering")

        adjustment_region_set = []

        for region in self.voronoi:

            # If we are already water, skipping
            if region.biome.land_type == "Water":
                continue

            # Iterating on all regions, first checking how many water tiles are adjacent
            water_count = 0
            water_list = []
            water_neighbor_index_list = []

            for neighbor in region.neighbors_index:
                neighbor_region = self.voronoi[neighbor]

                if neighbor_region.biome.land_type == "Water":
                    water_count = water_count + 1
                    water_list.append(neighbor_region)
                    water_neighbor_index_list.append(neighbor_region.index)

            if water_count < 2 or water_count > 4:
                continue

            # Checking neighbor adjacency
            neighbor_count = 0

            for neighbor_region in water_list:
                # Taking our neighbor regions, their neighbor lists and checking if their index matches anyone else

                neighbor_list = neighbor_region.neighbors_index
                for nl in neighbor_list:
                    for wnil in water_neighbor_index_list:
                        if nl == wnil:
                            neighbor_count = neighbor_count + 1

                            # Can comment out break for more relaxed neighbor levels
                            break

            if neighbor_count <= 0:
                # We have a weathered tile
                adjustment_region_set.append(region.index)


        # Finally doing the final adjustment. At the end so weathering doesnt affect other tiles as we go
        for index in adjustment_region_set:
            self.voronoi[index].biome.reload_index(1)

    # Function for 'building' our oceanic regions
    def build_ocean_regions(self, ocean_reduction_count):
        # This function is desgined to build the oceanic regions
        print("Building ocean regions")

        ocean_set = {}
        for region in self.voronoi:

            # Duplicating our voronoi regions for all water based regions
            if region.biome.land_type == "Water":

                # Checking if we are not an edge based water tile, because those suck
                if not region.edge:

                    # Finally, checking if we are not a water tile with a land neighbor
                    # Since those also suck

                    for neighbor_index in region.neighbors_index:

                        land_flag = 0
                        if self.voronoi[neighbor_index].biome.land_type == "Land":
                            # If our neighbor is a land tile, we flag it as land
                            # This is because we don't want to grow around tiny islands as it results in huge
                            # amounts of oceans taking up weird island chains in an awkward manner
                            land_flag = 1
                            break

                        else:
                            for secondary_neighbor_index in self.voronoi[neighbor_index].neighbors_index:
                                if self.voronoi[secondary_neighbor_index].biome.land_type == "Land":
                                    land_flag = 1
                                    break

                        # If we got a land flag...
                        if land_flag > 0:
                            break

                        else:
                            ocean_set[region.index] = region.__copy__()
                            ocean_set[region.index].biome = region.biome.__copy__()


        # Reducing
        # Keeping a copy of the ocean set for later, when we want to grow back
        growth_ocean_set = ocean_set.copy()
        for count in range(0,ocean_reduction_count):

            deletion_set = {}
            for key in ocean_set:
                region = ocean_set[key]

                existing_neighbor_flag = 0

                # If we are past the threshold then we are going to keep final dudes

                deletion_flag = 0
                for neighbor_index in region.neighbors_index:
                    if neighbor_index not in ocean_set:
                        deletion_flag = 1
                    else:
                        existing_neighbor_flag = 1

                if existing_neighbor_flag and deletion_flag:
                    deletion_set[region.index] = 1

                # Checking if we are deleting lonesome guys underneath the ocean threshold
                elif existing_neighbor_flag == 0 and count < ocean_size_threshold:
                    deletion_set[region.index] = 1

            for key in deletion_set:
                if (len(ocean_set) <= 1):
                    break

                self.voronoi[key].ocean_distance = count + 1
                ocean_set.pop(key)

        # Succesful reduction
        print("Successful oceanic reduction, expanding ocean set (with " + str(len(ocean_set)) + " oceans)")

        # Now to build the oceans by expanding outwards from the core positions
        ocean_obj = []

        # Assembling the new oceans from the old ones...
        ocean_count = 0
        for tile in ocean_set:

            # Getting the base tile
            region = ocean_set[tile]
            region.ocean_index = ocean_count

            new_ocean = Ocean(ocean_count)
            new_ocean.color = (random.randrange(0,255), random.randrange(0,255), random.randrange(0,255))

            # Setting the root tile
            new_ocean.root_tile = self.voronoi[tile]
            new_ocean.initialized = 1

            # Setting the base tile
            new_ocean.region_set.append(region)

            ocean_obj.append(new_ocean)
            ocean_count = ocean_count + 1

        # Now that we've assembled it, lets begin building it...
        # Continuous looping until all ocean sets have been expanded permanently

        while 1 == 1:
            # Taking each ocean
            visit_ocean = 0
            for ocean in ocean_obj:

                # print("Expanding ocean " + str(ocean.ocean_index))

                # Iterating on all of its tiles, and expanding it to all its neighbors that DO NOT belong to an ocean
                # Also don't expand if its a land tile of course

                # Checking if this ocean has been fully initialized...
                if ocean.initialized == 2:
                    continue

                if ocean.merged == 1:
                    continue

                did_expand_ocean = 0
                append_set = []

                # Keeping track of merge status
                merge_break = 0

                for tile in ocean.region_set:

                    # Iterating on each tile
                    neighbor_set = tile.neighbors_index

                    # Now iterating on each neighbor...
                    for neighbor_index in neighbor_set:

                        if neighbor_index not in growth_ocean_set:
                            continue

                        neighbor = growth_ocean_set[neighbor_index]

                        # Skipping edges
                        if neighbor.edge:
                            continue

                        if neighbor.biome.land_type == "Water" and neighbor.ocean_index == -1 and neighbor.ocean_index != ocean.ocean_index:

                            # We have an ocean tile that has not been assimilated
                            # Assimilating
                            neighbor.ocean_index = ocean.ocean_index

                            # Indicate that we did expand this ocean
                            did_expand_ocean = 1

                            append_set.append(neighbor)

                        # Allowing mergers if our oceans are small enough
                        # Basically will only happen in early stages
                        elif neighbor.ocean_index > 0 and len(ocean.region_set) < ocean_merge_threshold and neighbor.ocean_index != ocean.ocean_index:

                            print("2 Performing merger on ocean index " + str(neighbor.ocean_index) + " from " + str(ocean.ocean_index))

                            # Interesting, an ocean tile next to us at a very young age
                            # Lets merge them together
                            merge_ocean = ocean_obj[neighbor.ocean_index]

                            # Taking all of our tiles and putting them into the merge ocean
                            for tile in ocean.region_set:
                                # print("Appending oceanic tile")
                                tile.ocean_index = merge_ocean.ocean_index
                                merge_ocean.region_set.append(tile)

                            # Finally deleting this ocean
                            ocean.initialized = -2
                            ocean.region_set = []
                            ocean.merged = 1
                            merge_break = 1

                            break

                    if merge_break:
                        break

                if merge_break:
                    break


                for tile in append_set:
                    ocean.region_set.append(tile)


                # Checking if we did expand the ocean or not
                if did_expand_ocean:
                    visit_ocean = 1

                # If we did not expand our ocean, this ocean has been fully initialized to its base-state
                else:
                    ocean.initialized = 2


            # Checking if we have finished expanding
            if not visit_ocean:
                break

        self.ocean_set = ocean_obj
        print("Finished expanding base-state oceans. Beginning final stage ocean expansion")

        # Finally we want to expand to the final set of tiles that we have
        while 1 == 1:

            # Taking each ocean
            visit_ocean = 0
            for ocean in self.ocean_set:

                # print("Expanding ocean " + str(ocean.ocean_index))

                # Iterating on all of its tiles, and expanding it to all its neighbors that DO NOT belong to an ocean
                # Also don't expand if its a land tile of course

                # Checking if this ocean has been fully initialized...
                if ocean.initialized == 3:
                    continue

                did_expand_ocean = 0
                append_set = []
                for tile in ocean.region_set:

                    # Iterating on each tile
                    neighbor_set = tile.neighbors_index

                    # Now iterating on each neighbor...
                    for neighbor_index in neighbor_set:

                        neighbor = self.voronoi[neighbor_index]
                        if -1 in neighbor.neighbors_index:
                            continue

                        # In final state form, we do not want to grow to ocean tiles that are connected by edge tiles
                        if -1 in neighbor_set and -1 in neighbor.neighbors_index:
                            continue

                        if neighbor.biome.land_type == "Water" and neighbor.ocean_index == -1 and neighbor.ocean_index != ocean.ocean_index:

                            # We have an ocean tile that has not been assimilated
                            # Assimilating
                            neighbor.ocean_index = ocean.ocean_index

                            # Indicate that we did expand this ocean
                            did_expand_ocean = 1

                            append_set.append(neighbor)

                        # Allowing mergers if our oceans are small enough
                        # Basically will only happen in early stages
                        elif neighbor.ocean_index > 0 and len(ocean.region_set) < ocean_merge_threshold and neighbor.ocean_index != ocean.ocean_index:

                            print("1 Performing merger on ocean index " + str(neighbor.ocean_index) + " from " + str(ocean.ocean_index))

                            # Interesting, an ocean tile next to us at a very young age
                            # Lets merge them together
                            merge_ocean = ocean_obj[neighbor.ocean_index]

                            # Taking all of our tiles and putting them into the merge ocean
                            for tile in ocean.region_set:
                                # print("Appending oceanic tile")
                                tile.ocean_index = merge_ocean.ocean_index
                                merge_ocean.region_set.append(tile)

                            # Finally deleting this ocean
                            ocean.initialized = -2
                            ocean.region_set = []
                            neighbor_set = []

                for tile in append_set:
                    tile.ocean_index = ocean.ocean_index
                    ocean.region_set.append(tile)


                # Checking if we did expand the ocean or not
                if did_expand_ocean:
                    visit_ocean = 1

                # If we did not expand our ocean, this ocean has been fully initialized to its final form
                else:
                    ocean.initialized = 3


            # Checking if we have finished expanding
            if not visit_ocean:
                break

    def oceanic_land_analysis(self, percentage_threshold):
        print("Beginning land-based analysis")
        # Checking how many land neighbors each ocean has
        for ocean_index in self.ocean_set:

            ocean = self.ocean_set[ocean_index]
            for region in ocean.region_set:

                for neighbor_index in region.neighbors_index:
                    if self.voronoi[neighbor_index].biome.land_type == "Land":
                        ocean.land_neighbor_count = ocean.land_neighbor_count + 1

                        # You neighbor land, no need to continue
                        break

        # Setting oceans to 'inland' oceans based on the number of land neighbors to oceanic neighbors
        for ocean_index in self.ocean_set:

            ocean = self.ocean_set[ocean_index]
            if ocean.land_neighbor_count > (percentage_threshold * len(ocean.region_set)):
                ocean.inland_sea = 1

    # Function that is going to build the rest of the oceans, since some didn't make it
    def gen_freshwater(self):
        # First we are going to build a set of all water tiles that do NOT belong to the ocean
        unvisited_water = {}
        for region in self.voronoi:

            if region.ocean_index < 0 and region.biome.land_type != "Land":
                unvisited_water[region.index] = region

        # Okay our structure that contains all of the unvisited water tiles is complete
        # We will continually build fresh water from whats left...
        while len(unvisited_water) > 0:

            # Taking a region
            key_index = 0
            for key in unvisited_water:
                key_index = key
                break

            region = unvisited_water[key_index]

            visited_set = {}
            to_visit_set = {}

            # Freshwater tag, in case we run into a non-freshwater tile through a neighbor node
            freshwater_tag = 1

            # Initial adjustment, getting all the neighbors into the to_visit_set
            for neighbor_index in region.neighbors_index:

                if self.voronoi[neighbor_index].biome.land_type == "Land":
                    continue

                to_visit_set[neighbor_index] = self.voronoi[neighbor_index]

            # Adding ourself to the visited set
            visited_set[region.index] = region

            # Continually visiting everything...
            while len(to_visit_set) > 0:

                to_add_to_visited = {}
                to_add_to_visit = {}

                # Iterating on everything currently in the to_visit_set
                for key in to_visit_set:

                    visited_region = self.voronoi[key]
                    to_add_to_visited[key] = to_visit_set[key]

                    for neighbor_index in visited_region.neighbors_index:

                        # Make sure we are water first...
                        if self.voronoi[neighbor_index].biome.land_type == "Land":
                            continue

                        if neighbor_index not in unvisited_water:
                            # Oh no, we found a water tile thats a neighbor but NOT in the unvisited water set
                            # That is not good
                            # Luckily we can just continue
                            # But we are probably not freshwater anymore
                            freshwater_tag = self.ocean_set[self.voronoi[neighbor_index].ocean_index].fresh_water
                            continue

                        if neighbor_index not in visited_set and neighbor_index not in to_add_to_visited:
                            # Adding us into the to_add_to_visit
                            to_add_to_visit[neighbor_index] = self.voronoi[neighbor_index]

                # Okay we have a set of guys that have been visisted, lets remove them from the to visit set
                for key in to_add_to_visited:
                    to_visit_set.pop(key)
                    visited_set[key] = to_add_to_visited[key]

                for key in to_add_to_visit:
                    to_visit_set[key] = to_add_to_visit[key]

            # Okay we now have an EMPTY to_visit set
            # This should be because we visisted all the possible options
            # Lets turn this into a fresh water ocean tile
            fresh_ocean = Ocean(len(self.ocean_set))
            fresh_ocean.initialized = 2
            fresh_ocean.inland_sea = 1
            fresh_ocean.fresh_water = freshwater_tag
            fresh_ocean.root_tile = region

            # Building the region set
            for region_index in visited_set:

                region = visited_set[region_index]
                region.ocean_index = fresh_ocean.ocean_index
                fresh_ocean.region_set.append(region)

                if region_index in unvisited_water:
                    unvisited_water.pop(region.index)

            print("Built freshwater ocean")
            self.ocean_set.append(fresh_ocean)

    # Function that will fix oceanic generation
    # Accomplishes this by deleting all the 'empty' oceans
    def fix_ocean_gen(self):

        print("Fixing ocean set...")

        new_ocean_set = {}
        for ocean in self.ocean_set:

            if len(ocean.region_set) <= 0:

                # Double checking before continuing
                continue_flag = 1
                for region in self.voronoi:
                    if region.ocean_index == ocean.ocean_index:
                        print("Fixed oceanic region with messed up tracking...")
                        ocean.region_set.append(region)
                        continue_flag = 0

                if continue_flag:
                    continue

            new_ocean_set[ocean.ocean_index] = ocean

        self.ocean_set = new_ocean_set



    # Function for generating base temperature information
    # Does this by first generating an planetary tilt and amplitude to make things a little more interesting
    # Also uses a final noise value
    def gen_base_temperature(self, noise, start_noise, oceanic_averaging_count):
        print("Generating base temperature value set")

        # Getting start value information to build the temperature gradiant equation
        cycle_middle = self.height / 2

        # Adjusting with start_noise
        if (start_noise != 0):

            lower_limit = cycle_middle - (cycle_middle * start_noise)
            upper_limit = cycle_middle + (cycle_middle * start_noise)
            cycle_middle = random.randrange(lower_limit, upper_limit)

        # Okay we have our middle
        # Now we need to generate the cycle period and the cycle strength
        # Think of it as a sin wave
        cycle_count = random.randrange( int(100 * temp_lower_cycle_limit), int( 100 * temp_upper_cycle_limit)) / 100
        cycle_width = self.width / cycle_count * 0.2

        # Using a cycle height modifier, which is basically half the height of our map
        cycle_height_modifier = self.height / temp_height_division_factor
        cycle_amplitude = random.randrange( int(round(temp_lower_amplitude * cycle_height_modifier)), int(round(temp_upper_amplitude * cycle_height_modifier)))

        cycle_shift = random.randrange(-self.width, self.width)

        # Calculating our maximum and minimum ranges
        # These ranges should really just be the amplitudes
        top_point = (PI / 2, self.height)
        bottom_point = (-PI / 2, 0)
        max_upper_distance = self.temp_equ_distance(1, cycle_amplitude, cycle_middle, 0, top_point)
        max_lower_distance = self.temp_equ_distance(1, cycle_amplitude, cycle_middle, 0, bottom_point)

        max_range = max_upper_distance
        if max_lower_distance > max_upper_distance:
            max_range = max_lower_distance

        # We have our cycle width and our cycle amplitude
        # Now we will begin our cyclic temperature process
        print("Beginning cyclic temperature evaluation with following values: " + str(cycle_count) + ", " + str(cycle_width) + ", " + str(cycle_amplitude) + ", " + str(cycle_middle))
        print("Boundary: " + str(max_lower_distance) + ", " + str(max_upper_distance) + ", max of " + str(max_range))

        for region in self.voronoi:

            # Grabbing the Y value
            height = region.center[1]

            # Calculating its X temperature equatorial position
            temp_equator = self.temp_equ_distance(cycle_width, cycle_amplitude, cycle_middle, cycle_shift, region.center)

            # Calculating the Y distance
            distance = abs(temp_equator - height)

            # This is our absolute distance
            # We will now build the relative distance
            random_temp_adjustment = random.randrange(-noise, +noise)

            relative_distance = (distance / max_range) * temp_base_level
            relative_distance = relative_distance + random_temp_adjustment

            # Checking limits
            if relative_distance < 0:
                relative_distance = 0
            elif relative_distance > temp_base_level:
                relative_distance = temp_base_level

            relative_distance = temp_base_level - round(relative_distance)
            region.relative_normalized_temperature = relative_distance

        # Oceans have fairly averaged temperatures, going to do that
        print("Averaging oceanic temperatures")
        for count in range(0, oceanic_averaging_count):

            adjustment_set = {}
            for region in self.voronoi:

                if region.biome.land_type == "Land":
                    continue

                temperature_count = region.relative_normalized_temperature
                neighbor_count = len(region.neighbors_index)

                for neighbor_index in region.neighbors_index:
                    temperature_count = temperature_count + self.voronoi[neighbor_index].relative_normalized_temperature

                adjustment_temp = temperature_count / (neighbor_count + ocean_temp_downward_trend)

                # Still keeping some noise
                adjustment_set[region.index] = adjustment_temp

            for key in adjustment_set:
                self.voronoi[key].relative_normalized_temperature = adjustment_set[key]

    # Function that provides the distance from a point to the temperature equator
    def temp_equ_distance(self, cyle_width, cycle_amplitude, cycle_middle, cycle_shift, point):

        # Calculating the cyclic position first
        cycle_position = math.sin( ( cycle_shift + point[0]) / cyle_width) * cycle_amplitude + cycle_middle
        cycle_position = round(cycle_position)

        return cycle_position

    # Function that begins building the base for humidity, humidity source
    # This is done by finding all water tiles, and computing their temperature
    # Higher temp = higher humidity
    def gen_humidity_source(self):

        print("Generating humidity source tiles")
        for region in self.voronoi:

            if region.biome.land_type == "Land":
                continue

            # Okay we have a water tile
            # Getting the temperature
            temp = region.relative_normalized_temperature

            # Okay we have a water tile, and we have a temperature
            # The humidity should be equal to the water tile as well as the temperature
            region.base_humidity = temp / 4

            # If we are an inland sea, our humidity value is actually a little lower
            if self.ocean_set[region.ocean_index].inland_sea or self.ocean_set[region.ocean_index].fresh_water:
                region.base_humidity = temp / 10

            # Below a certain value we ignore humidity
            if region.base_humidity < humidity_threshold:
                region.base_humidity = 0
                continue

            # Deciding if this is going to be a humidity source tile
            humid_chance = temp * temp * temp
            random_chance = random.randrange(0, 100000) + humidity_source_threshold

            if humid_chance > random_chance:

                # Lets check its final randomizer
                random_result = random.randrange(0, humidity_source_chance[1])
                if random_result <= humidity_source_chance[0]:

                    # We have a humidity source tile!
                    # Upping the humidity of course, and indicating its humidity level
                    region.humid_source = 1
                    region.base_humidity = temp * 5 / 4
                    region.humid_out = 0
                    region.humid_in = 0

                    # Giving our neighbors some humidity as well
                    for neighbor_index in region.neighbors_index:
                        neighbor = self.voronoi[neighbor_index]

                        # Giving our neighbors some humidity
                        if not neighbor.humid_source:
                            neighbor.base_humidity = neighbor.base_humidity + (region.base_humidity / 2)

    # Function for generating oceanic wind sources
    def gen_oceanic_wind_sources(self):
        print("Generating oceanic wind source tiles")

        ocean_base_wind_set = {}
        ocean_wind_set = {}

        # This set lets us index doubly without keeping the results
        # Lets us deal with duplicate occurances without ending up with duplicate guys
        ocean_wind_double_check_set = {}

        for ocean_index in self.ocean_set:
            ocean = self.ocean_set[ocean_index]

            for region in ocean.region_set:

                # If our region has a neighbor from a DIFFERENT ocean, then its time to make an oceanic wind source...
                for neighbor_index in region.neighbors_index:
                    neighbor = self.voronoi[neighbor_index]

                    if neighbor.biome.land_type == "Land":
                        continue

                    if not neighbor.ocean_index == region.ocean_index:

                        # Should be an ocean tile
                        # Lets randomly select if its not
                        random_select_wind = random.randrange(0,ocean_wind_chance[1])
                        if random_select_wind > ocean_wind_chance[0]:
                            continue

                        # Mismatching oceanic indexes, must be a wind source here
                        # Compare value basically lets us index with two values, kinda weird but should work...
                        compare = str(neighbor.ocean_index) + "," + str(region.ocean_index)
                        inverse_compare = str(region.ocean_index) + "," + str(neighbor.ocean_index)
                        if compare not in ocean_base_wind_set:

                            # Adding both of these guys into the ocean base wind set
                            # First determining the angle that we will use...
                            ocean_root_alpha = ocean.root_tile.center
                            ocean_root_beta = self.ocean_set[neighbor.ocean_index].root_tile.center

                            # Comparing centers
                            degree = self.get_angle_between_points(ocean_root_alpha, ocean_root_beta)

                            # Determine if we are going to use the inverse or normal
                            random_select = random.randrange(0, 100)
                            if random_select <= 50:
                                # Using the inverse
                                degree = degree - 180
                                if degree < 0:
                                    degree = degree + 360

                            # Alright we have our degree, putting it within our set
                            # Using some variance here
                            variance = random.randrange(-ocean_wind_variance, ocean_wind_variance)
                            degree = degree + variance

                            if degree < 0:
                                degree = degree + 360

                            if degree > 360:
                                degree = degree - 360

                            degree = int(round(degree))

                            ocean_base_wind_set[inverse_compare] = degree
                            ocean_base_wind_set[compare] = degree

                        # Checking if we do not already exist
                        if region.index not in ocean_wind_double_check_set and region.index not in ocean_wind_set:
                            ocean_wind_set[region.index] = Wind(region.index, region, ocean_base_wind_set[compare], 70)
                            ocean_wind_double_check_set[neighbor_index] = 0

        self.ocean_wind_set = ocean_wind_set
        print(ocean_base_wind_set)

    # Experimental function for generating oceanic winds...
    # This could get tricky
    def gen_winds(self):
        print("Generating winds...")

        # Continuously grow each wind source
        wind_set = {}

        # Copying the oceanic wind set
        for wind_index in self.ocean_wind_set:
            wind_set[wind_index] = self.ocean_wind_set[wind_index]

        # Growing
        val = 0
        while val < wind_gen_count:

            growth_set = {}
            for wind_index in wind_set:
                wind = wind_set[wind_index]

                if wind.grown:
                    continue

                if wind.strength < wind_strength_limit:
                    continue

                # Getting a possible neighbor to select for growth
                neighbor_index_set = wind.region.neighbors_index
                for neighbor_index in neighbor_index_set:

                    # Checking if we can grow to any of these
                    neighbor = self.voronoi[neighbor_index]

                    # Getting the angle between the two points, checking if it matches the wind degrees
                    angle = self.get_angle_between_points(neighbor.center, wind.region.center)
                    range_min = wind.direction - wind_range
                    range_max = wind.direction + wind_range

                    grow_flag = 0

                    if range_min > 0:
                        if angle > range_min and angle <= wind.direction:
                            grow_flag = 1
                    else:
                        range_min = range_min + 360
                        if angle < range_min and angle >= wind.direction:
                            grow_flat = 1

                    if range_max < 360:
                        if angle < range_max and angle >= wind.direction:
                            grow_flag = 1
                    else:
                        range_max = range_max - 360
                        if angle > range_max and angle <= wind.direction:
                            grow_flag = 1

                    if grow_flag:
                        wind.grown = 1

                        # Determining new wind strength
                        # print("Growing winds...")

                        # Wind strength decreases with elevation loss
                        elevation = ( neighbor.elevation / 100)

                        elevation_loss = 0
                        if elevation < 0.2 and wind.strength < 70:
                            elevation_loss = -10

                        else:
                            elevation_loss = elevation * wind_loss_strength

                        # Calculating angle difference...
                        wind_difference = abs(int(round(self.get_angular_difference(wind.direction, angle)))) + 2
                        adjustment = random.randrange(int(round(wind.direction - (wind_difference_factor * wind_difference))),
                                                      int(round(wind.direction + (wind_difference_factor * wind_difference))))

                        if adjustment > 360:
                            adjustment = adjustment - 360
                        if adjustment < 0:
                            adjustment = adjustment + 360

                        new_wind_direction = adjustment

                        new_wind_strength = wind.strength - elevation_loss
                        if new_wind_strength < wind_strength_limit:
                            new_wind_strength = wind_strength_limit - random.randrange(-wind_strength_limit/2, wind_strength_limit/2)

                        neighbor.is_wind = 1
                        new_wind = Wind(neighbor.index, neighbor, int(round(new_wind_direction)), new_wind_strength)
                        wind.wind_neighbor = new_wind
                        growth_set[neighbor.index] = new_wind

                        break

            for wind_growth_index in growth_set:
                wind_set[growth_set[wind_growth_index]] = growth_set[wind_growth_index]

            val = val + 1

        self.winds = wind_set

    # Function for fixing regions with duplicate wind values
    def average_remove_wind(self):
        print("Averaging winds and removing duplicates")

        #TODO: Determine if we should do this

    # Function for widening the winds
    # Fills out the rest of the map with wind, basically
    def grow_wind_width(self):
        print("Growing wind width, filling rest of map with wind basically")

        growth = 1
        while growth:

            did_grow = 0
            growth_set = {}

            for wind_index in self.winds:
                wind = self.winds[wind_index]

                # Indicating we have already widened this wind
                if wind.grown == 2:
                    continue

                wind.grown = 2

                # Growing to all neighbors
                # Dramatically reducing strength of course
                for neighbor_index in wind.region.neighbors_index:
                    neighbor = self.voronoi[neighbor_index]

                    if neighbor.is_wind:
                        continue

                    elevation = (neighbor.elevation / 100)
                    elevation_loss = elevation * wind_loss_strength

                    new_wind_strength = wind.strength - elevation_loss
                    if new_wind_strength < wind_strength_limit:
                        new_wind_strength = wind_strength_limit - random.randrange(-wind_strength_limit / 2,
                                                                                   wind_strength_limit / 2)

                    # Making this a new windy dude
                    neighbor.is_wind = 1

                    # Decays slightly faster
                    new_wind = Wind(neighbor.index, neighbor, wind.direction, int(round(new_wind_strength / 1.2)))
                    wind.wind_neighbor = new_wind
                    growth_set[neighbor.index] = new_wind

            for growth_index in growth_set:
                did_grow = 1
                self.winds[growth_index] = growth_set[growth_index]

            if not did_grow:
                growth = 0



    ################
    ## Debug Help ##
    ################

    def get_angle_between_points(self, point_1, point_2):

        # We negate the Ys because in our graph Y is an inverted position
        # Very strange I know...

        # Comparing centers
        alpha_x = point_2[0]
        alpha_y = -point_2[1]

        beta_x = point_1[0]
        beta_y = -point_1[1]

        # Calculating angle
        delta_x = alpha_x - beta_x
        delta_y = alpha_y - beta_y
        theta_radians = math.atan2(delta_y, delta_x)

        degree = theta_radians * 180 / 3.14159

        # Fixing angles less than 0, since we are scrubs
        if degree < 0:
            degree = degree + 360

        # We also care more about reacing 180 degrees as well, so lets subtract 180 for values > 180
        if degree > 360:
            degree = degree - 360

        return degree

    def get_angular_difference(self, angle_1, angle_2):

        math_diff = angle_2 - angle_1

        if math_diff > 180:
            math_diff = 360 - math_diff

        return math_diff

    def debug_region(self):

        index = 1

        print("SETTING NEIGHBORS WITH INDEX OF " + str(index) + " TO " + str(self.voronoi[index].neighbors_index))
        print("MY CENTER IS: " + str(self.voronoi[index].center))
        print("MY VERTEX LIST IS : " + str(self.voronoi[index].vertex_list_value))
        print("MY VERTEX INDEX LIST IS : " + str(self.voronoi[index].vertex_list_index))
        for neighbor in self.voronoi[index].neighbors_index:
            print("NEIGHBOR CENTER IS " + str(self.voronoi[neighbor].center))


class VoronoiRegion:

    # This voronoi region object represents a region
    # note, it SHOULD probably be used within a list to leverage the index, neighbor_list data

    def __copy__(self):
        copy_region = VoronoiRegion(self.center, self.index)

        # Time to init
        copy_region.initialized = self.initialized

        # Index simply for tracking
        copy_region.index = self.index

        # Assigning center, having to regenerate it because its bad
        copy_region.center = self.center
        copy_region.edge = self.edge

        # Assigning empty values to the lists
        copy_region.vertex_list_value = self.vertex_list_value
        copy_region.vertex_list_index = self.vertex_list_index

        # Assigning empty values to the neighbors
        copy_region.neighbors_index = self.neighbors_index

        # Constructing a shape list
        copy_region.shape_list = self.shape_list

        # Assigning a deep water biome as default, will be set later hopefully...
        copy_region.biome = self.biome
        copy_region.rock_layer = self.rock_layer
        copy_region.elevation = self.elevation
        copy_region.ocean_distance = self.ocean_distance
        copy_region.ocean_index = self.ocean_index
        copy_region.relative_normalized_temperature = self.relative_normalized_temperature
        copy_region.is_mountain = self.is_mountain
        copy_region.humid_source = self.humid_source
        copy_region.base_humidity = self.base_humidity
        copy_region.humid_out = self.humid_out
        copy_region.humid_in = self.humid_in

        return copy_region

    def __init__(self, center, index):
        # Time to init
        self.initialized = 1

        # Index simply for tracking
        self.index = index

        # Assigning center, having to regenerate it because its bad
        self.center = center

        # Tracking edge tiles
        self.edge = 0

        # Assigning empty values to the lists
        self.vertex_list_value = []
        self.vertex_list_index = []

        # Assigning empty values to the neighbors
        self.neighbors_index = []

        # Constructing a shape list
        self.shape_list = []

        # Assigning a deep water biome as default, will be set later hopefully...
        self.biome = Biome(1)
        self.rock_layer = RockLayer(defaultRock)
        self.elevation = 0

        # Ocean distance
        self.ocean_distance = -1
        self.ocean_index = -1

        # Some temperature based information
        self.relative_normalized_temperature = -1

        # Tracking mountain status
        self.is_mountain = 0

        # Tracking humidity information
        # Base stored tile humidity
        self.base_humidity = 0

        # How much humidity this tile is GAININIG from winds
        self.humid_out = 0

        # How much humidity this tile is LOSING to winds
        self.humid_in = 0

        # Humid source represents whether or not this is a humidity source
        # This means we will NEVER lower its value during an averaging
        self.humid_source = 0

        self.is_wind = 0

# Helper function for checking if a point is within a polygon
# Ray tracing
def check_point_within_polygon(x,y,poly):

    n = len(poly)
    inside = False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xints = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xints:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside