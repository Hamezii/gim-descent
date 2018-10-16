'''
GIM Descent 4

James Lecomte

To do:
- Improve AI
'''

# VV Do this to profile VV
# py -m cProfile -s tottime gim.pyw

import pickle
import random
import os

import pygame

import audio
import components as c
import constants
import entity_templates
import levelgen
import renderer
import systems as s
import ui
from ecs import World

#from functools import lru_cache

pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

pygame.mixer.set_num_channels(8)

audio.load_audio()


# CLASSES

class Game:
    """The game. Can perform functions on the ECS."""

    def __init__(self):
        self.renderer = renderer.Renderer()
        self.world: World = None

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
            data["blinking"] = self.world.entity_component(entity, c.Render).blinking and self.renderer.is_blinking()

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
        entity_surface = self.renderer.entity_image(scale, **self.entity_draw_data(entity))
        self.renderer.draw_centered_image(surface, entity_surface, pos)

    def teleport_entity(self, entity, amount):
        """Teleport an entity to a random position in a specific radius."""
        pos = self.world.entity_component(entity, c.TilePosition)
        while True:
            randpos = (pos.x+random.randint(-amount, amount),
                       pos.y+random.randint(-amount, amount))
            if self.world.get_system(s.GridSystem).on_grid(randpos):
                if self.world.get_system(s.GridSystem).get_blocker_at(randpos) == 0:
                    self.world.get_system(s.GridSystem).move_entity(entity, randpos)
                    return

    def speed_entity(self, entity, amount):
        """Give an entity free turns."""
        if self.world.has_component(entity, c.FreeTurn):
            self.world.entity_component(entity, c.FreeTurn).life += amount
        else:
            self.world.add_component(entity, c.FreeTurn(amount))

    def heal_entity(self, entity, amount):
        """Heal an entity for a certain amount of health."""
        if self.world.has_component(entity, c.Health):
            health = self.world.entity_component(entity, c.Health)
            health.current = min(health.max, health.current+amount)

    def generate_level(self):
        """Generate a level depending on how far the player is."""

        level_num = self.world.entity_component(self.world.tags.player, c.Level).level_num

        g_sys = self.world.get_system(s.GridSystem)
        gridsize = (g_sys.gridwidth, g_sys.gridheight)

        if level_num == 12:
            level = levelgen.generate_fly_boss_level(gridsize)
        else:
            level = levelgen.generate_random_level(gridsize, level_num)

        for components in level.entities:
            self.world.create_entity(*components)
        self.world.add_component(self.world.tags.player, c.TilePosition(*level.player_start))

        if level_num == 1:
            pos = self.world.entity_component(self.world.tags.player, c.TilePosition)
            for _ in range(3):
                self.world.create_entity(*entity_templates.bomb(pos.x, pos.y))

    def has_save(self):
        """Return True if there is a save file and False otherwise."""
        return os.path.isfile("save.save")

    def delete_save(self):
        """Delete the save file."""
        os.remove("save.save")

    def save_game(self):
        """Save the game state."""
        if self.world is not None: # If there is a world to save
            if not self.world.has_component(self.world.tags.player, c.Dead): # If the player is not dead
                with open("save.save", "wb") as save_file:
                    pickle.dump(self.world, save_file)

    def load_game(self):
        """Load the game from where it was last saved."""
        with open("save.save", "rb") as save_file:
            self.world = pickle.load(save_file)
            self.world.set_game_reference(self)

    def add_system(self, system_instance):
        """Add a system to the ECS and give it a reference to this game."""
        self.world.add_system(system_instance)
        system_instance.game = self
        system_instance.renderer = self.renderer

    def init_world(self):
        """Initialise for a new game."""
        self.world = World()

        self.add_system(s.GameStatsSystem())

        self.add_system(s.GridSystem())
        self.add_system(s.InitiativeSystem())

        self.add_system(s.PlayerInputSystem())
        self.add_system(s.AIFlyWizardSystem())
        self.add_system(s.AISystem())
        self.add_system(s.FreezingSystem())
        self.add_system(s.BurningSystem())
        self.add_system(s.AIDodgeSystem())
        self.add_system(s.BumpSystem())

        self.add_system(s.ExplosionSystem())
        self.add_system(s.DamageSystem())
        self.add_system(s.RegenSystem())
        self.add_system(s.PickupSystem())
        self.add_system(s.IdleSystem())
        self.add_system(s.SplitSystem())
        self.add_system(s.StairsSystem())

        self.add_system(s.AnimationSystem())

        self.add_system(s.DeadSystem())
        self.add_system(s.DeleteSystem())

    def new_game(self):
        """Set the seed then generate a level."""
        if constants.SEED is not None:
            random.seed(constants.SEED)

        self.generate_level()

# MAIN

def get_input(events):
    """Return the last key that was just pressed."""
    keypress = None

    for event in events:
        if event.type == pygame.KEYDOWN:
            keypress = event.key

            if event.key == pygame.K_w or event.key == pygame.K_UP:
                keypress = constants.UP

            if event.key == pygame.K_a or event.key == pygame.K_LEFT:
                keypress = constants.LEFT

            if event.key == pygame.K_s or event.key == pygame.K_DOWN:
                keypress = constants.DOWN

            if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                keypress = constants.RIGHT

    return keypress


def main():
    """Run the game."""

    screen = init_screen()

    game = Game()

    menus = ui.MenuManager(game)

    menus.add_menu(ui.MainMenu)

    while True:

        delta = CLOCK.tick()
        fps = CLOCK.get_fps()
        if fps != 0:
            avgms = 1000/fps
        else:
            avgms = delta

        screen.fill(constants.BLACK)

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game.save_game()
                ui.leave()
        keypress = get_input(events)

        if keypress == pygame.K_MINUS:  # Zooming out
            if game.renderer.camera.get_zoom() > 20:
                game.renderer.camera.zoom(-20)

        if keypress == pygame.K_EQUALS:  # Zooming in
            game.renderer.camera.zoom(20)

        if keypress == pygame.K_F10: # Save
            game.save_game()
        if keypress == pygame.K_F11: # Load
            game.load_game()

        menus.send_event(("input", menus.get_focus(), keypress))

        if game.world:    # Processing ecs
            game.world.process(playerinput=None, d_t=delta)

            while not game.world.has_component(game.world.tags.player, c.MyTurn): # Waiting for input
                game.world.process(playerinput=None, d_t=0)

        game.renderer.t_elapsed += delta
        menus.send_event(("update", avgms))
        menus.draw_menus(screen)

        pygame.display.update()

def init_screen():
    """Returns the screen surface, as well as WIDTH and HEIGHT constants."""

    pygame.display.set_caption("Gim 4")

    if constants.FULLSCREEN_MODE:
        info_object = pygame.display.Info()
        constants.WIDTH = info_object.current_w
        constants.HEIGHT = info_object.current_h

        screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
    else:
        screen = pygame.display.set_mode((constants.WIDTH, constants.HEIGHT))

    constants.MENU_SCALE = round(constants.WIDTH/600)

    pygame.display.set_icon(pygame.image.load(constants.IMAGES+"logo.png").convert_alpha())

    return screen

if __name__ == "__main__":
    CLOCK = pygame.time.Clock()

    main()
