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
        """Return a list of all the nodes."""
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

def __get_path_direction(x, distance):
    """Return the direction a path should travel. Return None if not possible."""
    min_x = -1
    max_x = 5
    can_go_left = True
    can_go_right = True
    if x - distance < min_x:
        can_go_left = False
    if x + distance > max_x:
        can_go_right = False
    if can_go_left and can_go_right:
        return random.choice([constants.LEFT, constants.RIGHT])
    elif can_go_right:
        return constants.RIGHT
    elif can_go_left:
        return constants.LEFT
    else:
        return None

def __make_node_and_connect_from(network, x, y, direction):
    """Add a Node(x, y) to a network and connect it from a direction."""
    node = LevelNode((x, y))
    network.add_node(node)
    network.connect(node, network.opposite[direction])

def __generate_main_path(network):
    """Make the random path connecting the start to the end of the dungeon."""
    x = 0
    y = 0
    path_height = 5
    path_length = 7
    for height in range(path_height-1, -1, -1):
        distance = random.randint(path_length//(1+height), path_length//(1+height*0.5))
        direction = __get_path_direction(x, distance)
        attempts = 0
        while direction is None:
            attempts += 1
            distance = random.randint(max(0, path_length//(1+height) - attempts), distance-1)
            direction = __get_path_direction(x, distance)
        path_length -= distance

        for _ in range(distance):
            x += direction[0]
            __make_node_and_connect_from(network, x, y, direction)

        y += 1
        __make_node_and_connect_from(network, x, y, constants.DOWN)
    network.get_node_at((x, y)).properties.append("boss")

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
            if network.get_node_at(pos) is None and -1 <= pos[0] <= 4 and 0 <= pos[1] <= 5:
                network.add_node(LevelNode(pos))
                network.connect(node, direction)

def __add_random_connections(network, chance):
    """Add random connections, which chance being the chance per connection."""
    for node in network.get_nodes():
        for direction in (constants.LEFT, constants.DOWN): # So node chances aren't repeated
            if random.random() < chance:
                network.connect(node, direction)

def __add_elemental_effect(node, element_type):
    """Add the given type of effect to the the node's properties.

    Don't add the effect if the node is the starting level.
    """
    if not "start" in node.properties and not "boss" in node.properties:
        node.properties.append(element_type)

def generate_dungeon_layout():
    """Return a DungeonNetwork object containing the layout of the dungeon."""
    network = DungeonNetwork()
    node = LevelNode((0, 0), properties=["start"])
    network.add_node(node)
    network.player_node = node

    __generate_main_path(network)
    __add_random_rooms(network, 3, 5)
    __add_random_connections(network, 0.15)
    # Add random fire sections
    for node in random.choices(network.get_nodes(), k=2):
        __add_elemental_effect(node, "fire")
        for _, connected_node in node.connections.items():
            if connected_node is not None:
                __add_elemental_effect(connected_node, "fire")

    return network
