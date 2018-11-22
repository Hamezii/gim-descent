"""Contains the InventoryOptions scene."""

import pygame

import audio
import components as c
import constants
import widget as wgt
from misc import DynamicPos

from .scene import Scene
from .throw_options import ThrowOptions


class InventoryOptions(Scene):
    """Option menu for item selected in menu."""

    def __init__(self, item, **kwargs):
        super().__init__(**kwargs)
        self.world = self.parent.parent.world
        self.item = item
        self.options = []
        self.visible = True
        if self.world.has_component(item, c.UseEffect):
            self.options.append("use")
        if self.world.has_component(item, c.Explosive):
            self.options.append("prime")
        self.options.append("throw")
        self.options.append("drop")
        self.size = len(self.options)

        inv_slot_size = constants.TILE_SIZE*constants.MENU_SCALE
        self.pos = (40 + inv_slot_size*2 + 12*constants.MENU_SCALE, self.game.height/2 - inv_slot_size*3)
        image_bottom = self.pos[1]+inv_slot_size*1.5
        self.options_pos = [DynamicPos((self.pos[0], image_bottom + (10 + i*12)*constants.MENU_SCALE), speed=20) for i in range(self.size)]
        self.cursorpos = 0

        audio.play("snap2", replace=True)

        self.widgets = []
        if self.world.has_component(self.item, c.Describable):
            text_x = constants.TILE_SIZE * constants.MENU_SCALE * 1.6
            describe = self.world.entity_component(self.item, c.Describable)
            self.widgets.extend((
                wgt.Text(renderer=self.game.renderer, size=10*constants.MENU_SCALE, text=describe.name, offset=(text_x, 0)),
                wgt.Text(renderer=self.game.renderer, size=5*constants.MENU_SCALE, text=describe.desc, offset=(text_x, 15*constants.MENU_SCALE)),
            ))

    def handle_input(self, keypress):
        if keypress == constants.DOWN:
            self.cursorpos = min(self.cursorpos + 1, self.size-1)
            audio.play("click2", replace=True)
        if keypress == constants.UP:
            self.cursorpos = max(self.cursorpos - 1, 0)
            audio.play("click2", replace=True)
        if keypress == pygame.K_x:
            self.remove_scene()
            audio.play("drop", replace=True)
        if keypress == pygame.K_z:
            audio.play("snap1", replace=True)

            selection = self.options[self.cursorpos]
            if selection == "use":
                self.remove_scene()
                use = self.world.entity_component(self.item, c.UseEffect)
                if self.world.has_component(self.world.tags.player, c.WeakPotions):
                    for effect in use.effects: # Weak potions for mecha
                        getattr(self.parent.parent, effect[0])(self.world.tags.player, int(effect[1]/2), *effect[2:])
                else:
                    for effect in use.effects: # Normal effect
                        getattr(self.parent.parent, effect[0])(self.world.tags.player, *effect[1:])

                if self.world.entity_component(self.item, c.Item).consumable:
                    self.world.entity_component(self.world.tags.player, c.Inventory).contents.remove(self.item)
                    self.world.delete_entity(self.item)

            if selection == "prime":
                self.world.entity_component(self.item, c.Explosive).primed = True

            if selection == "throw":
                self.visible = False
                throw_scene = self.parent.add_child_scene(ThrowOptions, self.item)
                self.game.set_focus(throw_scene)
                self.remove_scene()

            if selection == "drop":
                self.remove_scene()
                self.world.entity_component(self.world.tags.player, c.Inventory).contents.remove(self.item)
                self.world.remove_component(self.item, c.Stored)

                pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
                self.world.add_component(self.item, c.TilePosition(pos.x, pos.y))

        handled = keypress in (*constants.DIRECTIONS, pygame.K_z, pygame.K_x)
        return handled

    def update(self, delta):
        for pos in self.options_pos:
            pos.update(delta)

    def draw(self, screen):
        if not self.visible:
            return
        for i, pos in enumerate(self.options_pos):
            if i == self.cursorpos:
                pos.move((self.pos[0]+24*constants.MENU_SCALE, pos.y))
            else:
                pos.move((self.pos[0]+12*constants.MENU_SCALE, pos.y))
            pygame.draw.rect(screen, (0, 0, 0), (pos.x, pos.y, 60*constants.MENU_SCALE, 12*constants.MENU_SCALE), 0)
            text_pos = (pos.x+30*constants.MENU_SCALE, pos.y + 6*constants.MENU_SCALE)
            self.game.renderer.draw_text(screen, constants.WHITE, text_pos, self.options[i], size=5 * constants.MENU_SCALE, centered=True)

        option_cursor_image = self.game.renderer.get_image(name="cursor", color=(
            255, 255, 255, pygame.BLEND_ADD), scale=constants.MENU_SCALE)
        option_cursor_pos = (self.pos[0], self.pos[1]+12*constants.MENU_SCALE *
                             (self.cursorpos+0.5)+(constants.TILE_SIZE*1.5+10)*constants.MENU_SCALE)
        self.game.renderer.draw_centered_image(screen, option_cursor_image, option_cursor_pos)

        pos = (self.pos[0] + constants.TILE_SIZE * constants.MENU_SCALE * 0.75, self.pos[1] + constants.TILE_SIZE * constants.MENU_SCALE * 0.75)
        self.game.renderer.draw_centered_image(screen, self.game.renderer.get_image(name="inventory-slot", scale=constants.MENU_SCALE*1.5), pos)
        self.parent.parent.draw_centered_entity(screen, self.item, constants.MENU_SCALE*1.5, pos)

        for widget in self.widgets:
            widget.draw(screen, self.pos)
