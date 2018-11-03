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

        self.dungeon_center_x = 100 * constants.MENU_SCALE
        self.dungeon_center_y = 120 * constants.MENU_SCALE

        self.network = self.parent.dungeon_network

        self.widgets = []
        for node in self.parent.dungeon_network.get_nodes():
            self.widgets.append(wgt.LevelNode(renderer=self.game.renderer, node=node, offset=self.__node_to_screen_pos(node)))
        self.__update_explorable_nodes()

    def __update_explorable_nodes(self):
        """Update which nodes can be explored.

        A node which can be eplored has not been explored yet
        but is next to one which has been.
        """

        for node in self.network.get_nodes():
            node.can_be_explored = False
            if not node.explored:
                for direction in constants.DIRECTIONS:
                    adj_node = node.connections[direction]
                    if adj_node is not None:
                        if adj_node.explored:
                            node.can_be_explored = True
                if "start" in node.properties:
                    node.can_be_explored = True

    def handle_input(self, keypress):
        if keypress in constants.DIRECTIONS:
            player_node = self.network.player_node
            node = player_node.connections[keypress]
            if node is not None:
                if node.explored or node.can_be_explored:
                    self.network.player_node = node

            return True

        if keypress == pygame.K_z:
            node = self.network.player_node
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

        for node in self.network.get_nodes():
            for direction in (constants.DOWN, constants.RIGHT):
                if node.connections[direction] is not None:
                    other_node = node.connections[direction]
                    color = constants.DARK_GRAY
                    if node.explored or other_node.explored:
                        color = constants.GRAY
                    start = self.__node_to_screen_pos(node)
                    end = self.__node_to_screen_pos(other_node)
                    pygame.draw.line(screen, color, start, end, 5)

        for widget in self.widgets:
            widget.draw(screen)

        player_pos = self.__node_to_screen_pos(self.network.player_node)
        self.parent.draw_centered_entity(screen, self.parent.world.tags.player, constants.MENU_SCALE, player_pos)

    def __node_to_screen_pos(self, node):
        """Return the position of the center of a node on the screen."""
        x = self.dungeon_center_x + node.pos[0] * 50 * constants.MENU_SCALE
        y = self.dungeon_center_y + node.pos[1] * 40 * constants.MENU_SCALE
        return (x, y)
