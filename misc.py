"""Contains miscellaneous classes and functions which are used throughout the code."""

import sys

import pygame


def leave():
    """Close the game."""
    pygame.quit()
    sys.exit(0)


class DynamicPos:
    """A vector value which linearly interpolates to a position.

    Specifically for the camera in this module.
    """

    def __init__(self, pos, speed):
        self.current = pos
        self.goal = pos
        self.speed = speed

    def move(self, pos, instant=False):
        """Set a target position. Instant moves it there instantly."""
        self.goal = pos
        if instant:
            self.current = pos

    def update(self, delta):
        """Linearly interpolate to target position."""
        x = (self.goal[0] - self.current[0])*min(1, delta*self.speed*0.001)
        y = (self.goal[1] - self.current[1])*min(1, delta*self.speed*0.001)
        self.current = (self.current[0]+x, self.current[1] + y)

    @property
    def x(self):
        """Get x value of vector."""
        return self.current[0]

    @property
    def y(self):
        """Get y value of vector."""
        return self.current[1]
