"""Contains all the Widget classes."""

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
    """Multiple lines of text."""
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


class LevelNode(Widget):
    """Represents a node in the dungeon."""
    OUTER_COLOR = constants.GRAY
    INNER_COLOR = constants.LIGHT_GRAY
    def __init__(self, level_node, **kwargs):
        super().__init__(**kwargs)

        self.level_node = level_node

        self.dirty_attributes = ("level_node",)

    def _update_surface(self):
        scale = constants.MENU_SCALE
        self._draw_surface = pygame.Surface((40*scale, 30*scale))
        self._draw_surface.fill(self.INNER_COLOR)
        outer_rect = (2*scale, 2*scale, (40-4)*scale, (30-4)*scale)
        pygame.draw.rect(self._draw_surface, self.OUTER_COLOR, outer_rect, 4*scale)
