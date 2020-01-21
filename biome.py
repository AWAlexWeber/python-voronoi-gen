# This class represents a biome
# These are held within the voronoi objects
import random

debug = 0

# Database for holding our biome table entry thingy
class BiomeDatabase:

    def __init__(self):

        debug = BiomeTableEntry(0, "DEBUG", "red", "Land")
        deep_ocean = BiomeTableEntry(1, "Deep Ocean", "#91BFFF", "Water")
        grassland = BiomeTableEntry(2, "Grassland", "green", "Land")

        self.db = [debug, deep_ocean, grassland]

    def get_entry(self, index):
        return self.db[index]

class BiomeTableEntry:

    def __init__(self, index, biome_name, biome_color, land_type):
        self.index = index
        self.biome_name = biome_name
        self.biome_color = biome_color
        self.land_type = land_type

# Biome objects list
# Contains the information, or database for all the biome information
biomeDatabase = BiomeDatabase()

class Biome:

    def __copy__(self):

        copy_biome = Biome(self.entry_index)
        return copy_biome

    def __init__(self, index):
        # Using the index to build a biome
        if (debug == 1):
            print("Building biome with index")

        entry = biomeDatabase.get_entry(index)
        self.entry_index = index
        self.biome_color = entry.biome_color
        self.land_type = entry.land_type
        self.biome_name = entry.biome_name
        self.biome_index = entry.index


    def reload_index(self, index):

        entry = biomeDatabase.get_entry(index)
        self.entry_index = index
        self.biome_color = entry.biome_color
        self.land_type = entry.land_type
        self.biome_name = entry.biome_name
        self.biome_index = entry.index