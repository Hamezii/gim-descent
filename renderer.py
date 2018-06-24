'''
Contains the Renderer of Gim Descent.
'''

import pygame

import constants

# CONSTANTS

class Renderer:
    """Rendering wrapper which stores cached surfaces."""
    BLINK_RATE = 250
    SPECIAL_CHARS = {":": "col", "-": "dash", ".": "dot",
                     "!": "exc", "/": "fwdslash", "?": "que", " ": "space"}

    def __init__(self):
        self.camera = None
        self._imported_images = {}
        self.images = {}
        self.total_images = 0

        self.t_elapsed = 0

    def get_image(self, **args):
        """Get an image surface from the cache. If it does not exist, the image is created.

        Optional modifier parameters like scale and color can be used.
        """
        if "scale" not in args:
            args["scale"] = 1

        if "blinking" in args:
            if args["blinking"] and self.t_elapsed % self.BLINK_RATE < self.BLINK_RATE/2:
                args["blinking"] = True
            else:
                del args["blinking"]

        key = str(args)

        if key not in self.images:
            self.total_images += 1
            self.images[key] = self._import_image(args["name"])
            if "scale" in args:
                self.images[key] = pygame.transform.scale(self.images[key], (int(
                    self.images[key].get_width()*args["scale"]), int(self.images[key].get_height()*args["scale"])))

            if "color" in args:
                self.images[key].fill(args["color"][0:3], special_flags=args["color"][3])

            if "blinking" in args:
                if args["blinking"]:
                    self.images[key].fill((50, 50, 50), special_flags=pygame.BLEND_ADD)



        return self.images[key]

    def _import_image(self, name):
        if not name in self._imported_images:
            try:
                image = pygame.image.load(constants.IMAGES+name+".png").convert_alpha()
            except pygame.error:
                image = pygame.image.load(constants.DEFAULT_IMAGES+name+".png").convert_alpha()
            self._imported_images[name] = image

        return self._imported_images[name].copy()

    def draw_text(self, surface, color, pos, text, size, centered=False):
        """Draw text to a surface.

        size refers to the height and width of each character in pixels.
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

    def draw_image(self, surface, image, pos):
        """Blit an image to a surface."""
        surface.blit(image, pos)

    def draw_centered_image(self, surface, image, centerpos):
        """Blit an image to a surface, centering it at centerpos."""
        surface.blit(
            image, (centerpos[0] - image.get_width()//2, centerpos[1] - image.get_height()//2))
