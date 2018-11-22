"""Contains the MainMenuTitle scene."""

import random

import constants

from .scene import Scene


class MainMenuTitle(Scene):
    """The game title text.

    It falls down then shakes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.surface = self.game.renderer.get_image(name="title", scale=constants.MENU_SCALE/2)
        center_x, center_y = self.surface.get_rect().center

        self.offset = [self.game.width//2-center_x, -center_y*2]
        self.y_goal = self.game.height/2 - 150*constants.MENU_SCALE
        self.speed = 0
        self.shake_x = 0
        self.shake_y = 0
        self.shake = 0
        self.lastshake = 1000/60

    def update(self, delta):
        if self.offset[1] < self.y_goal:
            self.speed += delta*0.001
            self.offset[1] = min(self.offset[1]+self.speed*delta, self.y_goal)
            if self.offset[1] == self.y_goal:
                self.shake = 15*constants.MENU_SCALE
        else:
            if self.shake > 0:
                self.lastshake += delta
                while self.lastshake > 1000/60:
                    self.lastshake -= 1000/60
                    self.shake_x = random.uniform(-self.shake, self.shake)
                    self.shake_y = random.uniform(-self.shake, self.shake)
                    self.shake *= 0.9
                    if self.shake < 1:
                        self.shake = 0

    def draw(self, screen):
        screen.blit(self.surface, (self.offset[0] + self.shake_x, self.offset[1] + self.shake_y))
