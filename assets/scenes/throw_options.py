"""Contains the ThrowOptions scene."""

import pygame

import components as c
import constants
import systems as s
import widget as wgt
from misc import DynamicPos

from . import inventory_options
from .scene import Scene


class ThrowOptions(Scene):
    """Throw direction selector once an item has been chosen to throw."""
    scene_properties = {
        **Scene.scene_properties,
        "draw_above_parent": False
    }
    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.camera = self.parent.parent.camera
        self.world = self.parent.parent.world
        self.item = item
        self.dir = (0, 0)
        self.targettile = None
        self.droptile = None

        self.help_pos = DynamicPos((constants.WIDTH//2, constants.HEIGHT+constants.MENU_SCALE*2.5), speed=10)
        self.help_pos.move((self.help_pos.x, constants.HEIGHT/2+constants.TILE_SIZE*constants.MENU_SCALE))

        text_args = {
            "renderer":self.game.renderer,
            "size":5*constants.MENU_SCALE,
            "centered":True
        }

        self.help_text = (
            wgt.Text(
                **text_args,
                text="Pick a direction",
                offset=(0, 0),
                color=constants.LIGHT_GRAY
            ),
            wgt.TextLines(
                **text_args,
                text=["Z to throw", "X to cancel"],
                offset=(0, 7*constants.MENU_SCALE)
            )
        )

    def get_input(self, keypress):
        handled = False
        if keypress == pygame.K_x:
            self.game.set_focus(self.parent.add_child_scene(inventory_options.InventoryOptions, self.item))
            self.remove_scene()
            handled = True

        if keypress in constants.DIRECTIONS:
            self.dir = keypress
            playerpos = self.world.entity_component(
                self.world.tags.player, c.TilePosition)
            self.targettile = [playerpos.x, playerpos.y]
            stopped = False
            distance = 0
            while not stopped:
                self.targettile[0] += self.dir[0]
                self.targettile[1] += self.dir[1]
                distance += 1
                if not self.world.get_system(s.GridSystem).on_grid(self.targettile):
                    self.targettile[0] -= self.dir[0]
                    self.targettile[1] -= self.dir[1]
                    distance -= 1
                    stopped = True
                if self.world.get_system(s.GridSystem).get_blocker_at(self.targettile) != 0:
                    distance -= 1
                    stopped = True
                if distance == 5:
                    stopped = True

            self.droptile = [playerpos.x + self.dir[0] * distance, playerpos.y + self.dir[1] * distance]

            handled = True

        if keypress == pygame.K_z:
            if self.droptile is not None:
                self.world.entity_component(self.world.tags.player, c.Inventory).contents.remove(self.item)
                self.world.remove_component(self.item, c.Stored)
                self.world.add_component(self.item, c.TilePosition(*self.droptile))
            if self.targettile is not None:
                target = self.world.get_system(s.GridSystem).get_blocker_at(self.targettile)
                if target:
                    if self.world.has_component(self.item, c.UseEffect):
                        use = self.world.entity_component(self.item, c.UseEffect)
                        for effect in use.effects:
                            getattr(self.game, effect[0])(target, *effect[1:])
                    if self.world.entity_component(self.item, c.Item).consumable:
                        self.world.add_component(self.item, c.Dead())
                self.remove_scene()

            handled = True

        return handled

    def update(self, delta):
        self.help_pos.update(delta)

    def draw(self, screen):
        item_x = constants.WIDTH//2+self.dir[0]*self.camera.get_zoom()/2
        item_y = constants.HEIGHT//2+self.dir[1]*self.camera.get_zoom()/2
        self.parent.parent.draw_centered_entity(screen, self.item, self.camera.get_scale(), (item_x, item_y))
        if self.targettile is not None:
            crosshair = self.game.renderer.get_image(name="crosshair", scale=self.camera.get_scale())
            self.game.renderer.draw_centered_image(screen, crosshair, self.camera.tile_to_screen_pos(*self.targettile))

        for text in self.help_text:
            text.draw(screen, (self.help_pos.x, self.help_pos.y))
