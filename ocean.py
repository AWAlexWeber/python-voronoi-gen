# File that manages ocean classes

class Ocean:

    def __init__(self, index):

        # Whether or not the ocean object has been initialized
        self.initialized = 0

        # The set of tiles that this ocean owns
        self.region_set = []

        # The color of the ocean as a set
        self.color = (50, 50, 240)

        # Setting index
        self.ocean_index = index

        # Root tile
        self.root_tile = None

        self.land_neighbor_count = 0

        self.merged = 0

        self.inland_sea = 0

        self.fresh_water = 0
