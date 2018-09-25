'''
Contains the Renderer of Gim Descent.
'''
import random
from functools import lru_cache

import pygame

import constants


@lru_cache(maxsize=None)
def _import_image(name):
    try:
        image = pygame.image.load(constants.IMAGES+name+".png").convert_alpha()
    except pygame.error:
        image = pygame.image.load(constants.DEFAULT_IMAGES+name+".png").convert_alpha()
    return image


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


class Camera:
    """The renderer camera.

    Can follow a point and shake.
    """

    def __init__(self, speed):
        self._ppt = round(constants.MENU_SCALE*1.5)*20
        self._shake = 0
        self._shake_x = 0
        self._shake_y = 0
        self._pos = DynamicPos((0, 0), speed=speed)

        self._t_lastshake = 0
        self.start = True

    def get_rect(self):
        """Return the rect in which the camera can see.

        Rect position and size is in pixels.
        """
        x = (self._pos.x + random.uniform(-self._shake_x, self._shake_x)) * self._ppt / constants.TILE_SIZE
        y = (self._pos.y + random.uniform(-self._shake_y, self._shake_y)) * self._ppt / constants.TILE_SIZE
        rect = pygame.Rect(0, 0, constants.WIDTH, constants.HEIGHT)
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

    def set(self, pos, direct=False):
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
            if self.start:
                self.start = False
                self.set(pos, direct=True)
            else:
                self.set(pos)

        self._pos.update(t_frame)

        self._t_lastshake += t_frame
        while self._t_lastshake >= 1000/30:
            self._t_lastshake -= 1000/30
            self._shake_x = random.uniform(-self._shake, self._shake)
            self._shake_y = random.uniform(-self._shake, self._shake)

            self._shake *= 0.75
            if self._shake < 0.1:
                self._shake = 0


class Renderer:
    """Rendering wrapper which stores cached surfaces."""
    BLINK_RATE = 250
    SPECIAL_CHARS = {":": "col", "-": "dash", ".": "dot",
                     "!": "exc", "/": "fwdslash", "?": "que", " ": "space"}

    def __init__(self):
        self.camera = Camera(speed=5)
        self.total_images = 0

        self.t_elapsed = 0

    def is_blinking(self):
        """Return True if blinking images should be lit up at the moment."""
        if self.t_elapsed % self.BLINK_RATE < self.BLINK_RATE/2:
            return True
        return False


    @lru_cache(maxsize=None)
    def get_image(self, **args):
        """Get an image. Optional modifier parameters like scale and color can be used.

        Function is cached with lru_cache.
        """
        if "scale" not in args:
            args["scale"] = 1

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
                char_name = "txt-"+character.lower()
            surface.blit(self.get_image(name=char_name, scale=size*0.2, color=color), (pos[0] + i * character_width, pos[1]))

    def make_text(self, color, text, size):
        """Return a surface containing text."""
        surface = pygame.Surface(self.text_rect(text, size).size)
        surface.set_colorkey(constants.COLOR_KEY)
        surface.fill(constants.COLOR_KEY)
        self.draw_text(surface, color, (0, 0), text, size)
        return surface

    def text_rect(self, text, size, pos=(0, 0)):
        """Return the rect that text would occupy if drawn."""
        rect = pygame.Rect(pos, (size * (len(text) * 0.8 - 0.2), size))
        return rect

    def draw_image(self, surface, image, pos):
        """Blit an image to a surface."""
        surface.blit(image, pos)

    def draw_centered_image(self, surface, image, centerpos):
        """Blit an image to a surface, centering it at centerpos."""
        surface.blit(image, (centerpos[0] - image.get_width()//2, centerpos[1] - image.get_height()//2))

    @lru_cache(maxsize=None)
    def _icon_image(self, icons, scale):
        """Return an icons surface."""
        images = []

        for i, icon in enumerate(icons):
            image_name = icon[0]
            images.append(self.get_image(name=image_name, scale=scale))

        tile_size = scale * constants.TILE_SIZE
        rects = []
        text_rects = []
        for i, image in enumerate(images):
            pos = (tile_size*(i*0.2), 0)
            rects.append(image.get_rect(center=pos))

            if icons[i][1]:
                text_pos = (pos[0], pos[1]-tile_size*0.3)
                text_rect = self.text_rect(str(icons[i][1]), scale*10)
                text_rect.center = text_pos
                text_rects.append(text_rect)
            else:
                text_rects.append(pygame.Rect(0, 0, 0, 0))

        surface_rect = pygame.Rect(0, 0, 0, 0).unionall(rects)
        surface_rect.unionall_ip(text_rects)
        x, y = surface_rect.topleft

        surface = pygame.Surface(surface_rect.size)
        surface.set_colorkey(constants.COLOR_KEY)
        surface.fill(constants.COLOR_KEY)

        for i, image in enumerate(images):
            rects[i].move_ip(-x, -y)
            #pygame.draw.rect(surface, constants.BLACK, rects[i])
            surface.blit(image, rects[i])

            if icons[i][1]:
                text_rects[i].move_ip(-x, -y)
                #pygame.draw.rect(surface, constants.BLACK, text_rects[i])
                self.draw_text(surface, constants.WHITE, text_rects[i], str(icons[i][1]), 10 * scale)

        return surface

    @lru_cache(maxsize=None)
    def entity_image(self, scale, **draw_data):
        """Return an entity surface given draw data."""
        images = []
        rects = []

        # Entity image
        images.append(self.get_image(scale=scale, **draw_data))
        rects.append(images[0].get_rect())
        center = rects[0].center

        tile_size = scale * constants.TILE_SIZE

        # Icon images
        if draw_data["icons"]:
            images.append(self._icon_image(draw_data["icons"], scale))
            rects.append(images[-1].get_rect(left=center[0]-tile_size*0.4, bottom=center[1]+0.4*tile_size))

        # Frozen ice cube
        if draw_data["frozen"]:
            images.append(self.get_image(name="ice-cube", scale=scale))
            rects.append(images[-1].get_rect(center=center))

        surface_rect = pygame.Rect(center, (0, 0)).unionall(rects)

        surface = pygame.Surface(surface_rect.size, pygame.SRCALPHA)

        x, y = surface_rect.topleft
        for i, image in enumerate(images):
            surface.blit(image, rects[i].move(-x, -y))

        return surface
