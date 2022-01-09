'''
=============================
Dungeon Generation Algorithms
=============================

This is an implimentation of some of the dungeon generating
algorithms that are often brought up when talking about roguelikes.

Most of these algorithms have been copied from online sources.
I've included those sources where aplicable.

A lot of my implimentations of these algorithms are overly complicated
(especially in how the different algorithm classes interact with
the rest of the module). The main reason for this is that I wanted
each of the algorithm classes to be easily portable into other
projects. My success in that reguard is up for debate.
'''

import random
from math import sqrt

SCREEN_WIDTH = 80
SCREEN_HEIGHT = 60
TEXTBOX_HEIGHT = 10

MAP_WIDTH = SCREEN_WIDTH
MAP_HEIGHT = SCREEN_HEIGHT - TEXTBOX_HEIGHT

USE_PREFABS = False


# ==== Map Class ====

class Map:
    def __init__(self):
        self.level = []
        '''
        level values of 1 are walls
        level values of 0 are floors
        '''
        self._previousGenerator = self
        self.tunnelingAlgorithm = TunnelingAlgorithm()
        self.bspTree = BSPTree()
        # self.drunkardsWalk = DrunkardsWalk()
        # self.cellularAutomata = CellularAutomata()
        # self.roomAddition = RoomAddition()
        self.mazeWithRooms = MazeWithRooms()

        self.cityWalls = CityWalls()

        self.messyBSPTree = MessyBSPTree()

    def generateLevel(self, MAP_WIDTH, MAP_HEIGHT):
        # Creates an empty 2D array or clears existing array
        self.level = [[0
                       for y in range(MAP_HEIGHT)]
                      for x in range(MAP_WIDTH)]

        return self.level

        print("Flag: map.generateLevel()")

    def useTunnelingAlgorithm(self):
        self.level = self.tunnelingAlgorithm.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.tunnelingAlgorithm

    def useBSPTree(self):
        self.level = self.bspTree.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.bspTree

    def useDrunkardsWalk(self):
        self.level = self.drunkardsWalk.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.drunkardsWalk

    def useCellularAutomata(self):
        self.level = self.cellularAutomata.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.cellularAutomata

    def useRoomAddition(self):
        self.level = self.roomAddition.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.roomAddition

    def useCityWalls(self):
        self.level = self.cityWalls.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.cityWalls

    def useMazeWithRooms(self):
        self.level = self.mazeWithRooms.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.mazeWithRooms

    def useMessyBSPTree(self):
        self.level = self.messyBSPTree.generateLevel(MAP_WIDTH, MAP_HEIGHT)
        self._previousGenerator = self.messyBSPTree


# ==== Tunneling Algorithm ====
class TunnelingAlgorithm:
    '''
    This version of the tunneling algorithm is essentially
    identical to the tunneling algorithm in the Complete Roguelike
    Tutorial using Python, which can be found at
    http://www.roguebasin.com/index.php?title=Complete_Roguelike_Tutorial,_using_python%2Blibtcod,_part_1

    Requires random.randint() and the Rect class defined below.
    '''

    def __init__(self):
        self.level = []
        self.ROOM_MAX_SIZE = 15
        self.ROOM_MIN_SIZE = 6
        self.MAX_ROOMS = 30

    # TODO: raise an error if any necessary classes are missing

    def generateLevel(self, mapWidth, mapHeight):
        # Creates an empty 2D array or clears existing array
        self.level = [[1
                       for y in range(mapHeight)]
                      for x in range(mapWidth)]

        rooms = []
        num_rooms = 0

        for r in range(self.MAX_ROOMS):
            # random width and height
            w = random.randint(self.ROOM_MIN_SIZE, self.ROOM_MAX_SIZE)
            h = random.randint(self.ROOM_MIN_SIZE, self.ROOM_MAX_SIZE)
            # random position within map boundries
            x = random.randint(0, MAP_WIDTH - w - 1)
            y = random.randint(0, MAP_HEIGHT - h - 1)

            new_room = Rect(x, y, w, h)
            # check for overlap with previous rooms
            failed = False
            for other_room in rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                self.createRoom(new_room)
                (new_x, new_y) = new_room.center()

                if num_rooms != 0:
                    # all rooms after the first one
                    # connect to the previous room

                    # center coordinates of the previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()

                    # 50% chance that a tunnel will start horizontally
                    if random.randint(0, 1) == 1:
                        self.createHorTunnel(prev_x, new_x, prev_y)
                        self.createVirTunnel(prev_y, new_y, new_x)

                    else:  # else it starts virtically
                        self.createVirTunnel(prev_y, new_y, prev_x)
                        self.createHorTunnel(prev_x, new_x, new_y)

                # append the new room to the list
                rooms.append(new_room)
                num_rooms += 1

        return self.level

    def createRoom(self, room):
        # set all tiles within a rectangle to 0
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.level[x][y] = 0

    def createHorTunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.level[x][y] = 0

    def createVirTunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.level[x][y] = 0


# ==== BSP Tree ====
class BSPTree:
    def __init__(self):
        self.level = []
        self.room = None
        self.MAX_LEAF_SIZE = 45
        self.ROOM_MAX_SIZE = 30
        self.ROOM_MIN_SIZE = 9

    def generateLevel(self, mapWidth, mapHeight):
        # Creates an empty 2D array or clears existing array
        self.level = [[1
                       for y in range(mapHeight)]
                      for x in range(mapWidth)]

        self._leafs = []

        rootLeaf = Leaf(0, 0, mapWidth, mapHeight)
        self._leafs.append(rootLeaf)

        splitSuccessfully = True
        # loop through all leaves until they can no longer split successfully
        while (splitSuccessfully):
            splitSuccessfully = False
            for l in self._leafs:
                if (l.child_1 == None) and (l.child_2 == None):
                    if ((l.width > self.MAX_LEAF_SIZE) or
                            (l.height > self.MAX_LEAF_SIZE) or
                            (random.random() > 0.8)):
                        if (l.splitLeaf()):  # try to split the leaf
                            self._leafs.append(l.child_1)
                            self._leafs.append(l.child_2)
                            splitSuccessfully = True

        rootLeaf.createRooms(self)

        return self.level

    def createRoom(self, room):
        # set all tiles within a rectangle to 0
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.level[x][y] = 0

    def createHall(self, room1, room2):
        # connect two rooms by hallways
        x1, y1 = room1.center()
        x2, y2 = room2.center()
        # 50% chance that a tunnel will start horizontally
        if random.randint(0, 1) == 1:
            self.createHorTunnel(x1, x2, y1)
            self.createVirTunnel(y1, y2, x2)

        else:  # else it starts virtically
            self.createVirTunnel(y1, y2, x1)
            self.createHorTunnel(x1, x2, y2)

    def createHorTunnel(self, x1, x2, y):
        for x in range(min(int(x1), int(x2)), max(int(x1), int(x2)) + 1):
            self.level[x][int(y)] = 0

    def createVirTunnel(self, y1, y2, x):
        for y in range(min(int(y1), int(y2)), max(int(y1), int(y2)) + 1):
            self.level[int(x)][y] = 0


# ==== City Walls ====
class CityWalls:
    '''
    The City Walls algorithm is very similar to the BSP Tree
    above. In fact their main difference is in how they generate
    rooms after the actual tree has been created. Instead of
    starting with an array of solid walls and carving out
    rooms connected by tunnels, the City Walls generator
    starts with an array of floor tiles, then creates only the
    exterior of the rooms, then opens one wall for a door.
    '''

    def __init__(self):
        self.level = []
        self.room = None
        self.MAX_LEAF_SIZE = 30
        self.ROOM_MAX_SIZE = 16
        self.ROOM_MIN_SIZE = 8

    def generateLevel(self, mapWidth, mapHeight):
        # Creates an empty 2D array or clears existing array
        self.level = [[0
                       for y in range(mapHeight)]
                      for x in range(mapWidth)]

        self._leafs = []
        self.rooms = []

        rootLeaf = Leaf(0, 0, mapWidth, mapHeight)
        self._leafs.append(rootLeaf)

        splitSuccessfully = True
        # loop through all leaves until they can no longer split successfully
        while (splitSuccessfully):
            splitSuccessfully = False
            for l in self._leafs:
                if (l.child_1 == None) and (l.child_2 == None):
                    if ((l.width > self.MAX_LEAF_SIZE) or
                            (l.height > self.MAX_LEAF_SIZE) or
                            (random.random() > 0.8)):
                        if (l.splitLeaf()):  # try to split the leaf
                            self._leafs.append(l.child_1)
                            self._leafs.append(l.child_2)
                            splitSuccessfully = True

        rootLeaf.createRooms(self)
        self.createDoors()

        return self.level

    def createRoom(self, room):
        # Build Walls
        # set all tiles within a rectangle to 1
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.level[x][y] = 1
        # Build Interior
        for x in range(room.x1 + 2, room.x2 - 1):
            for y in range(room.y1 + 2, room.y2 - 1):
                self.level[x][y] = 0

    def createDoors(self):
        for room in self.rooms:
            (x, y) = room.center()

            wall = random.choice(["north", "south", "east", "west"])
            if wall == "north":
                wallX = x
                wallY = room.y1 + 1
            elif wall == "south":
                wallX = x
                wallY = room.y2 - 1
            elif wall == "east":
                wallX = room.x2 - 1
                wallY = y
            elif wall == "west":
                wallX = room.x1 + 1
                wallY = y

            self.level[wallX][wallY] = 0

    def createHall(self, room1, room2):
        # This method actually creates a list of rooms,
        # but since it is called from an outside class that is also
        # used by other dungeon Generators, it was simpler to
        # repurpose the createHall method that to alter the leaf class.
        for room in [room1, room2]:
            if room not in self.rooms:
                self.rooms.append(room)


# ==== Maze With Rooms ====
class MazeWithRooms:
    '''
    Python implimentation of the rooms and mazes algorithm found at
    http://journal.stuffwithstuff.com/2014/12/21/rooms-and-mazes/
    by Bob Nystrom
    '''

    def __init__(self):
        self.level = []

        self.ROOM_MAX_SIZE = 13
        self.ROOM_MIN_SIZE = 6

        self.buildRoomAttempts = 100
        self.connectionChance = 0.04
        self.windingPercent = 0.1
        self.allowDeadEnds = False

    def generateLevel(self, mapWidth, mapHeight):
        # The level dimensions must be odd
        self.level = [[1
                       for y in range(mapHeight)]
                      for x in range(mapWidth)]
        if (mapWidth % 2 == 0): mapWidth -= 1
        if (mapHeight % 2 == 0): mapHeight -= 1

        self._regions = [[None
                          for y in range(mapHeight)]
                         for x in range(mapWidth)]

        self._currentRegion = -1  # the index of the current region in _regions

        self.addRooms(mapWidth, mapHeight)  # ?

        # Fill in the empty space around the rooms with mazes
        for y in range(1, mapHeight, 2):
            for x in range(1, mapWidth, 2):
                if self.level[x][y] != 1:
                    continue
                start = (x, y)
                self.growMaze(start, mapWidth, mapHeight)

        self.connectRegions(mapWidth, mapHeight)

        if not self.allowDeadEnds:
            self.removeDeadEnds(mapWidth, mapHeight)

        return self.level

    def growMaze(self, start, mapWidth, mapHeight):
        north = (0, -1)
        south = (0, 1)
        east = (1, 0)
        west = (-1, 0)

        cells = []
        lastDirection = None

        self.startRegion()
        self.carve(start[0], start[1])

        cells.append(start)

        while cells:
            cell = cells[-1]

            # see if any adjacent cells are open
            unmadeCells = set()

            '''
            north = (0,-1)
            south = (0,1)
            east = (1,0)
            west = (-1,0)
            '''
            for direction in [north, south, east, west]:
                if self.canCarve(cell, direction, mapWidth, mapHeight):
                    unmadeCells.add(direction)

            if (unmadeCells):
                '''
                Prefer to carve in the same direction, when
                it isn't necessary to do otherwise.
                '''
                if ((lastDirection in unmadeCells) and
                        (random.random() > self.windingPercent)):
                    direction = lastDirection
                else:
                    direction = unmadeCells.pop()

                newCell = ((cell[0] + direction[0]), (cell[1] + direction[1]))
                self.carve(newCell[0], newCell[1])

                newCell = ((cell[0] + direction[0] * 2), (cell[1] + direction[1] * 2))
                self.carve(newCell[0], newCell[1])
                cells.append(newCell)

                lastDirection = direction

            else:
                # No adjacent uncarved cells
                cells.pop()
                lastDirection = None

    def addRooms(self, mapWidth, mapHeight):
        rooms = []
        for i in range(self.buildRoomAttempts):

            '''
            Pick a random room size and ensure that rooms have odd 
            dimensions and that rooms are not too narrow.
            '''
            roomWidth = random.randint(int(self.ROOM_MIN_SIZE / 2), int(self.ROOM_MAX_SIZE / 2)) * 2 + 1
            roomHeight = random.randint(int(self.ROOM_MIN_SIZE / 2), int(self.ROOM_MAX_SIZE / 2)) * 2 + 1
            x = (random.randint(0, mapWidth - roomWidth - 1) / 2) * 2 + 1
            y = (random.randint(0, mapHeight - roomHeight - 1) / 2) * 2 + 1

            room = Rect(x, y, roomWidth, roomHeight)
            # check for overlap with previous rooms
            failed = False
            for otherRoom in rooms:
                if room.intersect(otherRoom):
                    failed = True
                    break

            if not failed:
                rooms.append(room)

                self.startRegion()
                self.createRoom(room)

    def connectRegions(self, mapWidth, mapHeight):
        # Find all of the tiles that can connect two regions
        north = (0, -1)
        south = (0, 1)
        east = (1, 0)
        west = (-1, 0)

        connectorRegions = [[None
                             for y in range(mapHeight)]
                            for x in range(mapWidth)]

        for x in range(1, mapWidth - 1):
            for y in range(1, mapHeight - 1):
                if self.level[x][y] != 1: continue

                # count the number of different regions the wall tile is touching
                regions = set()
                for direction in [north, south, east, west]:
                    newX = x + direction[0]
                    newY = y + direction[1]
                    region = self._regions[newX][newY]
                    if region != None:
                        regions.add(region)

                if (len(regions) < 2): continue

                # The wall tile touches at least two regions
                connectorRegions[x][y] = regions

        # make a list of all of the connectors
        connectors = set()
        for x in range(0, mapWidth):
            for y in range(0, mapHeight):
                if connectorRegions[x][y]:
                    connectorPosition = (x, y)
                    connectors.add(connectorPosition)

        # keep track of the regions that have been merged.
        merged = {}
        openRegions = set()
        for i in range(self._currentRegion + 1):
            merged[i] = i
            openRegions.add(i)

        # connect the regions
        while len(openRegions) > 1:
            # get random connector
            # connector = connectors.pop()
            for connector in connectors: break

            # carve the connection
            self.addJunction(connector)

            # merge the connected regions
            x = connector[0]
            y = connector[1]

            # make a list of the regions at (x,y)
            regions = []
            for n in connectorRegions[x][y]:
                # get the regions in the form of merged[n]
                actualRegion = merged[n]
                regions.append(actualRegion)

            dest = regions[0]
            sources = regions[1:]

            '''
            Merge all of the effective regions. You must look
            at all of the regions, as some regions may have
            previously been merged with the ones we are
            connecting now.
            '''
            for i in range(self._currentRegion + 1):
                if merged[i] in sources:
                    merged[i] = dest

            # clear the sources, they are no longer needed
            for s in sources:
                openRegions.remove(s)

            # remove the unneeded connectors
            toBeRemoved = set()
            for pos in connectors:
                # remove connectors that are next to the current connector
                if self.distance(connector, pos) < 2:
                    # remove it
                    toBeRemoved.add(pos)
                    continue

                regions = set()
                x = pos[0]
                y = pos[1]
                for n in connectorRegions[x][y]:
                    actualRegion = merged[n]
                    regions.add(actualRegion)
                if len(regions) > 1:
                    continue

                if random.random() < self.connectionChance:
                    self.addJunction(pos)

                # remove it
                if len(regions) == 1:
                    toBeRemoved.add(pos)

            connectors.difference_update(toBeRemoved)

    def createRoom(self, room):
        # set all tiles within a rectangle to 0
        for x in range(room.x1, room.x2):
            for y in range(room.y1, room.y2):
                self.carve(x, y)

    def addJunction(self, pos):
        self.level[pos[0]][pos[1]] = 0

    def removeDeadEnds(self, mapWidth, mapHeight):
        done = False

        north = (0, -1)
        south = (0, 1)
        east = (1, 0)
        west = (-1, 0)

        while not done:
            done = True

            for y in range(1, mapHeight):
                for x in range(1, mapWidth):
                    if self.level[x][y] == 0:

                        exits = 0
                        for direction in [north, south, east, west]:
                            if self.level[x + direction[0]][y + direction[1]] == 0:
                                exits += 1
                        if exits > 1: continue

                        done = False
                        self.level[x][y] = 1

    def canCarve(self, pos, dir, mapWidth, mapHeight):
        '''
        gets whether an opening can be carved at the location
        adjacent to the cell at (pos) in the (dir) direction.
        returns False if the location is out of bounds or if the cell
        is already open.
        '''
        x = pos[0] + dir[0] * 3
        y = pos[1] + dir[1] * 3

        if not (0 < x < mapWidth) or not (0 < y < mapHeight):
            return False

        x = pos[0] + dir[0] * 2
        y = pos[1] + dir[1] * 2

        # return True if the cell is a wall (1)
        # false if the cell is a floor (0)
        return (self.level[x][y] == 1)

    def distance(self, point1, point2):
        d = sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)
        return d

    def startRegion(self):
        self._currentRegion += 1

    def carve(self, x, y):
        self.level[x][y] = 0
        self._regions[x][y] = self._currentRegion


# ==== Maze ====

# ==== Messy BSP Tree ====
class MessyBSPTree:
    '''
    A Binary Space Partition connected by a severely weighted
    drunkards walk algorithm.
    Requires Leaf and Rect classes.
    '''

    def __init__(self):
        self.level = []
        self.room = None
        self.MAX_LEAF_SIZE = 24
        self.ROOM_MAX_SIZE = 15
        self.ROOM_MIN_SIZE = 6
        self.smoothEdges = True
        self.smoothing = 1
        self.filling = 3

    def generateLevel(self, mapWidth, mapHeight):
        # Creates an empty 2D array or clears existing array
        self.mapWidth = mapWidth
        self.mapHeight = mapHeight
        self.level = [[1
                       for y in range(mapHeight)]
                      for x in range(mapWidth)]

        self._leafs = []

        rootLeaf = Leaf(0, 0, mapWidth, mapHeight)
        self._leafs.append(rootLeaf)

        splitSuccessfully = True
        # loop through all leaves until they can no longer split successfully
        while (splitSuccessfully):
            splitSuccessfully = False
            for l in self._leafs:
                if (l.child_1 == None) and (l.child_2 == None):
                    if ((l.width > self.MAX_LEAF_SIZE) or
                            (l.height > self.MAX_LEAF_SIZE) or
                            (random.random() > 0.8)):
                        if (l.splitLeaf()):  # try to split the leaf
                            self._leafs.append(l.child_1)
                            self._leafs.append(l.child_2)
                            splitSuccessfully = True

        rootLeaf.createRooms(self)
        self.cleanUpMap(mapWidth, mapHeight)

        return self.level

    def createRoom(self, room):
        # set all tiles within a rectangle to 0
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.level[x][y] = 0

    def createHall(self, room1, room2):
        # run a heavily weighted random Walk
        # from point2 to point1
        drunkardX, drunkardY = room2.center()
        goalX, goalY = room1.center()
        while not (room1.x1 <= drunkardX <= room1.x2) or not (room1.y1 < drunkardY < room1.y2):  #
            # ==== Choose Direction ====
            north = 1.0
            south = 1.0
            east = 1.0
            west = 1.0

            weight = 1

            # weight the random walk against edges
            if drunkardX < goalX:  # drunkard is left of point1
                east += weight
            elif drunkardX > goalX:  # drunkard is right of point1
                west += weight
            if drunkardY < goalY:  # drunkard is above point1
                south += weight
            elif drunkardY > goalY:  # drunkard is below point1
                north += weight

            # normalize probabilities so they form a range from 0 to 1
            total = north + south + east + west
            north /= total
            south /= total
            east /= total
            west /= total

            # choose the direction
            choice = random.random()
            if 0 <= choice < north:
                dx = 0
                dy = -1
            elif north <= choice < (north + south):
                dx = 0
                dy = 1
            elif (north + south) <= choice < (north + south + east):
                dx = 1
                dy = 0
            else:
                dx = -1
                dy = 0

            # ==== Walk ====
            # check colision at edges
            if (0 < drunkardX + dx < self.mapWidth - 1) and (0 < drunkardY + dy < self.mapHeight - 1):
                drunkardX += dx
                drunkardY += dy
                if self.level[drunkardX][drunkardY] == 1:
                    self.level[drunkardX][drunkardY] = 0

    def cleanUpMap(self, mapWidth, mapHeight):
        if (self.smoothEdges):
            for i in range(3):
                # Look at each cell individually and check for smoothness
                for x in range(1, mapWidth - 1):
                    for y in range(1, mapHeight - 1):
                        if (self.level[x][y] == 1) and (self.getAdjacentWallsSimple(x, y) <= self.smoothing):
                            self.level[x][y] = 0

                        if (self.level[x][y] == 0) and (self.getAdjacentWallsSimple(x, y) >= self.filling):
                            self.level[x][y] = 1

    def getAdjacentWallsSimple(self, x, y):  # finds the walls in four directions
        wallCounter = 0
        # print("(",x,",",y,") = ",self.level[x][y])
        if (self.level[x][y - 1] == 1):  # Check north
            wallCounter += 1
        if (self.level[x][y + 1] == 1):  # Check south
            wallCounter += 1
        if (self.level[x - 1][y] == 1):  # Check west
            wallCounter += 1
        if (self.level[x + 1][y] == 1):  # Check east
            wallCounter += 1

        return wallCounter


# ==== TinyKeep ====
'''
https://www.reddit.com/r/gamedev/comments/1dlwc4/procedural_dungeon_generation_algorithm_explained/
and
http://www.gamasutra.com/blogs/AAdonaac/20150903/252889/Procedural_Dungeon_Generation_Algorithm.php
'''


# ==== Helper Classes ====
class Rect:  # used for the tunneling algorithm
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        centerX = (self.x1 + self.x2) / 2
        centerY = (self.y1 + self.y2) / 2
        return (centerX, centerY)

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)


class Leaf:  # used for the BSP tree algorithm
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.MIN_LEAF_SIZE = 10
        self.child_1 = None
        self.child_2 = None
        self.room = None
        self.hall = None

    def splitLeaf(self):
        # begin splitting the leaf into two children
        if (self.child_1 != None) or (self.child_2 != None):
            return False  # This leaf has already been split

        '''
        ==== Determine the direction of the split ====
        If the width of the leaf is >25% larger than the height,
        split the leaf vertically.
        If the height of the leaf is >25 larger than the width,
        split the leaf horizontally.
        Otherwise, choose the direction at random.
        '''
        splitHorizontally = random.choice([True, False])
        if (self.width / self.height >= 1.25):
            splitHorizontally = False
        elif (self.height / self.width >= 1.25):
            splitHorizontally = True

        if (splitHorizontally):
            max = self.height - self.MIN_LEAF_SIZE
        else:
            max = self.width - self.MIN_LEAF_SIZE

        if (max <= self.MIN_LEAF_SIZE):
            return False  # the leaf is too small to split further

        split = random.randint(self.MIN_LEAF_SIZE, max)  # determine where to split the leaf

        if (splitHorizontally):
            self.child_1 = Leaf(self.x, self.y, self.width, split)
            self.child_2 = Leaf(self.x, self.y + split, self.width, self.height - split)
        else:
            self.child_1 = Leaf(self.x, self.y, split, self.height)
            self.child_2 = Leaf(self.x + split, self.y, self.width - split, self.height)

        return True

    def createRooms(self, bspTree):
        if (self.child_1) or (self.child_2):
            # recursively search for children until you hit the end of the branch
            if (self.child_1):
                self.child_1.createRooms(bspTree)
            if (self.child_2):
                self.child_2.createRooms(bspTree)

            if (self.child_1 and self.child_2):
                bspTree.createHall(self.child_1.getRoom(),
                                   self.child_2.getRoom())

        else:
            # Create rooms in the end branches of the bsp tree
            w = random.randint(bspTree.ROOM_MIN_SIZE, min(bspTree.ROOM_MAX_SIZE, self.width - 1))
            h = random.randint(bspTree.ROOM_MIN_SIZE, min(bspTree.ROOM_MAX_SIZE, self.height - 1))
            x = random.randint(self.x, self.x + (self.width - 1) - w)
            y = random.randint(self.y, self.y + (self.height - 1) - h)
            self.room = Rect(x, y, w, h)
            bspTree.createRoom(self.room)

    def getRoom(self):
        if (self.room):
            return self.room

        else:
            if (self.child_1):
                self.room_1 = self.child_1.getRoom()
            if (self.child_2):
                self.room_2 = self.child_2.getRoom()

            if (not self.child_1 and not self.child_2):
                # neither room_1 nor room_2
                return None

            elif (not self.room_2):
                # room_1 and !room_2
                return self.room_1

            elif (not self.room_1):
                # room_2 and !room_1
                return self.room_2

            # If both room_1 and room_2 exist, pick one
            elif (random.random() < 0.5):
                return self.room_1
            else:
                return self.room_2


class Prefab(Rect):
    pass


def generate_draw_map(filename="map.png"):
    map = Map()
    map.generateLevel(200, 200)
    map.useBSPTree()

    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (100, 100))

    pixels = img.load()
    number_of_rooms = 0

    rooms = []

    def retrieve_rooms(leaf):
        room = leaf.getRoom()
        if room not in rooms:
            rooms.append(room)
        if leaf.child_1 is not None:
            retrieve_rooms(leaf.child_1)
        if leaf.child_2 is not None:
            retrieve_rooms(leaf.child_2)

    for x in range(len(map.level)):
        y_array = map.level[x]
        for y in range(len(y_array)):
            if y_array[y] == 1:
                pixels[x, y] = (255, 255, 255)
            else:
                pixels[x, y] = (0, 0, 0)

    img = img.resize((1000, 1000), Image.AFFINE)
    image_editable = ImageDraw.Draw(img)

    font = ImageFont.truetype("fonts\\arial.ttf", 20)

    retrieve_rooms(map.bspTree._leafs[0])

    for i in range(len(rooms)):
        room = rooms[i]
        middleX = (room.x2 - room.x1) / 2 + room.x1
        middleY = (room.y2 - room.y1) / 2 + room.y1
        image_editable.text((middleX * 10, middleY * 10), f"{i}", (255, 0, 0), font=font)

    img.save(filename)

    return rooms


if __name__ == "__main__":
    generate_draw_map("test.png")
