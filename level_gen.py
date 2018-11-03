"""Contains functions for generating levels."""

import random

from pygame import Rect

import entity_templates
from components import FireElement, IceElement


class Level:
    """Contains data about a level which can be used to create it."""
    def __init__(self, player_start=None):
        self.player_start = player_start
        self.entities = []

class Grid:
    """A grid of cells which each contain a list of strings corresponding to entities."""
    def __init__(self, gridsize):
        self.gridsize = gridsize

        self.grid = []
        for x in range(0, self.width):  # Walls
            self.grid.append([])
            for _ in range(0, self.height):
                self.grid[x].append([])

    @property
    def width(self):
        """Return width of grid array."""
        return self.gridsize[0]

    @property
    def height(self):
        """Return height of grid array."""
        return self.gridsize[1]

    def __getitem__(self, x):
        """Return a column from the grid."""
        return self.grid[x]

    def __iter__(self):
        """Return an iterable which iterates through the grid."""
        for x in range(self.width):
            for y in range(self.height):
                yield (x, y, self.grid[x][y])

def __random_loot():
    """Return the name of a random peice of loot."""
    return random.choice(("health_potion", "speed_potion", "teleport_potion", "bomb"))

def __generate_spawn_pool(levelnum):
    """Return a list of creatures which can spawn on a level."""
    spawn_pool = [*["snake"]*10]
    if 1 <= levelnum <= 6:
        spawn_pool.extend(["ogre"]*4)

    if 1 <= levelnum <= 5:
        spawn_pool.extend(["slime_medium"]*2)
    else:
        spawn_pool.extend(["slime_large"]*2)

    if levelnum >= 7:
        spawn_pool.extend(["bomb_goblin"]*2)
    if levelnum >= 7:
        spawn_pool.extend(["caterkiller"]*3)
    if levelnum >= 9:
        spawn_pool.extend(["golem"]*1)
    return spawn_pool

def __random_empty_pos(grid):
    x = random.randrange(grid.width)
    y = random.randrange(grid.height)
    while grid[x][y]:
        x = random.randrange(grid.width)
        y = random.randrange(grid.height)
    return (x, y)

def __random_enemy_spawn(level, grid):
    x = random.randrange(grid.width)
    y = random.randrange(grid.height)
    while "wall" in grid[x][y] or "stairs" in grid[x][y] or (x, y) == level.player_start:
        x = random.randrange(grid.width)
        y = random.randrange(grid.height)
    return (x, y)

def __add_grid_to_level(level, grid, level_type=None):
    """Add a grid to the list of entities in a Level object."""
    for x, y, cell in grid:
        for entity_string in cell:
            entity = getattr(entity_templates, entity_string)(x, y)
            if entity_string == "wall":
                if random.randint(1, 3) == 1:
                    if level_type == "ice":
                        entity.append(IceElement())
                    if level_type == "fire":
                        entity.append(FireElement())
            level.entities.append(entity)

def __add_random_enemies_to_level(level, grid, levelnum, level_type=None):
    """Add enemies to a level, making sure to place them in valid positions."""
    spawn_pool = __generate_spawn_pool(levelnum)
    for _ in range(20 + 2*levelnum):
        x, y = __random_enemy_spawn(level, grid)
        entity = getattr(entity_templates, random.choice(spawn_pool))(x, y)
        if random.randint(1, 2) == 1:
            if level_type == "ice":
                entity.append(IceElement())
            if level_type == "fire":
                entity.append(FireElement())
        level.entities.append(entity)


def generate_fly_boss_level(gridsize):
    """Return a Level object for the fly boss level."""

    level = Level((2, 15))
    grid = Grid(gridsize)

    main_room = Rect(5, 5, 20, 20)

    for x, y, cell in grid:
        if not main_room.collidepoint(x, y):
            cell.append("wall")

    for x in range(1, 5):
        for y in range(14, 17):
            grid[x][y].remove("wall")

    for y in range(14, 17):
        grid[8][y].append("wall")

    grid[7][15].append("fly")
    grid[22][15].append("fly_wizard")

    __add_grid_to_level(level, grid)

    return level

def generate_random_level(gridsize, levelnum):
    """Return a randomly generated Level object."""

    level_type = "normal"
    if random.random() < 0.5 and levelnum > 1:
        level_type = random.choice(("ice", "fire"))

    grid = Grid(gridsize)

    for x, y, cell in grid:
        cell.append("wall")

    for roomx, roomy, _ in grid:
        roomheight = random.randint(2, 6)
        roomwidth = random.randint(2, 6)
        if roomx + roomwidth <= grid.width and roomy + roomheight <= grid.height and random.randint(1, 15) == 1:
            for x in range(0, roomwidth):
                for y in range(0, roomheight):
                    entities = grid[roomx+x][roomy+y]
                    if "wall" in entities:
                        entities.remove("wall")

    # Stairs down
    exit_x, exit_y = __random_empty_pos(grid)
    grid[exit_x][exit_y].append("stairs")

    # Loot
    loot_x = random.randint(0, grid.width-2)
    loot_y = random.randint(0, grid.height-2)
    while "wall" in grid[loot_x][loot_y]:
        loot_x = random.randint(0, grid.width-2)
        loot_y = random.randint(0, grid.height-2)
    for x in range(loot_x, loot_x + 2):
        for y in range(loot_y, loot_y + 2):
            if "wall" in grid[x][y]:
                grid[x][y].remove("wall")
            grid[x][y].append(__random_loot())

    for _ in range(random.randint(2, 5)):
        x, y = __random_empty_pos(grid)
        grid[x][y].append(__random_loot())

    # Making Level object
    player_start = __random_empty_pos(grid)
    level = Level(player_start)

    # Adding grid and enemies to level
    __add_grid_to_level(level, grid, level_type)

    __add_random_enemies_to_level(level, grid, levelnum, level_type)

    return level