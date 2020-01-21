<h1>Geology Generation Rules</h1>

Quick Geology Overview:

Sedimentary:
    Top-layer rock layer, usually defined by what
    is happening ABOVE the layer
    
Igneous:
    Igenous is formed from hot-magma that cools. This
       means that it will mostly be seen in areas with
       high volcanic activity. Think the ocean,
       as well as where tectonic plates meet

Metamorphic:
    Metamorphic rocks are any of the above that have
    gone under extreme pressure or heat. This is why
    the metamorphic layer will usually be near the bottom
    

The geology of the world is an important tool when building a world.
The first thing we need to pay attention to is that the
oceans have lots of sea life and will almost
dominantely be filled with limestone

# Steps to build Geology

1) Determine the top-layers by what is happening. This
usually means if its ocean then we are going to be looking
almost entirely at the limestone layer. Deeper oceans will
become part of basalt later. All other land becomes either
    1a. Siltstone, Shale, or Dolomite
    
These are our base layers. During the later process
we will begin making some adjustments, as weather, water levels
and vegetation all makes adjustments...

# Steps to determininig elevation

Elevation is a complicated metric, but one that is vital to the
development of our world. We consider two things

1. Number of tectonic interactions at the region
2. Type of base-rock assigned to the region

These two values give us our default heightmap. Once
weve built our default heightmap, we begin our first
errosion algorithm which is really just an averaging function

However, there is a little more complexity to it. Any
region that has the maximum possible height will not
average its height out, becoming instead a source node

Same goes for the lowest (excluding of course the ocean)

Finally, we will run an elevation smoothing algorithm on the ocean
floor as well. This will mostly pick random spots to become
ocean trenches, which will contain basalt. From there we will
begin averaging out the elevations