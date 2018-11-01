"""Contains the Dungeon scene."""

import os
import random

import pygame

import components as c
import constants
import dungeon_gen
import entity_templates
import level_gen
import systems as s
from ecs import World

from . import main_menu
from .scene import Scene
from .level_select import LevelSelect
from .level import Level


class Dungeon(Scene):
    """The current dungeon. Stores the layout and can perform functions on the ECS."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world: World = None
        self.dungeon_network = None

    def handle_input(self, keypress):
        if keypress == pygame.K_F10: # Save
            self.save_game()
        if keypress == pygame.K_F11: # Load
            self.load_game()
        if keypress == pygame.K_ESCAPE: # Exiting to menu
            self.save_game()
            self.game.change_base_scene(main_menu.MainMenu)

        return True

    def is_blinking(self):
        """Return True if blinking images should be lit up at the moment."""
        if self.game.t_elapsed % constants.BLINK_RATE < constants.BLINK_RATE/2:
            return True
        return False

    #@lru_cache()
    def entity_draw_data(self, entity):
        """Return a dictionary of draw data about an entity."""
        data = {}
        # Image name
        data["name"] = self.world.entity_component(entity, c.Render).imagename
        # Color modifier
        color = [0, 0, 0]
        if self.world.has_component(entity, c.FireElement) or self.world.has_component(entity, c.Burning):
            color[0] += 100
        if self.world.has_component(entity, c.IceElement):
            color[0] += 0
            color[1] += 50
            color[2] += 100
        if any(color):
            data["color"] = (color[0], color[1], color[2], pygame.BLEND_ADD)
        # Blinking tag
        if self.world.has_component(entity, c.Render):
            data["blinking"] = self.world.entity_component(entity, c.Render).blinking and self.is_blinking()

        # Icons
        icons = []
        if self.world.has_component(entity, c.FireElement):
            icons.append(("elementFire", None))

        if self.world.has_component(entity, c.IceElement):
            icons.append(("elementIce", None))

        if self.world.has_component(entity, c.Explosive):
            explosive = self.world.entity_component(entity, c.Explosive)
            if explosive.primed:
                icons.append(("explosive", explosive.fuse))

        if self.world.has_component(entity, c.FreeTurn):
            freeturn = self.world.entity_component(entity, c.FreeTurn)
            icons.append(("free-turn", freeturn.life))

        data["icons"] = tuple(icons)

        data["frozen"] = self.world.has_component(entity, c.Frozen)

        # Returning dictionary
        return data

    def draw_centered_entity(self, surface, entity, scale, pos):
        """Draw an entity, including icons etc."""
        entity_surface = self.game.renderer.entity_image(scale, **self.entity_draw_data(entity))
        self.game.renderer.draw_centered_image(surface, entity_surface, pos)

    def show_level(self):
        """Add the level scene and focus on it."""
        self.game.set_focus(self.add_child_scene(Level, self.world))

    def generate_level(self):
        """Generate a level depending on how far the player is."""

        level_num = self.world.entity_component(self.world.tags.player, c.Level).level_num
        g_sys = self.world.get_system(s.GridSystem)
        gridsize = (g_sys.gridwidth, g_sys.gridheight)
        if level_num == 12:
            level = level_gen.generate_fly_boss_level(gridsize)
        else:
            level = level_gen.generate_random_level(gridsize, level_num)

        for components in level.entities:
            self.world.create_entity(*components)
        self.world.add_component(self.world.tags.player, c.TilePosition(*level.player_start))

        if level_num == 1:
            self.world.add_component(self.world.tags.player, c.FreeTurn(1)) # To fix off-by-one turn timing
            inv = self.world.entity_component(self.world.tags.player, c.Inventory)
            for _ in range(3):
                # This code will create the bomb, remove its tile position then
                # manually put it into the player's inventory.
                bomb = self.world.create_entity(*entity_templates.bomb(0, 0))
                self.world.remove_component(bomb, c.TilePosition)
                self.world.add_component(bomb, c.Stored(self.world.tags.player))
                inv.contents.append(bomb)
        else:
            self.world.remove_component(self.world.tags.player, c.MyTurn) # To fix off-by-one turn timing

    def get_health_bar_color(self, health_comp):
        """Return what color an entity's health bar should be given its health component."""
        amount_left = health_comp.current / health_comp.max
        if amount_left > 0.5:
            return constants.GREEN
        if amount_left > 0.2:
            return constants.ORANGE
        return constants.RED

    def delete_save(self):
        """Delete the save file."""
        os.remove("save.save")

    def save_game(self):
        """Save the game state.

        Temporarily disabled.
        """
        pass
        # if self.world is not None: # If there is a world to save
        #     if self.player_alive: # If the player is not dead
        #         with open("save.save", "wb") as save_file:
        #             pickle.dump(self.world, save_file)

    def load_game(self):
        """Load the game from where it was last saved.

        Temporarily disabled.
        """
        pass
        # with open("save.save", "rb") as save_file:
        #     self.world = pickle.load(save_file)
        #     self.world.set_game_reference(self)

    def init_world(self):
        """Initialise for a new game."""
        self.world = World()

        self.world.add_system(s.GameStatsSystem())

        self.world.add_system(s.GridSystem())
        self.world.add_system(s.InitiativeSystem())

        self.world.add_system(s.PlayerInputSystem())
        self.world.add_system(s.AIFlyWizardSystem())
        self.world.add_system(s.AISystem())
        self.world.add_system(s.FreezingSystem())
        self.world.add_system(s.BurningSystem())
        self.world.add_system(s.AIDodgeSystem())
        self.world.add_system(s.BumpSystem())

        self.world.add_system(s.ExplosionSystem())
        self.world.add_system(s.DamageSystem())
        self.world.add_system(s.RegenSystem())
        self.world.add_system(s.PickupSystem())
        self.world.add_system(s.IdleSystem())
        self.world.add_system(s.SplitSystem())
        self.world.add_system(s.StairsSystem())

        self.world.add_system(s.AnimationSystem())

        self.world.add_system(s.DeadSystem())
        self.world.add_system(s.DeleteSystem())

    def new_game(self):
        """Set the seed then generate a level."""
        if constants.SEED is not None:
            random.seed(constants.SEED)

        self.dungeon_network = dungeon_gen.generate_dungeon_layout()
        self.game.set_focus(self.add_child_scene(LevelSelect))
