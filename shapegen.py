# Imports
import matplotlib.pyplot as plt
import random
import math
from scipy import dot
from scipy import sin
from scipy import cos
from scipy import array as ar


debug = 0

# Default shapes

# Square
square = [(0.2,0),(1,0),(1,1),(0,1)]

# Diamond
diamond = [(0.5,0),(1,0.5),(0.5,1),(0,0.5)]

# Triangle
triangle = [(0.2,1),(0.5,0),(1,1)]

# List
shapeList = [square, diamond, triangle]

# Options for randomizing the position of the shape
# Pretend this is a fraction, 'smaller' number = more centralized shapes
center_power = (5, 7)

# Class for containing shape information
class Shape:

    def __init__(self, volatility, scale, eschew, numSubdivisions, finalScaleRange, dimensions, tectonic, SEED):

        # Setting seed
        random.seed(SEED)

        # Generating a random shape
        self.volatility = volatility
        self.eschew = eschew
        self.subdivision_count = 1
        self.finalScaleRange = finalScaleRange
        # Selecting a random shape
        self.vertex_list = random.choice(shapeList)[:]
        self.shape_index = -1
        self.tectonic = tectonic
        self.dimensions = dimensions

        self.base_rock = -1

        # Subdividing
        for x in range(0,numSubdivisions):
            self.subdivide()

        # Random rotation
        randomRotation = random.randrange(0,360)

        # Applying the rotation
        self.rotate(randomRotation)

        self.scale(scale)

        # Generating the random scale
        randomScaleDirection = random.randrange(0,359)
        if (finalScaleRange[0] == finalScaleRange[1]):
            randomScaleValue = finalScaleRange[0]
        else:
            minVal = round(finalScaleRange[0] * 100)
            maxVal = round(finalScaleRange[1] * 100)
            randomScaleValue = random.randrange(minVal, maxVal)
            randomScaleValue = randomScaleValue / 100
        self.random_scale(randomScaleDirection, randomScaleValue)

        # Loading to middle before offsetting...
        self.load_to_middle()

        # Finally, randomly positioning our object within the range...
        x_offset = random.randrange(-center_power[0] * round(dimensions[0] / center_power[1]), center_power[0] * round(dimensions[0] / center_power[1]))
        y_offset = random.randrange(-center_power[0] * round(dimensions[1] / center_power[1]), center_power[0] * round(dimensions[1] / center_power[1]))

        self.offset(x_offset, y_offset)

    def initSpecial(self, vertex_list, volatility, eschew):
        self.vertex_list = vertex_list[:]
        self.volatility = volatility
        self.eschew = eschew
        self.subdivision_count = 1

    def subdivide(self):
        if (debug):
            print(self.vertex_list)

        # First we need to iteratively find all of the middlepoints
        newpoints = self.vertex_list[:]

        count = 1
        insertIndex = 1
        for point in self.vertex_list:

            startX = point[0]
            startY = point[1]

            endX = self.vertex_list[count][0]
            endY = self.vertex_list[count][1]

            middleX = (startX + endX) / 2
            middleY = (startY + endY) / 2




            # Calculating the inverse slope
            rise = endY - startY
            run = endX - startX

            if run == 0:
                slope = 100
            else:
                slope = rise / run

            # Calculating the inverse
            if slope != 0:
                inverse_slope = 1 / slope * -1
            else:
                inverse_slope = 100

            # Calculating the y-intercept
            inverse_intercept = middleY - inverse_slope * middleX

            # Generating an arbitrary point
            arbitrary_point = (0, inverse_intercept)






            # Calculating V
            v = (arbitrary_point[0] - middleX, arbitrary_point[1] - middleY)

            # Calculating U
            bottom = math.sqrt( (v[0] * v[0]) + (v[1] * v[1]) )

            if (bottom == 0):
                bottom = 0.001

            uleft = v[0] / bottom
            uright = v[1] / bottom

            # Calculating strength
            strength = random.randrange(self.eschew[0],self.eschew[1])
            strength = strength / 10

            if (random.randrange(0,100) > 50):
                strength = strength * -1

            middleX += ( strength * (self.volatility / self.subdivision_count) * uleft)
            middleY += ( strength * (self.volatility / self.subdivision_count) * uright)







            middle = (middleX, middleY)

            newpoints.insert(insertIndex, middle)

            insertIndex = insertIndex + 2

            count = count + 1
            if (count >= len(self.vertex_list)):
                count = 0

        self.vertex_list = newpoints

        self.subdivision_count = self.subdivision_count + 4

    def draw(self):

        # Creating x/y list
        x = []
        y = []

        # Iterating on all of the points
        for point in self.vertex_list:
            x.append(point[0])
            y.append(point[1])

        # Doing the final point
        x.append(self.vertex_list[0][0])
        y.append(self.vertex_list[0][1])

        # Plotting and showing the final amount
        plt.plot(x,y)
        plt.show()

    def rotate(self, angle=3.14159/4):
        # Calculating the center
        x = 0
        y = 0
        vertex_count = 0

        for point in self.vertex_list:
            x += point[0]
            y += point[1]
            vertex_count += 1

        x = x/vertex_count
        y = y/vertex_count

        center = (x,y)


        # Rotating
        self.vertex_list = dot(ar(self.vertex_list)-center,ar([[cos(angle),sin(angle)],[-sin(angle),cos(angle)]]))+center

    def scale(self, scale):
        # Scaling all points
        for point in self.vertex_list:
            point[0] = point[0] * scale
            point[1] = point[1] * scale

    def random_scale(self, rotation, value):
        # Randomly scaling in a certain direction
        if (debug):
            print("Randomly scaling with angle of " + str(rotation) + " and strength of " + str(value))

        # Skewing everything in the given angle by the given value
        # We take all points within our shape,

    # Function that adds an offset value
    def offset(self, x_offset, y_offset):
        for point in self.vertex_list:
            point[0] = point[0] + x_offset
            point[1] = point[1] + y_offset

    def load_to_zero(self):
        # Taking the shape and ensuring the smallest numeric value is 0
        smallest_x = 9999
        smallest_y = 9999

        for point in self.vertex_list:
            if (point[0] < smallest_x):
                smallest_x = point[0]
            if (point[1] < smallest_y):
                smallest_y = point[1]

        # Allowing us to stay not perfectly close
        smallest_y = smallest_y * 0.9
        smallest_x = smallest_x * 0.9

        # Taking this information and offsetting everything
        self.offset(-smallest_x, -smallest_y)

    def load_to_middle(self):
        # Taking the shape and ensuring the smallest numeric value is 0
        x = 0
        y = 0

        size = len(self.vertex_list)

        for point in self.vertex_list:
            x = x + point[0]
            y = y + point[1]

        # Allowing us to stay not perfectly close
        x = x / size
        y = y / size

        # We now have the center
        # Loading the entire shape to the middle now
        center_x = self.dimensions[0] / 2
        center_y = self.dimensions[1] / 2

        adjust_x = center_x - x
        adjust_y = center_y - y


        # Taking this information and offsetting everything
        self.offset(adjust_x, adjust_y)