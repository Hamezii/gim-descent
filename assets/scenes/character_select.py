"""Contains the CharacterSelect scene."""

import constants
import entity_templates
import key_input
import widget as wgt

from . import main_menu
from .dungeon import Dungeon
from .scene import Scene


class CharacterSelect(Scene):
    """Allows you to choose who you play as. Opens at new game."""
    characters = ("magnum", "mecha", "edward")
    num_characters = 3
    character_desc = (
        "Magnum",
        "Mecha",
        "Punchout",
    )
    character_detail = (
        ("Balanced and reliable", "Disciplined fighter"),
        ("Thick armour comes in handy", "Half efficiency when drinking potions"),
        ("Gets a free turn after any kill", "Can't take many hits")
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cursor_pos = 0
        self.desc_widget = wgt.Text(
            renderer=self.game.renderer,
            size=constants.MENU_SCALE * 10,
            offset=(self.game.width/4, self.game.height/2 + constants.MENU_SCALE * 45)
        )
        self.detail_widget = wgt.TextLines(
            renderer=self.game.renderer,
            size=constants.MENU_SCALE * 5,
            offset=(self.game.width/4, self.game.height/2 + constants.MENU_SCALE * 60)
        )

        self.widgets = [
            wgt.Text(
                renderer=self.game.renderer,
                text="Choose your character",
                size=constants.MENU_SCALE * 15,
                offset=(self.game.width / 2, constants.MENU_SCALE * 100),
                centered=True
            ),
            self.desc_widget,
            self.detail_widget
        ]

    def handle_input(self, keypress):
        if keypress.has_action(key_input.Action.RIGHT):
            self.cursor_pos = min(self.cursor_pos+1, 2)

        if keypress.has_action(key_input.Action.LEFT):
            self.cursor_pos = max(self.cursor_pos-1, 0)

        if keypress.has_action(key_input.Action.BACK):
            self.game.change_base_scene(main_menu.MainMenu)

        if keypress.has_action(key_input.Action.ACCEPT):
            self.game.change_base_scene(Dungeon)
            dungeon = self.game.base_scene
            dungeon.init_world()
            if self.cursor_pos == 0: # Magnum
                dungeon.world.tags.player = dungeon.world.create_entity(*entity_templates.magnum(0, 0))
            if self.cursor_pos == 1: # Mecha
                dungeon.world.tags.player = dungeon.world.create_entity(*entity_templates.mecha(0, 0))
            if self.cursor_pos == 2: # Edward
                dungeon.world.tags.player = dungeon.world.create_entity(*entity_templates.edward(0, 0))
            dungeon.new_game()
        return True

    def draw(self, screen):
        screen.fill(constants.ALMOST_BLACK)
        cursor_image = self.game.renderer.get_image(name="inventory-cursor-box", scale=constants.MENU_SCALE)

        for i, character in enumerate(self.characters):
            spacing = constants.MENU_SCALE* constants.TILE_SIZE * 2
            character_pos = (self.game.width/2 + spacing*(i - (self.num_characters-1)/2), self.game.height/2)
            character_image = self.game.renderer.get_image(name=character, scale=constants.MENU_SCALE)
            self.game.renderer.draw_centered_image(screen, character_image, (character_pos))
            if self.cursor_pos == i:
                self.game.renderer.draw_centered_image(screen, cursor_image, (character_pos))

        self.desc_widget.text = self.character_desc[self.cursor_pos]
        self.detail_widget.text = self.character_detail[self.cursor_pos]

        for widget in self.widgets:
            widget.draw(screen)
