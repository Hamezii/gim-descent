"""Contains functions for generating dungeon layout."""

from dataclasses import dataclass

@dataclass
class LevelNode:
    """A node representing a level than the player can go to."""
    level_type: str = "normal"


class DungeonNetwork:
    """Contains all the nodes which represent the layout of the dungeon."""
    def __init__(self):
        self.__nodes = {}

    def set_node_at(self, pos, node):
        """Put a node at a certain position in the network."""
        self.__nodes[tuple(pos)] = node

    def get_node_at(self, pos):
        """Get a node from a certain position in the network, or None if there is not one there."""
        try:
            return self.__nodes[tuple(pos)]
        except KeyError:
            return None

    def get_nodes(self):
        """Return all the nodes in the network in position-node pairs."""
        return self.__nodes.items()

def generate_dungeon_layout():
    """Return a DungeonNetwork object containing the layout of the dungeon."""
    network = DungeonNetwork()
    for y in range(11):
        network.set_node_at((0, y), LevelNode(level_type="normal"))
    network.set_node_at((0, 11), LevelNode(level_type="boss"))
    return network
