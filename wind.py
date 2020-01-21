# Class for managing wind...
class Wind:

    def __init__(self, index, region, direction, strength):
        self.index = index
        self.region = region
        self.direction = direction
        self.strength = strength
        self.grown = 0
        self.wind_neighbor = None

        self.stored_humidity = 0