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
    level_type: str = "normal"
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


def generate_dungeon_layout():
    """Return a DungeonNetwork object containing the layout of the dungeon."""
    network = DungeonNetwork()
    for y in range(6):
        node = LevelNode((0, y), level_type="normal")
        network.add_node(node)
        network.connect(node, constants.UP)
        if random.random() < 0.5:
            for x in range(1, random.randint(1, 4)):
                node = LevelNode((x, y), level_type="normal")
                network.add_node(node)
                network.connect(node, constants.LEFT)

    node = LevelNode((0, 6), level_type="boss")
    network.add_node(node)
    network.connect(node, constants.UP)

    network.player_node = network.get_node_at((0, 0))

    return network
