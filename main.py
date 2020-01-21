# Base imports
from PIL import Image, ImageDraw, ImageFont

# Importing voronoi
from voronoi import VoronoiWrapper
import random
import string
from shapegen import Shape
from rock import RockDatabase
import noise
import math
import voronoi

debug = 3

erosion_count = 2
height_noise = 5
weathering_count = 3
erode_noise = 5
erode_strength = 0.5

# Temperature noise, higher number = higher variance on temperature
temp_noise = 1

# Percentage based value
temp_start_noise = 0.05

# Number of times to iteratively average out the oceanic temperatures
oceanic_average_count = 10

# Percent value threshold of land neighbors to water tiles to be considered inland sea
ocean_percentage_threshold = 0.35

# Variables controlling mountain ranges
mountain_range_count_min = 2
mountain_range_count_max = 6
mountain_height_noise = 5
mountain_range_length_dimension = (3, 17)

font_08 = ImageFont.truetype("arial.ttf", 8)
font_18 = ImageFont.truetype("arial.ttf", 18)
font_40 = ImageFont.truetype("arial.ttf", 40)
font_70 = ImageFont.truetype("arial.ttf", 70)
font_120 = ImageFont.truetype("arial.ttf", 120)

# Class that does all of the processing
class Main:

    def __init__(self, width, height, polycount, relaxation_count, SEED):
        # Setting up local sizes

        self.width = width
        self.height = height
        self.polycount = polycount
        self.relaxation_count = relaxation_count

        # Shape list
        self.landShapeList = []
        self.waterShapeList = []
        self.fullShapeList = []

    def gen_shapes_land(self, numShapes, scale, volatility, eschew, numberSubdivision, finalScaleRange, tectonic, SEED):
        print("Generating land tectonics")

        # Generating shapes
        for x in range(0,numShapes):
            # Generating shapes
            newShape = Shape(volatility, scale, eschew, numberSubdivision, finalScaleRange, (self.width, self.height), tectonic, SEED)

            # Setting the shapes index
            print(len(self.landShapeList) + len(self.waterShapeList))
            newShape.shape_index = len(self.landShapeList) + len(self.waterShapeList)

            self.landShapeList.append(newShape)
            # Incrementing seed
            SEED += 1

        for shape in self.landShapeList:
            if (debug == 1):
                shape.draw()

    def gen_shape_water(self, numShapes, scale, volatility, eschew, numberSubdivision, finalScaleRange, tectonic, SEED):
        # Generating shapes
        print("Generating water tectonics")

        for x in range(0,numShapes):
            # Generating shapes
            newShape = Shape(volatility, scale, eschew, numberSubdivision, finalScaleRange, (self.width, self.height), tectonic, SEED)

            # Setting the shapes index
            print(len(self.landShapeList) + len(self.waterShapeList))
            newShape.shape_index = len(self.landShapeList) + len(self.waterShapeList)

            self.waterShapeList.append(newShape)
            # Incrementing seed
            SEED += 1

        for shape in self.waterShapeList:
            if (debug == 1):
                shape.draw()

    def gen_tectonic_geology(self):
        # Generating the tectonic geology
        rockDatabase = RockDatabase()

        for shape in self.landShapeList:
            # Determining what type to make this, first checking if its a tectonic or not...
            if (shape.tectonic):
                # Okay its tectonic, lets set the geologic information here...
                print("Assigning tectonic geologic information for shape with index " + str(shape.shape_index))
                shape.base_rock = rockDatabase.getDefaultLandRock()


        # Same thing but for oceanic tectonic plates
        for shape in self.waterShapeList:
            # Determining what type to make this, first checking if its a tectonic or not...
            if (shape.tectonic):
                # Okay its tectonic, lets set the geologic information here...
                print("Assigning tectonic geologic information for shape with index " + str(shape.shape_index))
                shape.base_rock = rockDatabase.getDefaultOceanRock()

    # Function for defining biome parameters
    # This gives us advanced capabilities for determining how the biomes are generated
    def run(self):

        # Making the Voronoi Wrapper
        self.v = VoronoiWrapper(self.width, self.height, self.polycount, self.relaxation_count, SEED)

        # If debug, drawing the voronoi
        if (debug == 1):
            self.v.display()

        # Building final shape list because we are good
        self.fullShapeList = self.landShapeList.copy()

        # Moving over the other shapes
        for shape in self.waterShapeList:
            self.fullShapeList.append(shape)

        # Now that we've built our Voronoi Wrapper, lets construct the world from the shapes
        # This will require us to iterate on every vornoi point, calculate if its within any of the shapes. If it is
        # then we set the land type to "land"
        self.v.gen_shape_land(self.landShapeList)
        self.v.gen_shape_water(self.waterShapeList)

        # Experimental landscape weathering, reduces a lot of strange land bridges into water tiles
        for x in range(0, weathering_count):
            self.v.gen_experimental_weathering()

        # Generating all of the tectonic plates geologic information
        # Lets begin building all of the other information that we need to build our world
        # First and foremost we are going to do calculations of rock type
        # This is a very defining characteristic of our world and must be used appropriately

        # The generation rules can be seen in the options
        self.gen_tectonic_geology()

        # Some error handling
        if (debug == 3):
            self.print_shape_info()

        self.v.genRegionRock(self.fullShapeList)

        # Next lets assign base-level heightmap data from tectonic interactions
        self.v.gen_voronoi_base_height(height_noise, len(self.fullShapeList))

        # Building some cool mountain ranges
        mountain_range_count = random.randrange(mountain_range_count_min, mountain_range_count_max)
        self.v.gen_mountain_ranges(mountain_range_count, mountain_height_noise, mountain_range_length_dimension)

        # Doing erosion
        for x in range(0, erosion_count):
            self.v.gen_voronoi_heightmap_average(erode_noise, erode_strength)

        # Building the oceanic regions
        self.v.build_ocean_regions(50)

        # Building the freshwater oceans
        self.v.gen_freshwater()

        # Fixing some of the bugs caused by oceanic generation
        self.v.fix_ocean_gen()

        # Generating oceanic info
        self.v.oceanic_land_analysis(ocean_percentage_threshold)

        # Building the temperature differential
        self.v.gen_base_temperature(temp_noise, temp_start_noise, oceanic_average_count)

        # Okay...
        # We now have OCEANS and we also have BASE TEMPERATURE
        # We can now build the worlds 'base' humidity zones
        self.v.gen_humidity_source()

        # We can also build the worlds 'base' wind zones
        self.v.gen_oceanic_wind_sources()
        self.v.gen_winds()
        self.v.grow_wind_width()

        # Now that we've built the Voronoi Wrapper, time to begin building the biomes

    ###########
    ## Debug ##
    ###########

    def print_shape_info(self):

        for region in self.landShapeList:
            if (region.tectonic):
                print(
                    "Land Tectonic: " + str(region.tectonic) + ", Rock: " + str(region.base_rock) + ", Geology: " + str(
                        region.base_rock.rock_name) + " Index: " + str(region.shape_index))
            else:
                print("Land Tectonic: " + str(region.tectonic) + ", Rock: " + str(region.base_rock) + " Index: " + str(region.shape_index))

        for region in self.waterShapeList:
            if (region.tectonic):
                print(
                    "Water Tectonic: " + str(region.tectonic) + ", Rock: " + str(region.base_rock) + ", Geology: " + str(
                        region.base_rock.rock_name) + " Index: " + str(region.shape_index))
            else:
                print("Water Tectonic: " + str(region.tectonic) + ", Rock: " + str(region.base_rock) + " Index: " + str(region.shape_index))


    ####################
    ## Draw Functions ##
    ####################

    def draw(self):
        # Generating a new picture
        im = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="white")


        # Drawing every region
        #print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw.polygon(draw_vert_list, fill=region.biome.biome_color)

        im.save("output/output.png")

    def draw_index(self):
        # Generating a new picture
        im = Image.new("RGB", (self.width, self.height), "#91BFFF")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#91BFFF")


        # Drawing every region
        #print("Centers")

        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw.polygon(draw_vert_list, fill=region.biome.biome_color)
            draw.text(region.center, str(region.index), font=font_70)
            draw.line(draw_vert_list, fill="red", width=9)

        im.save("output/indexed_output.png")

    def border_draw(self):
        # Generating a new picture
        im = Image.new("RGB", (self.width, self.height), "#91BFFF")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#91BFFF")


        # Drawing every region
        #print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw.polygon(draw_vert_list, fill=region.biome.biome_color)
            draw.line(draw_vert_list, fill="red", width=9)

        im.save("output/border_output.png")

    def draw_region_overlap(self):
        # Generating a new picture and filling it with the overlap data we have
        im = Image.new("RGB", (self.width, self.height), "#91BFFF")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#6A6A6B")

        # Drawing every region
        # print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            # Grabbing our number of shapes
            shape_count = len(region.shape_list)
            color_base = 200 * (shape_count / len(self.fullShapeList)) + 55
            color_base = round(color_base)

            draw.polygon(draw_vert_list, fill=(color_base,color_base,color_base))

        im.save("output/overlap_output.png")

    def draw_tectonic(self):

        # Determining the number of tectonic plates to draw
        num_tectonic = len(self.fullShapeList)
        for x in range(0,num_tectonic):

            # Generating a new picture and filling it with the geological data that we have
            im = Image.new("RGB", (self.width, self.height), "#91BFFF")
            draw = ImageDraw.Draw(im)

            draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#6A6A6B")

            # Drawing every region
            # print("Centers")
            for region in self.v.voronoi:
                if not region.shape_list.__contains__(x):
                    continue

                vert_list = region.vertex_list_value

                draw_vert_list = []
                for vertex in vert_list:
                    new_vertex = (vertex[0], vertex[1])
                    draw_vert_list.append(new_vertex)

                draw.polygon(draw_vert_list, fill="red")
                draw.line(draw_vert_list, fill="red", width=9)

            im.save("output/tectonic/tectonic_"+str(x)+"_output.png")

    def draw_geology(self):
        # Generating a new picture and filling it with the geological data that we have
        im = Image.new("RGB", (self.width, self.height), "#91BFFF")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#6A6A6B")

        # Drawing every region
        # print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)


            # Grabbing our rock layer object
            rock = region.rock_layer.rock_layer_list[0]
            rock_color = rock.rock_color

            draw.polygon(draw_vert_list, fill=rock_color)

        im.save("output/geology_output.png")

    def draw_elevation(self, draw_only_land):
        # Generating a new picture and filling it with the geological data that we have
        im = Image.new("RGB", (self.width, self.height), "#91BFFF")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#6A6A6B")

        # Drawing every region
        # print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)


            # Grabbing our rock layer object
            if (draw_only_land):
                if region.biome.land_type == "Water":
                    color = 0
                else:
                    color = region.elevation / 100 * 255
                    color = round(color)
            else:
                color = region.elevation / 100 * 255
                color = round(color)

            draw.polygon(draw_vert_list, fill=(color,color,color))
            draw.text(region.center, str(int(round(region.elevation))), font=font_08, fill="red")

        im.save("output/heightmap_output.png")

    def draw_temperature_set(self):
        # Drawing temperature information
        im = Image.new("RGB", (self.width, self.height), "black")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="black")

        # Drawing every region
        # print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            # Grabbing our rock layer object
            temperature = region.relative_normalized_temperature

            # Normalizing it against 255
            temperature = int(round(temperature / 100 * 255))

            temp_color = (temperature, temperature, temperature)

            draw.polygon(draw_vert_list, fill=temp_color)

        im.save("output/temperature_output.png")

    def draw_edge_set(self):
        # Drawing temperature information
        im = Image.new("RGB", (self.width, self.height), "black")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="black")

        # Drawing every region
        # print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            # Grabbing our rock layer object
            temp_color = "black"

            if region.edge:
                temp_color = "blue"

            draw.polygon(draw_vert_list, fill=temp_color)

        im.save("output/edge_output.png")

    def draw_ocean_set(self):
        # Generating a new picture and filling it with the oceanic data that we have
        im = Image.new("RGB", (self.width, self.height), "#91BFFF")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="#6A6A6B")

        # Drawing every region
        # print("Centers")
        for ocean_index in self.v.ocean_set:

            ocean = self.v.ocean_set[ocean_index]

            for region in ocean.region_set:
                vert_list = region.vertex_list_value

                draw_vert_list = []
                for vertex in vert_list:
                    new_vertex = (vertex[0], vertex[1])
                    draw_vert_list.append(new_vertex)

                draw.polygon(draw_vert_list, fill=ocean.color)

        # Drawing ocean centers
        for ocean_index in self.v.ocean_set:
            ocean = self.v.ocean_set[ocean_index]

            region = ocean.root_tile

            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw.polygon(draw_vert_list, fill="black")
            draw.text(region.center, str(ocean.ocean_index) + "|" + str(ocean.land_neighbor_count) + "/" + str(len(ocean.region_set)), font=font_70)

            fill = "red"
            if ocean.inland_sea:
                fill = "blue"

            if ocean.fresh_water:
                fill = "green"

            draw.line(draw_vert_list, fill=fill, width=9)


        im.save("output/ocean_output.png")

    def draw_mountains_set(self):
        # Drawing temperature information
        im = Image.new("RGB", (self.width, self.height), "black")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="white")

        # Drawing base level
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw.polygon(draw_vert_list, fill=region.biome.biome_color)

        # Drawing mountains
        for mountain_range_index in self.v.mountain_set:

            mountain_range = self.v.mountain_set[mountain_range_index]
            for mountain_tile_index in mountain_range.mountains:

                mountain_tile = mountain_range.mountains[mountain_tile_index]
                region = mountain_tile.region

                vert_list = region.vertex_list_value

                draw_vert_list = []
                for vertex in vert_list:
                    new_vertex = (vertex[0], vertex[1])
                    draw_vert_list.append(new_vertex)

                draw.polygon(draw_vert_list, fill=mountain_range.color)
                display_strength = int(round(mountain_tile.mountain_strength * 100))
                draw.text(region.center, str(display_strength) + ", " + str(mountain_tile.growth_angle),
                          font=font_08)

            # Drawing root tiles
            region = mountain_range.root_tile.region

            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw.text(region.center, str(mountain_range.range_index) + ", " + str(mountain_range.base_growth_angle), font=font_08, fill="red")


        im.save("output/mountain_output.png")

    def draw_humidity(self):
        # Generating a new picture
        im = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="white")


        # Drawing every region
        #print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            # Getting humidity values
            fill = region.biome.biome_color

            if region.humid_source:
                fill = "blue"

            draw.polygon(draw_vert_list, fill=fill)
            draw.text(region.center, str(int(round(region.base_humidity))), font=font_08, fill="red")

        im.save("output/humidity_advanced_output.png")

    def draw_oceanic_wind(self):
        # Generating a new picture
        im = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="white")


        # Drawing every region
        #print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            # Getting humidity values
            fill = region.biome.biome_color
            draw.polygon(draw_vert_list, fill=fill)

        for wind_index in self.v.ocean_wind_set:
            wind = self.v.ocean_wind_set[wind_index]

            degree = wind.direction
            rad_degree = degree / 180 * 3.14159

            # Drawing a line
            center = wind.region.center
            center_x = center[0]
            center_y = center[1]

            left_x = center_x - (20 * math.cos(rad_degree))
            left_y = center_y + (20 * math.sin(rad_degree))

            right_x = center_x + (20 * math.cos(rad_degree))
            right_y = center_y - (20 * math.sin(rad_degree))

            vert_list = wind.region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw_wind_line = [(left_x, left_y), (center_x, center_y), (right_x, right_y)]

            strength = int(round((wind.strength * 255 / 100)))
            draw.polygon(draw_vert_list, fill=(strength, strength, strength))
            draw.line(draw_wind_line, fill="red", width=9)
            draw.text(wind.region.center, str(degree) + ", " + str(wind.strength), font=font_18, fill="white")

        im.save("output/oceanic_wind_output.png")

    def draw_winds(self):
        # Generating a new picture
        im = Image.new("RGB", (self.width, self.height), "white")
        draw = ImageDraw.Draw(im)

        draw.polygon(((0, 0), (0, self.height), (self.width, self.height), (self.width, 0)), fill="white")


        # Drawing every region
        #print("Centers")
        for region in self.v.voronoi:
            vert_list = region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            # Getting humidity values
            fill = region.biome.biome_color
            draw.polygon(draw_vert_list, fill=fill)

        for wind_index in self.v.winds:
            wind = self.v.winds[wind_index]

            degree = wind.direction
            rad_degree = degree / 180 * 3.14159

            # Drawing a line
            center = wind.region.center
            center_x = center[0]
            center_y = center[1]

            left_x = center_x - (20 * math.cos(rad_degree))
            left_y = center_y + (20 * math.sin(rad_degree))

            right_x = center_x + (20 * math.cos(rad_degree))
            right_y = center_y - (20 * math.sin(rad_degree))

            vert_list = wind.region.vertex_list_value

            draw_vert_list = []
            for vertex in vert_list:
                new_vertex = (vertex[0], vertex[1])
                draw_vert_list.append(new_vertex)

            draw_wind_line = [(left_x, left_y), (right_x, right_y)]

            strength = int(round((wind.strength * 255 / 100)))
            draw.polygon(draw_vert_list, fill=(strength, strength, strength))
            draw.line(draw_wind_line, fill="red", width=9)
            draw.text(wind.region.center, str(int(round(degree))) + ", " + str(int(round(wind.strength))), font=font_18, fill="white")

        im.save("output/wind_output.png")

# Setting a seed
def gen_seed():
    # Helper tool for generating a seed
    return random.randrange(10000, 100000)

# print(get_angle_between_points((500,2550),(520,2600)))
# Good Seeds: 12345
SEED = gen_seed()
print("Generating with seed: " + str(SEED))
m = Main(6800, 4200, 5000, 5, SEED)

# Generating landscapes
m.gen_shapes_land(10, 3200, 0.8, (5, 10), 5, (1, 5), 1, SEED)
m.gen_shapes_land(6, 600, 0.8, (5, 10), 5, (1, 5), 1, SEED)
m.gen_shapes_land(6, 700, 1.8, (10, 20), 5, (2, 10), 0, SEED)
m.gen_shape_water(3, 1000, 0.5, (25, 45), 5, (2, 10), 1, SEED)

m.run()
m.v.display()
m.draw()
m.border_draw()
m.draw_geology()
m.draw_region_overlap()
m.draw_elevation(1)
m.draw_index()
m.draw_ocean_set()
m.draw_edge_set()
m.draw_temperature_set()
m.draw_mountains_set()
m.draw_humidity()
m.draw_oceanic_wind()
m.draw_winds()