"""Contains the Inventory scene."""

import pygame

import audio
import components as c
import constants
import widget as wgt
from misc import DynamicPos

from .inventory_options import InventoryOptions
from .scene import Scene


class Inventory(Scene):
    """Main inventory menu."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.visible = False
        self.cursorpos = [0, 0]
        self.size = [2, 5]
        self.slot_size = constants.TILE_SIZE*constants.MENU_SCALE
        self.pos = DynamicPos((-self.slot_size*2-21, constants.HEIGHT/2-self.slot_size*3), speed=10)

        self.widgets = (
            wgt.TextLines(
                renderer=self.game.renderer, size=5*constants.MENU_SCALE, offset=(0, - 19*constants.MENU_SCALE),
                text=["Z to select", "X to return"]
            ),
            wgt.ImageGrid(
                renderer=self.game.renderer,
                grid_size=[2, 5],
                image=self.game.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE)
            ),
        )

    def get_input(self, keypress):
        handled = False
        if keypress == pygame.K_x:
            handled = True
            self.game.set_focus(self.parent)
            self.hide()

        if keypress in constants.DIRECTIONS:
            handled = True
            audio.play("click3", replace=True)
        if keypress == constants.UP:
            self.cursorpos[1] = max(self.cursorpos[1] - 1, 0)
        if keypress == constants.DOWN:
            self.cursorpos[1] = min(self.cursorpos[1] + 1, self.size[1]-1)
        if keypress == constants.LEFT:
            self.cursorpos[0] = max(self.cursorpos[0] - 1, 0)
        if keypress == constants.RIGHT:
            self.cursorpos[0] = min(self.cursorpos[0] + 1, self.size[0]-1)

        if keypress == pygame.K_z:
            handled = True
            itempos = self.cursorpos[0]*self.size[1]+self.cursorpos[1]
            items = self.parent.world.entity_component(self.parent.world.tags.player, c.Inventory).contents
            if itempos < len(items):
                self.game.set_focus(self.add_child_scene(InventoryOptions, items[itempos]))

        return handled

    def update(self, delta):
        if self.visible or self.game.focus_scene is self:
            self.pos.update(delta)
            if self.pos.x < -self.slot_size*2-20:
                self.visible = False
            else:
                self.visible = True

    def draw(self, screen):
        if not self.visible:
            return

        drawposx = round(self.pos.x)
        drawposy = round(self.pos.y)

        black_box_pos = (drawposx-5*constants.MENU_SCALE, drawposy-5*constants.MENU_SCALE)
        black_box_size = tuple(self.slot_size * self.size[i] +10*constants.MENU_SCALE for i in range(2))
        pygame.draw.rect(screen, constants.BLACK, (black_box_pos, black_box_size))

        inventory = self.parent.world.entity_component(self.parent.world.tags.player, c.Inventory)

        for widget in self.widgets:
            widget.draw(screen, (drawposx, drawposy))

        for i, entity in enumerate(inventory.contents):
            pos = (drawposx+self.slot_size*(i//self.size[1]+0.5), drawposy+self.slot_size*(i % self.size[1]+0.5))
            self.parent.draw_centered_entity(screen, entity, constants.MENU_SCALE, pos)

        inv_cursor_screenpos = (drawposx + self.slot_size * self.cursorpos[0], drawposy + self.slot_size * self.cursorpos[1])
        screen.blit(self.game.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE), inv_cursor_screenpos)

    def show(self):
        """Tell inventory to move onscreen."""
        self.pos.move((40, self.pos.y))
        audio.play("snap1", replace=True)
        audio.dim_music()
        self.game.set_focus(self)

    def hide(self):
        """Tell inventory to move offscreen."""
        self.pos.move((-self.slot_size*2-21, self.pos.y))
        audio.play("drop", replace=True)
        audio.undim_music()
        self.game.set_focus(self.parent)
