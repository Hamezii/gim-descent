"""Contains functions for generating dungeon layout."""

import random
from dataclasses import dataclass, field

import constants


def default_connections():
    """Default empty configuration for node connections."""
    return {
        constants.UP: None,
        constants.DOWN: None,
        constants.RIGHT: None,
        constants.LEFT: None
    }


@dataclass
class LevelNode:
    """A node representing a level than the player can go to."""
    pos: tuple
    properties: list = field(default_factory=list)
    connections: dict = field(default_factory=default_connections, init=False)
    explored: bool = field(default=False, init=False)
    can_be_explored: bool = field(default=False, init=False, repr=False)


class DungeonNetwork:
    """Contains all the nodes which represent the layout of the dungeon."""
    opposite = {
        constants.UP: constants.DOWN,
        constants.DOWN: constants.UP,
        constants.RIGHT: constants.LEFT,
        constants.LEFT: constants.RIGHT
    }
    def __init__(self):
        self.__nodes = []
        self.player_node = None

    def add_node(self, node):
        """Add a node to the list of nodes in the network."""
        self.__nodes.append(node)

    def get_node_at(self, pos):
        """Get a node which is at a certain position, or None if there is not one there."""
        pos = tuple(pos)
        for node in self.__nodes:
            if node.pos == pos:
                return node
        return None

    def get_nodes(self):
        """Return all the nodes in the network in position-node pairs."""
        return self.__nodes

    def connect(self, node, direction):
        """Connect a node to whatever is in a direction.

        Don't do anything if there is nothing to connect to.
        """
        other_pos = (node.pos[i] + direction[i] for i in range(2))
        other_node = self.get_node_at(other_pos)
        if other_node is not None:
            node.connections[direction] = other_node
            other_node.connections[self.opposite[direction]] = node

def __generate_main_path(network):
    """Make the random path connecting the start to the end of the dungeon."""
    y = 0
    x = 0
    move = None
    while y < 6:
        direction = random.randint(-(y+1), y+1) # More winding near the bottom

        if direction < 0:
            if x <= -1 or move == constants.RIGHT:
                move = constants.DOWN
            else:
                move = constants.LEFT
        if direction > 0:
            if x >= 4 or move == constants.LEFT:
                move = constants.DOWN
            else:
                move = constants.RIGHT
        if direction == 0:
            move = constants.DOWN
        x += move[0]
        y += move[1]
        node = LevelNode((x, y))
        network.add_node(node)
        network.connect(node, network.opposite[move])

def __add_random_rooms(network, amount, depth):
    """Add random rooms coming off of the rooms already placed.

    amount is amount of attempted room additions to do on the current rooms.
    depth is the amount of times to repeat this process.
    High amount, low depth: lots of short extra paths.
    Low amount, high depth: fewer but longer extra paths.
    """
    for _ in range(depth):
        for node in random.choices(network.get_nodes(), k=amount):
            direction = random.choice(constants.DIRECTIONS)
            pos = tuple(node.pos[i]+direction[i] for i in range(2))
            if network.get_node_at(pos) is None and -1 <= pos[0] <= 4 and 0 <= pos[1] <= 6:
                network.add_node(LevelNode(pos))
                network.connect(node, direction)

def __add_random_connections(network, chance):
    """Add random connections, which chance being the chance per connection."""
    for node in network.get_nodes():
        for direction in (constants.LEFT, constants.DOWN): # So node chances aren't repeated
            if random.random() < chance:
                network.connect(node, direction)

def generate_dungeon_layout():
    """Return a DungeonNetwork object containing the layout of the dungeon."""
    network = DungeonNetwork()
    node = LevelNode((0, 0), properties=["start"])
    network.add_node(node)
    network.player_node = node

    __generate_main_path(network)
    __add_random_rooms(network, 3, 5)
    __add_random_connections(network, 0.15)
    # for y in range(1, 6):
    #     node = LevelNode((0, y))
    #     network.add_node(node)
    #     network.connect(node, constants.UP)
    #     if random.random() < 0.5:
    #         for x in range(1, random.randint(1, 4)):
    #             node = LevelNode((x, y))
    #             network.add_node(node)
    #             network.connect(node, constants.LEFT)

    # node = LevelNode((0, 6), properties=["boss"])
    # network.add_node(node)
    # network.connect(node, constants.UP)

    return network
