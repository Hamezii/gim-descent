"""Contains classes and methods relating to key input."""

from enum import Enum, auto

import pygame

import constants


class Keypress:
    """Represents a keypress. Can correspond to multiple actions."""
    def __init__(self, key):
        self.key = key
        self.actions = KEY_ACTIONS.get(key, [])

    def has_action(self, action):
        """Return True if this corresponds to an Action."""
        return action in self.actions

    def get_direction(self):
        """Return the direction of a directional Keypress as a 2d tuple."""
        if self.actions[0] in ACTION_DIRECTIONS:
            return ACTION_DIRECTIONS[self.actions[0]]
        raise KeyError("Can't get direction of non-directional Keypress %s" % self.key)


class Action(Enum):
    """An enum which represents an input action."""
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    DIRECTION = auto()
    ACCEPT = auto()
    BACK = auto()
    INVENTORY_OPEN = auto()
    INVENTORY_CLOSE = auto()
    ZOOM_OUT = auto()
    ZOOM_IN = auto()

ACTION_DIRECTIONS = {
    Action.UP: constants.UP,
    Action.DOWN: constants.DOWN,
    Action.LEFT: constants.LEFT,
    Action.RIGHT: constants.RIGHT
    }

KEY_ACTIONS = {
    pygame.K_z: [Action.ACCEPT, Action.INVENTORY_OPEN],
    pygame.K_RETURN: [Action.ACCEPT, Action.INVENTORY_OPEN],
    pygame.K_SPACE: [Action.ACCEPT, Action.INVENTORY_OPEN],
    pygame.K_x: [Action.BACK],
    pygame.K_ESCAPE: [Action.BACK],
    pygame.K_TAB: [Action.INVENTORY_OPEN, Action.INVENTORY_CLOSE],

    pygame.K_MINUS: [Action.ZOOM_OUT],
    pygame.K_EQUALS: [Action.ZOOM_IN],

    # For directional keys, the direction must be first
    pygame.K_w: [Action.UP, Action.DIRECTION],
    pygame.K_s: [Action.DOWN, Action.DIRECTION],
    pygame.K_a: [Action.LEFT, Action.DIRECTION],
    pygame.K_d: [Action.RIGHT, Action.DIRECTION],
    pygame.K_UP: [Action.UP, Action.DIRECTION],
    pygame.K_DOWN: [Action.DOWN, Action.DIRECTION],
    pygame.K_LEFT: [Action.LEFT, Action.DIRECTION],
    pygame.K_RIGHT: [Action.RIGHT, Action.DIRECTION]
}

"""
Just in case I need these, they are outdated though
KEYS_UP = (pygame.K_w, pygame.K_UP)
KEYS_LEFT = (pygame.K_a, pygame.K_LEFT)
KEYS_DOWN = (pygame.K_s, pygame.K_DOWN)
KEYS_RIGHT = (pygame.K_d, pygame.K_RIGHT)
KEYS_ACCEPT = (pygame.K_RETURN, pygame.K_SPACE, pygame.K_z)
KEYS_BACK = (pygame.K_ESCAPE, pygame.K_x)
KEYS_INVENTORY_OPEN = (pygame.K_TAB, pygame.K_z)
KEYS_INVENTORY_CLOSE = (pygame.K_TAB)
"""
