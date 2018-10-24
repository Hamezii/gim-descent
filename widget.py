"""Contains all the Widget classes."""

import random

import pygame

import constants


class Widget:
    """A UI element which can be reused in the UI."""
    def __init__(self, renderer, offset=(0, 0)):
        self.renderer = renderer
        self.offset = offset

        self.dirty_attributes = []
        self._surface_attributes = None

        #self.redraws = 0 # Used for debugging

        self._draw_surface = None

    def _update_surface(self):
        """Update the draw surface."""
        pass

    def update(self, delta):
        """Update the widget every frame."""
        pass

    def _is_dirty(self):
        """Return True if the surface requires updating."""
        current_attributes = {attr: getattr(self, attr) for attr in self.dirty_attributes}

        if self._surface_attributes is None:
            self._surface_attributes = current_attributes
            return True

        if current_attributes == self._surface_attributes:
            return False

        self._surface_attributes = current_attributes
        return True

    def draw(self, surface, pos=(0, 0)):
        """Draw the widget to a surface."""
        if self._is_dirty():
            #self.redraws += 1
            #print(self.redraws)
            self._update_surface()


        surface.blit(self._draw_surface, [pos[i]+self.offset[i] for i in range(2)])

class MainMenuTitle(Widget):
    """The game title."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._draw_surface = self.renderer.get_image(name="title", scale=constants.MENU_SCALE/2)
        c_x, c_y = self._draw_surface.get_rect().center

        self.offset = [constants.WIDTH//2-c_x, -c_y*2]
        self.y_goal = constants.HEIGHT/2 - 150*constants.MENU_SCALE
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

    def draw(self, surface, pos=(0, 0)):
        super().draw(surface, (self.shake_x, self.shake_y))

class ImageGrid(Widget):
    """An image."""
    def __init__(self, image=None, grid_size=None, **kwargs):
        super().__init__(**kwargs)

        self._image = image
        self._grid_size = grid_size

    def _update_surface(self):
        image_rect = self._image.get_rect()
        surface_width = image_rect.width * self._grid_size[0]
        surface_height = image_rect.height * self._grid_size[1]
        self._draw_surface = pygame.Surface((surface_width, surface_height))
        for x in range(self._grid_size[0]):
            for y in range(self._grid_size[1]):
                self._draw_surface.blit(self._image, (image_rect.width*x, image_rect.height*y))


class Text(Widget):
    """A line of text."""
    def __init__(self, size=None, color=constants.WHITE, text="", centered=False, **kwargs):
        super().__init__(**kwargs)

        self.size = size
        self.color = color
        self.centered = centered
        self.text = text

        self.dirty_attributes = ("size", "color", "centered", "text")

    def _update_surface(self):
        if self.centered and self._draw_surface is not None:
            center = self._draw_surface.get_rect().center
            self.offset = tuple(self.offset[i]+center[i] for i in range(2))

        self._draw_surface = self.renderer.make_text(self.color, self.text, self.size)

        if self.centered:
            center = self._draw_surface.get_rect().center
            for i in range(2):
                self.offset = tuple(self.offset[i]-center[i]*0.5 for i in range(2))

class TextLines(Widget):
    """Multiple lines of text"""
    def __init__(self, size=None, v_spacing=1.4, color=constants.WHITE, text=None, centered=False, **kwargs):
        super().__init__(**kwargs)

        if text is None:
            text = []

        self.size = size
        self.v_spacing = v_spacing
        self.color = color
        self.centered = centered
        self.text = text
        self.lines = []

        self.dirty_attributes = ("size", "color", "centered", "text")

    def _update_surface(self):
        if len(self.text) > len(self.lines):
            for i in range(len(self.text) - len(self.lines)):
                self.lines.append(Text(renderer=self.renderer))

        for i in range(len(self.text)):
            self.lines[i].text = self.text[i]
            self.lines[i].size = self.size
            self.lines[i].color = self.color
            self.lines[i].centered = self.centered

    def draw(self, surface, pos=(0, 0)):
        if self._is_dirty():
            self._update_surface()
        for i in range(len(self.text)):
            self.lines[i].draw(surface, (self.offset[0] + pos[0], self.offset[1] + pos[1] + self.size*self.v_spacing*i))
