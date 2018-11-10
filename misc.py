"""Contains miscellaneous classes and functions which are used by multiple modules."""

import sys

import pygame


def leave():
    """Close the game."""
    pygame.quit()
    sys.exit(0)

def time_to_str(seconds):
    """Return a time string given a time in seconds."""
    time_s = str(int(seconds % 60))
    if len(time_s) == 1:
        time_s = "0" + time_s
    time_m = str(int(seconds // 60))
    return time_m + ":" + time_s

def pluralise(value, singular, plural=None):
    """Return the singular or plural of a word depending on whether the value is non-one.

    If plural is None (default), add an 's' to the end of the word instead.
    """
    if value == 1:
        word = singular
    elif plural is None:
        word = singular + "s"
    else:
        word = plural
    return str(value) + " " + word

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

    def __str__(self):
        keys = ("current", "goal", "speed")
        string = "DynamicPos("
        for key in keys:
            string += key+"="+str(getattr(self, key))+" "
        string += ")"
        return string

    def __getitem__(self, index):
        return self.current[index]
