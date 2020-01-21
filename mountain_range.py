import random

class Mountain:

    def __init__(self, region, growth_angle, mountain_range, mountain_strength):
        self.mountain_index = region.index
        self.region = region

        # Mountain elevation is an adjustment value, not an absolute value
        self.mountain_elevation = 0

        # Which direction to grow towards
        self.growth_angle = growth_angle

        # Tracking our mountain range
        self.mountain_range = mountain_range

        # Setting the strength value...
        self.mountain_strength = mountain_strength

        # If we have grown yet
        self.grown = 0


class MountainRange:

    def __init__(self, range_index, input_root_region, growth_angle):

        # Range index is just an indexing value for this mountain range
        self.range_index = range_index

        # Root tile is the base root tile
        self.root_tile = Mountain(input_root_region, growth_angle, self, 1)
        inverse_angle = 180 + growth_angle
        if inverse_angle > 360:
            inverse_angle = 360 - inverse_angle

        # Angle that represents which way this mountain range is going to grow
        self.base_growth_angle = growth_angle

        # Constructing the mountain range list
        # Dictionary where the index is the mountain index, also the region index
        self.mountains = {}

        # Setting mountain color
        self.color = (random.randrange(0,255), random.randrange(0,255), random.randrange(0,255))

        # Appending the base
        self.mountains[self.root_tile.mountain_index] = self.root_tile