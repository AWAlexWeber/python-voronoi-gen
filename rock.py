import random

# Rock database list
class RockDatabase:

    def __init__(self):

        self.db = {}

        # Debug layer
        Debug = RockTableEntry("Debug", "red", "Sedimentary", 0.8)

        # Building the sedimentary layers
        Dolomite = RockTableEntry("Dolomite", "#5B5B50", "Sedimentary", 0.60)
        Shale = RockTableEntry("Shale", "#56565B", "Sedimentary", 0.85)
        Limestone = RockTableEntry("Limestone", "#6A6A6B", "Sedimentary", 0.55)
        Siltstone = RockTableEntry("Siltstone", "#7F6C6B", "Sedimentary", 0.35)

        # Assigning a default list for the land-based rocks
        self.land_default = [Dolomite, Shale, Siltstone]

        # Assigning some default values
        self.defaultRock = Limestone

        self.addRockEntry(Debug)
        self.addRockEntry(Dolomite)
        self.addRockEntry(Shale)
        self.addRockEntry(Limestone)
        self.addRockEntry(Siltstone)

    def addRockEntry(self, rock):
        self.db[rock.rock_name] = rock

    def getDefaultLandRock(self):
        length = len(self.land_default)
        random_index = random.randrange(0, length)
        return_rock = self.land_default[random_index]
        return return_rock

    def getDefaultOceanRock(self):
        return self.defaultRock

# Entry class
class RockTableEntry:

    def __init__(self, rock_name, rock_color, rock_type, rock_hardness):

        # Defining all of the inforamtion we need for a layer
        self.rock_name = rock_name
        self.rock_color = rock_color
        self.rock_type = rock_type
        self.rock_hardness = rock_hardness

# Object that contains all of the rock layers
class RockLayer:

    def __init__(self):
        self.rock_layer_list = []

    def __init__(self, rock_default):
        self.rock_layer_list = [rock_default]