"""Contains the ImageGrid scene."""

import pygame

import constants

from .scene import Scene


class ImageGrid(Scene):
    """A grid of an image, with a black border."""
    scene_properties = {
        **Scene.scene_properties,
        "draw_above_parent": False
    }
    def __init__(self, image=None, grid_size=None, pos=None, **kwargs):
        super().__init__(**kwargs)

        self.__image = image
        self.__image_size = self.__image.get_rect().size
        self.__grid_size = grid_size
        self.pos = pos

        image_rect = self.__image.get_rect()
        surface_width = image_rect.width * self.__grid_size[0]
        surface_height = image_rect.height * self.__grid_size[1]
        self.surface = pygame.Surface((surface_width, surface_height))
        for x in range(self.__grid_size[0]):
            for y in range(self.__grid_size[1]):
                self.surface.blit(self.__image, (image_rect.width*x, image_rect.height*y))

    def draw(self, screen):
        x = round(self.pos[0])
        y = round(self.pos[1])

        # Black border
        black_box_pos = (x-5*constants.MENU_SCALE, y-5*constants.MENU_SCALE)
        black_box_size = tuple(self.__image_size[i] * self.__grid_size[i] +10*constants.MENU_SCALE for i in range(2))
        pygame.draw.rect(screen, constants.BLACK, (black_box_pos, black_box_size))

        # Image grid
        screen.blit(self.surface, (x, y))
