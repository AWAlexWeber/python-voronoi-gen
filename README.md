# Python Voronoi Generation
Using 2D-based Voronoi polygon generation as a base for random terrain generation using a variety of real-world algorithms.

## How to use
Download the repository, using pip install all of the base-level requirements found in main.py. Then run main, making configurations as you like.

# Generation overview #

## Tectonics
The generation revolves around taking a voronoi graph and performing a variety of computations against it, largely revolving around neighbors and positional data. The first steps that we make is generate random set of N random shapes, using a base shape set. Our base shape set is as follows:

### Square
square = [(0.2,0),(1,0),(1,1),(0,1)]

### Diamond
diamond = [(0.5,0),(1,0.5),(0.5,1),(0,0.5)]

### Triangle
triangle = [(0.2,1),(0.5,0),(1,1)]

All of which can be found in shapegen.py. We then take these shapes and iteratively calculate the midpoints between all edges, and make adjustments to the position of that midpoint randomly. This will create more and more points, changing the shape dramatically the deeper we go. 

## Geology & Heightmap

We then take these shapes and place them randomly as tectonic plates in our world, assigning them a 'Geology' value. The geology value (sedimentary, igneous, and metamorphic) determines the 'hardness' of our tectonic plate, changing how the heightmap generates.

Finally, we use the overlaps on all of the tectconic plates as well as their geology values to generate a conflict map. This conflict map, in combination with the generation of a set of mountains based on high conflict zones, creates our final heightmap and terrian map.

![Geology Output with Conflicts](https://i.imgur.com/BhotUMK.png)
![Tectonic Conflict Map](https://i.imgur.com/FrnlnHp.png)
![Final Heightmap](https://i.imgur.com/9mHBiAJ.png)
![Final Overview](https://i.imgur.com/8OYyanC.png)

## Temperature & Oceans

Using the generated elevations we generate a terrain gradient primarily based off of position closed to the equator but also based on elevation regions. We combine this, with our calculation of the ocean to create humidity zones, which are zones where oceans of different temperatures meet.

![Temperature Map](https://i.imgur.com/pQ0fQw8.png)

Below we can see the oceans that were generated. Each ocean is assigned an average temperature. The point where oceans of varying temperatures meet create our humidity zones which can be seen below.
![Oceanic Map](https://i.imgur.com/yO6wptg.png)
![Humidity Zones](https://i.imgur.com/SrE0xtG.png)

## Wind

Next, we generate a wind output map which uses temperature gradients to determine the direction of wind, using a variety of different features (such as temperature, elevation, inertia) to determine which direction to flow.

![Wind Map](https://i.imgur.com/AKPCpnP.png)
