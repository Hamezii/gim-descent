"""Contains the Viewport scene."""

import pygame

import components as c
import constants
from systems import GridSystem

from .scene import Scene


class Viewport(Scene):
    """The main dungeon view. Draws what the player can see of the dungeon."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._floor_cache = None
        self._zoom_cache = 0

    def draw(self, screen):
        camerarect = self.parent.camera.get_rect()
        camerazoom = self.parent.camera.get_zoom()
        camerascale = camerazoom/constants.TILE_SIZE

        if self._zoom_cache != camerazoom:
            self._zoom_cache = camerazoom

            gridwidth = self.parent.world.get_system(GridSystem).gridwidth
            gridheight = self.parent.world.get_system(GridSystem).gridheight

            self._floor_cache = pygame.surface.Surface((gridwidth*camerazoom, gridheight*camerazoom))
            floor_image = self.game.renderer.get_image(name="floor", scale=camerascale)
            for x in range(0, gridwidth):
                for y in range(0, gridheight):
                    self._floor_cache.blit(floor_image, (x*camerazoom, y*camerazoom))

        screen.blit(self._floor_cache, (0, 0), (camerarect.x, camerarect.y, camerarect.width, camerarect.height))

        for entity, comps in self.parent.world.get_components(c.Render, c.TilePosition):
            pos = comps[1]

            pixelpos = self.parent.camera.tile_to_pixel_pos(pos.x, pos.y)
            rect = pygame.Rect(0, 0, camerazoom*1.5, camerazoom*1.5)
            rect.center = pixelpos

            drawing = rect.colliderect(camerarect)

            if drawing:
                pixelpos = (pixelpos[0] - camerarect.x, pixelpos[1] - camerarect.y)
                self.parent.draw_centered_entity(screen, entity, camerascale, pixelpos)

                if self.parent.world.has_component(entity, c.Health):    # Healthbar
                    health = self.parent.world.entity_component(entity, c.Health)
                    barpos = (pixelpos[0] - camerazoom*0.35, pixelpos[1] + camerazoom*0.4)
                    barsize = camerazoom*0.7, camerazoom*0.05
                    barrect = pygame.Rect(barpos, barsize)
                    pygame.draw.rect(screen, constants.ALMOST_BLACK, barrect.inflate(camerazoom*0.1, camerazoom*0.1))
                    if health.current > 0:
                        health_width = barrect.width*(health.current / health.max)
                        pygame.draw.rect(screen, self.parent.get_health_bar_color(health), (barpos, (health_width, barrect.height)))
