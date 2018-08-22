'''
Contains the Renderer of Gim Descent.
'''
from functools import lru_cache

import pygame

import constants

# CONSTANTS

@lru_cache(maxsize=None)
def _import_image(name):
    try:
        image = pygame.image.load(constants.IMAGES+name+".png").convert_alpha()
    except pygame.error:
        image = pygame.image.load(constants.DEFAULT_IMAGES+name+".png").convert_alpha()
    return image


class Renderer:
    """Rendering wrapper which stores cached surfaces."""
    BLINK_RATE = 250
    SPECIAL_CHARS = {":": "col", "-": "dash", ".": "dot",
                     "!": "exc", "/": "fwdslash", "?": "que", " ": "space"}

    def __init__(self):
        self.camera = None
        self.total_images = 0

        self.t_elapsed = 0

    @lru_cache(maxsize=None)
    def get_image(self, **args):
        """Get an image. Optional modifier parameters like scale and color can be used.

        Function is cached with lru_cache.
        """
        if "scale" not in args:
            args["scale"] = 1

        if "blinking" in args:
            if args["blinking"] and self.t_elapsed % self.BLINK_RATE < self.BLINK_RATE/2:
                args["blinking"] = True
            else:
                del args["blinking"]

        self.total_images += 1
        image = _import_image(args["name"]).copy()
        if "scale" in args:
            image = pygame.transform.scale(image, (int(image.get_width()*args["scale"]), int(image.get_height()*args["scale"])))

        if "color" in args:
            image.fill(args["color"][0:3], special_flags=args["color"][3])

        if "blinking" in args:
            if args["blinking"]:
                image.fill((50, 50, 50), special_flags=pygame.BLEND_ADD)

        return image

    def draw_text(self, surface, color, pos, text, size, centered=False):
        """Draw text to a surface.

        size refers to the height of each character in pixels.
        """
        color = (color[0], color[1], color[2], pygame.BLEND_ADD)
        character_width = size * 0.8

        if centered:
            pos = (pos[0] - (len(text)/2) * character_width + 0.1 * size, pos[1] - size * 0.5)

        for i, character in enumerate(text):
            if character in self.SPECIAL_CHARS:
                char_name = "txt_"+self.SPECIAL_CHARS[character]
            else:
                char_name = "txt-"+character
            surface.blit(self.get_image(name=char_name, scale=size*0.2, color=color), (pos[0] + i * character_width, pos[1]))

    def make_text(self, color, text, size):
        """Return a surface containing text."""
        surface_height = size
        surface_width = size * (len(text) * 0.8 - 0.2)
        surface = pygame.Surface((surface_width, surface_height))
        surface.set_colorkey(constants.COLOR_KEY)
        surface.fill(constants.COLOR_KEY)
        self.draw_text(surface, color, (0, 0), text, size)
        return surface

    def draw_image(self, surface, image, pos):
        """Blit an image to a surface."""
        surface.blit(image, pos)

    def draw_centered_image(self, surface, image, centerpos):
        """Blit an image to a surface, centering it at centerpos."""
        surface.blit(image, (centerpos[0] - image.get_width()//2, centerpos[1] - image.get_height()//2))