"""Contains the HUD scene."""

import pygame

import components as c
import constants
import widget as wgt

from .scene import Scene


class HUD(Scene):
    """Displays information about your health, etc."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        health_bar_pos = constants.MENU_SCALE*8*4, constants.HEIGHT - constants.MENU_SCALE*8*5
        health_bar_size = constants.MENU_SCALE*8*14, constants.MENU_SCALE*8
        self.health_bar = pygame.Rect(health_bar_pos, health_bar_size)

        self.max_health_text = wgt.Text(
            renderer=self.game.renderer,
            size=15*constants.MENU_SCALE
        )

        self.health_text = wgt.Text(
            renderer=self.game.renderer,
            size=15*constants.MENU_SCALE,
            offset=(self.health_bar.left + 5*constants.MENU_SCALE, self.health_bar.top - 15*constants.MENU_SCALE)
        )

        self.level_text = wgt.Text(
            renderer=self.game.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x, self.health_bar.bottom + 5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.kills_text = wgt.Text(
            renderer=self.game.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x, self.health_bar.bottom + 17.5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.time_text = wgt.Text(
            renderer=self.game.renderer,
            size=10*constants.MENU_SCALE,
            offset=(self.health_bar.x + 80 * constants.MENU_SCALE, self.health_bar.bottom + 17.5*constants.MENU_SCALE),
            color=constants.LIGHT_GRAY
        )

        self.widgets = [
            self.max_health_text,
            self.health_text,
            self.level_text,
            self.kills_text,
            self.time_text
        ]

    def unfocused_input(self, keypress):
        """Respond to an input independent of what scene is currently being focused on."""
        if keypress == pygame.K_F8:
            self.remove_scene()

    def draw(self, screen):
        # Health bar
        health = self.parent.world.entity_component(self.parent.world.tags.player, c.Health)
        health_color = self.parent.get_health_bar_color(health)

        border_rect = self.health_bar.inflate(constants.MENU_SCALE*4, constants.MENU_SCALE*4)
        pygame.draw.rect(screen, constants.ALMOST_BLACK, border_rect)

        if health.current > 0:
            health_width = self.health_bar.width * (health.current / health.max)
            pygame.draw.rect(screen, health_color, (self.health_bar.topleft, (health_width, self.health_bar.height)))



        # Widgets

        self.health_text.color = self.max_health_text.color = health_color
        self.health_text.text = str(health.current)

        self.max_health_text.text = "/"+str(health.max)
        text_len = len(self.max_health_text.text)
        self.max_health_text.offset = (self.health_bar.right + (1 - text_len*4)*3*constants.MENU_SCALE, self.health_bar.top - 15*constants.MENU_SCALE)

        kills = self.parent.world.entity_component(self.parent.world.tags.player, c.GameStats).kills
        self.kills_text.text = "Kills " + str(kills)

        time = self.parent.world.entity_component(self.parent.world.tags.player, c.GameStats).time
        time_s = str(int(time % 60))
        if len(time_s) == 1:
            time_s = "0" + time_s
        time_m = str(int(time // 60))

        self.time_text.text = "Time " + time_m + ":" + time_s

        level = self.parent.world.entity_component(self.parent.world.tags.player, c.Level).level_num
        self.level_text.text = "Level " + str(level)

        for widget in self.widgets:
            widget.draw(screen)
