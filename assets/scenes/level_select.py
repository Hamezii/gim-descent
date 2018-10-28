"""Contains the LevelSelect screen."""

import pygame

import constants
import widget as wgt

from .scene import Scene


class LevelSelect(Scene):
    """Displays the dungeon layout and lets the player choose which level to go to."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_surface = pygame.Surface((constants.WIDTH, constants.HEIGHT))
        self.background_surface.blit(self.game.renderer.get_image(name="dungeon_surface", scale=constants.MENU_SCALE*3), (0, 0))
        self.dungeon_start_x = 100 * constants.MENU_SCALE
        self.dungeon_start_y = 120 * constants.MENU_SCALE
        self.network = self.parent.dungeon_network

        self.widgets = []
        for pos, node in self.parent.dungeon_network.get_nodes():
            screen_pos = self.__dungeon_to_screen_pos(pos)
            self.widgets.append(wgt.LevelNode(renderer=self.game.renderer, level_node=node, offset=screen_pos))
        self.__update_explorable_nodes()

    def __update_explorable_nodes(self):
        """Update which nodes can be explored.

        A node which can be eplored has not been explored yet
        but is next to one which has been.
        """

        for pos, node in self.network.get_nodes():
            node.can_be_explored = False
            if not node.explored:
                for direction in constants.DIRECTIONS:
                    adj_node = self.network.get_node_at(pos[i]+direction[i] for i in range(2))
                    if adj_node is not None:
                        if adj_node.explored:
                            node.can_be_explored = True
                if pos == (0, 0):
                    node.can_be_explored = True

    def get_input(self, keypress):
        if keypress in constants.DIRECTIONS:
            pos = self.network.player_pos
            check_pos = [pos[i]+keypress[i] for i in range(2)]
            node = self.network.get_node_at(check_pos)
            if node is not None:
                if node.explored or node.can_be_explored:
                    self.network.player_pos = check_pos

            return True

        if keypress == pygame.K_z:
            node = self.network.get_node_at(self.network.player_pos)
            if node.can_be_explored:
                node.explored = True
                self.parent.generate_level()
                self.parent.show_level()
                self.remove_scene()
            return True

    def update(self, delta):
        for widget in self.widgets:
            widget.update(delta)

    def draw(self, screen):
        screen.blit(self.background_surface, (0, 0))

        for widget in self.widgets:
            widget.draw(screen)

        dungeon_pos = self.parent.dungeon_network.player_pos
        screen_pos = self.__dungeon_to_screen_pos(dungeon_pos)
        self.parent.draw_centered_entity(screen, self.parent.world.tags.player, constants.MENU_SCALE, screen_pos)

    def __dungeon_to_screen_pos(self, pos):
        x = self.dungeon_start_x + pos[0] * 50 * constants.MENU_SCALE
        y = self.dungeon_start_y + pos[1] * 40 * constants.MENU_SCALE
        return (x, y)
