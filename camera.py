"""Contains the Camera class."""
import random

import pygame

import constants
from misc import DynamicPos


class Camera:
    """The renderer camera.

    Can follow a point and shake.
    """

    def __init__(self, speed, rect_size):
        self._ppt = round(constants.MENU_SCALE*1.5)*20
        self._shake = 0
        self._shake_x = 0
        self._shake_y = 0
        self._pos = DynamicPos((0, 0), speed=speed)
        self._rect_size = rect_size

        self._t_lastshake = 0

    def get_rect(self):
        """Return the rect in which the camera can see.

        Rect position and size is in pixels.
        """
        x = (self._pos.x + random.uniform(-self._shake_x, self._shake_x)) * self._ppt / constants.TILE_SIZE
        y = (self._pos.y + random.uniform(-self._shake_y, self._shake_y)) * self._ppt / constants.TILE_SIZE
        rect = pygame.Rect((0, 0), self._rect_size)
        rect.center = (x, y)
        return rect

    def get_scale(self):
        """Return scale of camera. Larger number means more zoomed in."""
        return self._ppt / constants.TILE_SIZE

    def get_zoom(self):
        """Get pixels per tile of camera. Larger number means larger tiles."""
        return self._ppt

    def zoom(self, zoom):
        """Change the pixels per tile of the camera. Positive zoom means zooming in."""
        self._ppt += zoom

    def shake(self, amount):
        """Shake the camera."""
        self._shake += amount

    def set_target(self, pos, direct=False):
        """Set target position of the camera."""
        self._pos.move(pos, direct)

    def tile_to_pixel_pos(self, x, y):
        """Including zoom, return the position of the center of a tile relative to the top-left of the map."""
        return ((x+0.5)*self._ppt, (y+0.5)*self._ppt)

    def tile_to_camera_pos(self, x, y):
        """Excluding zoom, return the position of the center of a tile relative to the top-left of the map."""
        return ((x+0.5)*constants.TILE_SIZE, (y+0.5)*constants.TILE_SIZE)

    def tile_to_screen_pos(self, x, y):
        """Return the position of the center of a tile relative to the top-left of the screen."""
        pixelpos = self.tile_to_pixel_pos(x, y)
        rect = self.get_rect()
        return (pixelpos[0] - rect.x, pixelpos[1] - rect.y)

    def update(self, t_frame, pos=None):
        """Update shake amount and move towards target position."""
        if pos is not None:
            self.set_target(pos)

        self._pos.update(t_frame)

        self._t_lastshake += t_frame
        while self._t_lastshake >= 1000/30:
            self._t_lastshake -= 1000/30
            self._shake_x = random.uniform(-self._shake, self._shake)
            self._shake_y = random.uniform(-self._shake, self._shake)

            self._shake *= 0.75
            if self._shake < 0.1:
                self._shake = 0
