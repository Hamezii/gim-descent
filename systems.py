"""Contains all the ECS Systems."""

import random
from math import hypot

import audio
import constants
from components import *
from ecs import System


# HELPER FUNCTIONS
def dist(pos1, pos2):
    """Return the distance between 2 points using Pythagoras."""
    return hypot(abs(pos1.x-pos2.x), abs(pos1.y-pos2.y))


def clamp(value, minimum, maximum):
    """Return the value clamped between a range."""
    return min(max(minimum, value), maximum)

#_________________

class GridSystem(System):
    """Stores grid attributes and a grid of blocker entities."""

    def __init__(self):
        super().__init__()
        self.gridwidth = 30
        self.gridheight = 30
        self.blocker_grid = self.blocker_grid = [[0 for y in range(self.gridheight)] for x in range(self.gridwidth)]
        self.grid = self.grid = [[set() for y in range(self.gridheight)] for x in range(self.gridwidth)]
        self._cached_pos = {}

    def on_grid(self, pos):
        """Return True if a position is on the grid."""
        if clamp(pos[0], 0, self.gridwidth-1) == pos[0]:
            if clamp(pos[1], 0, self.gridheight-1) == pos[1]:
                return True
        return False
    
    def random_free_pos(self):
        """Return a position on the grid which does not have a Blocker on it.
        
        WARNNG: Does not mark the returned position as blocked.
        """
        while True:
            randpos = (random.randrange(self.gridwidth), random.randrange(self.gridheight))
            if self.get_blocker_at(randpos) == 0:
                return randpos


    def get_blocker_at(self, pos):
        """Get id of blocker entity at a certain position.

        Returns 0 if there is no blocker entity at this position.
        """
        return self.blocker_grid[pos[0]][pos[1]]

    def get_entities_at(self, pos):
        """Get ids of all entities at a certain position."""
        return self.grid[pos[0]][pos[1]]

    def move_entity(self, entity, pos):
        """Move an entity to a position, raising an error if not possible."""
        entity_pos = self.world.entity_component(entity, TilePositionC)

        if self.world.has_component(entity, BlockerC):
            if self.blocker_grid[pos[0]][pos[1]] == 0:
                self.blocker_grid[entity_pos.x][entity_pos.y] = 0
                self.blocker_grid[pos[0]][pos[1]] = entity

            else:
                raise IndexError("Entity moving to an occupied tile")

        self.grid[entity_pos.x][entity_pos.y].remove(entity)
        entity_pos.x, entity_pos.y = pos
        self.grid[entity_pos.x][entity_pos.y].add(entity)
        self._cached_pos[entity] = pos

    def remove_pos(self, entity):
        """Remove an entity from the grid."""
        cache_x, cache_y = self._cached_pos[entity]
        self.grid[cache_x][cache_y].remove(entity)
        if self.blocker_grid[cache_x][cache_y] == entity:
            self.blocker_grid[cache_x][cache_y] = 0
        del self._cached_pos[entity]

    def update(self, **args):
        for entity, pos in self.world.get_component(TilePositionC):
            if not entity in self._cached_pos:
                self._cached_pos[entity] = (pos.x, pos.y)
                self.grid[pos.x][pos.y].add(entity)
                if self.world.has_component(entity, BlockerC):
                    self.blocker_grid[pos.x][pos.y] = entity

        for entity in tuple(self._cached_pos):
            if not self.world.has_component(entity, TilePositionC):
                self.remove_pos(entity)
                continue

            pos = self.world.entity_component(entity, TilePositionC)
            if (pos.x, pos.y) != self._cached_pos[entity]:
                cache_x, cache_y = self._cached_pos[entity]
                self._cached_pos[entity] = (pos.x, pos.y)

                self.grid[cache_x][cache_y].remove(entity)
                self.grid[pos.x][pos.y].add(entity)


                if self.blocker_grid[cache_x][cache_y] == entity:
                    self.blocker_grid[cache_x][cache_y] = 0
                    self.blocker_grid[pos.x][pos.y] = entity


class InitiativeSystem(System):
    """Acts on Initiative components once a turn passes and hands out MyTurn components."""
    def __init__(self):
        super().__init__()
        self.tick = False

    def update(self, **args):

        self.tick = True
        try:
            for _ in self.world.get_component(MyTurnC):
                self.tick = False
        except KeyError:
            pass

        for entity, freeturn in self.world.get_component(FreeTurnC):
            if self.world.has_component(entity, InitiativeC):
                if self.tick:
                    freeturn.life -= 1
                    if freeturn.life <= 0:
                        self.world.remove_component(entity, FreeTurnC)

                    initiative = self.world.entity_component(entity, InitiativeC)
                    initiative.nextturn -= 1
                    if initiative.nextturn <= 0:
                        initiative.nextturn += initiative.speed
                        self.world.add_component(entity, MyTurnC())
                self.tick = False
            else:
                self.world.remove_component(entity, FreeTurnC)

            return

        for entity, initiative in self.world.get_component(InitiativeC):
            if not self.world.has_component(entity, MyTurnC):
                if self.tick:
                    initiative.nextturn -= 1
                if initiative.nextturn <= 0:
                    initiative.nextturn += initiative.speed
                    self.world.add_component(entity, MyTurnC())


class PlayerInputSystem(System):
    """Interprets input from the player, applying it to all entities with a PlayerInput component."""

    def update(self, **args):
        playerinput = args["playerinput"]
        if playerinput in constants.DIRECTIONS:
            for entity, comps in self.world.get_components(TilePositionC, PlayerInputC, MyTurnC):
                tilepos = comps[0]
                bumppos = (tilepos.x+playerinput[0], tilepos.y+playerinput[1])
                self.world.add_component(entity, BumpC(*bumppos))


class AISystem(System):
    """Lets all AI controlled entities decide what action to make."""

    def update(self, **args):
        grid = self.world.get_system(GridSystem)

        for entity, comps in self.world.get_components(MovementC, TilePositionC, AIC, MyTurnC):
            movement = comps[0]
            pos = comps[1]
            ai = comps[2]

            playerpos = self.world.entity_component(self.world.tags.player, TilePositionC)
            if dist(pos, playerpos) <= 15:
                ai.target = self.world.tags.player
            else:
                ai.target = 0

            if ai.target:
                targetpos = self.world.entity_component(ai.target, TilePositionC)

                movex = 0
                movey = 0
                moved = False
                if movement.diagonal:
                    if pos.x < targetpos.x:
                        movex = 1
                    if pos.x > targetpos.x:
                        movex = -1
                    if pos.y < targetpos.y:
                        movey = 1
                    if pos.y > targetpos.y:
                        movey = -1
                    if grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(entity, BumpC(pos.x+movex, pos.y+movey))

                if not moved:
                    movex = targetpos.x - pos.x
                    movey = targetpos.y - pos.y
                    if abs(movex) < abs(movey):
                        movex = 0
                        if movey < 0:
                            movey = -1
                        if movey > 0:
                            movey = 1
                    else:
                        movey = 0
                        if movex < 0:
                            movex = -1
                        if movex > 0:
                            movex = 1

                    if grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(entity, BumpC(pos.x+movex, pos.y+movey))

                if not moved:
                    if movex != 0:
                        movex = 0
                        movey = targetpos.y - pos.y
                        if movey < 0:
                            movey = -1
                        if movey > 0:
                            movey = 1
                    elif movey != 0:
                        movey = 0
                        movex = targetpos.x - pos.x
                        if movex < 0:
                            movex = -1
                        if movex > 0:
                            movex = 1
                    if grid.get_blocker_at((pos.x+movex, pos.y+movey)) in (0, ai.target):
                        moved = True
                        self.world.add_component(entity, BumpC(pos.x+movex, pos.y+movey))


class FreezingSystem(System):
    """Cancels the action of frozen entities attempting to move, defreezing them instead."""

    def update(self, **args):

        try:
            for entity, _ in self.world.get_components(FrozenC, MyTurnC, BumpC):
                self.world.remove_component(entity, FrozenC)
                self.world.remove_component(entity, MyTurnC)
                self.world.entity_component(entity, InitiativeC).nextturn = 1
        except ValueError:
            pass

class BurningSystem(System):
    """Damages burning players, with the fire dying after a certain amount of time."""

    def update(self, **args):

        if not self.world.get_system(InitiativeSystem).tick:
            return

        for entity, burning in self.world.get_component(BurningC):

            if self.world.has_component(entity, HealthC):
                self.world.create_entity(DamageC(entity, 1))

            burning.life -= 1
            if burning.life <= 0:
                self.world.remove_component(entity, BurningC)


class BumpSystem(System):
    """Carries out bump actions, then deletes the Bump components."""

    def update(self, **args):
        for entity, comps in self.world.get_components(TilePositionC, BumpC, MyTurnC):
            bump = comps[1]
            bumppos = (bump.x, bump.y)

            if not self.world.get_system(GridSystem).on_grid(bumppos):
                continue

            targetent = self.world.get_system(GridSystem).get_blocker_at(bumppos)

            if targetent == 0:

                self.world.get_system(GridSystem).move_entity(entity, bumppos)
                self.world.remove_component(entity, MyTurnC)

            else:
                if self.world.has_component(targetent, HealthC) and self.world.has_component(entity, AttackC):
                    if entity == self.world.tags.player or targetent == self.world.tags.player:
                        # The player must be involved for damage to be inflicted in a bump.
                        # This is so that AI don't attack each other when trying to move.
                        damage = self.world.entity_component(entity, AttackC).damage
                        self.world.create_entity(
                            DamageC(targetent, damage,
                                    burn=self.world.has_component(entity, FireElementC),
                                    freeze=self.world.has_component(entity, IceElementC)
                                   )
                        )

                        if entity == self.world.tags.player:
                            self.game.camera.shake(5)
                            audio.play("punch", 0.5)

                        self.world.remove_component(entity, MyTurnC)
        for entity, _ in self.world.get_component(BumpC):
            self.world.remove_component(entity, BumpC)


class ExplosionSystem(System):
    """Manages explosives and makes anything with an ExplodeC component explode."""

    def update(self, **args):

        if self.world.get_system(InitiativeSystem).tick:
            for entity, explosive in self.world.get_component(ExplosiveC):
                if explosive.primed:
                    explosive.fuse -= 1
                    if explosive.fuse <= 0:
                        self.world.add_component(entity, ExplodeC())


        for entity, explode in self.world.get_component(ExplodeC):
            self.world.add_component(entity, DeadC())

            iterentity = entity
            while self.world.has_component(iterentity, StoredC):  # Getting carrier entity
                iterentity = self.world.entity_component(iterentity, StoredC).carrier

            if self.world.has_component(iterentity, TilePositionC):             # Damaging things around it
                pos = self.world.entity_component(iterentity, TilePositionC)
                for x in range(pos.x - explode.radius, pos.x + explode.radius + 1):
                    for y in range(pos.y - explode.radius, pos.y + explode.radius + 1):
                        if not self.world.get_system(GridSystem).on_grid((x, y)):
                            continue
                        for target_entity in self.world.get_system(GridSystem).get_entities_at((x, y)):
                            if self.world.has_component(target_entity, DestructibleC) and not self.world.has_component(target_entity, HealthC):
                                self.world.add_component(target_entity, DeadC())
                            if self.world.has_component(target_entity, ItemC):
                                self.world.add_component(target_entity, DeadC())
                            else:
                                self.world.create_entity(DamageC(target_entity, explode.damage))

                dist_to_player = dist(pos, self.world.entity_component(self.world.tags.player, TilePositionC))
                if dist_to_player < 10:
                    self.game.camera.shake(40 - dist_to_player * 3)
                    audio.play("explosion", 0.6 - dist_to_player * 0.05)

class DamageSystem(System):
    """Manages damage events, applying the damage and then deleting the message entity."""

    def update(self, **args):
        for message_entity, damage in self.world.get_component(DamageC):
            if self.world.has_component(damage.target, HealthC):
                targethealth = self.world.entity_component(damage.target, HealthC)

                targethealth.current -= damage.amount
                if damage.target == self.world.tags.player:
                    self.game.camera.shake(5 + damage.amount*2)
                    audio.play("ow", 0.4)
                if targethealth.current <= 0:
                    self.world.add_component(damage.target, DeadC())

                if damage.burn and not self.world.has_component(damage.target, FireElementC):
                    self.world.add_component(damage.target, BurningC(5))

                if damage.freeze and not self.world.has_component(damage.target, IceElementC):
                    self.world.add_component(damage.target, FrozenC())

            if self.world.has_component(damage.target, ExplosiveC):
                self.world.entity_component(damage.target, ExplosiveC).primed = True

            self.world.delete_entity(message_entity)

class RegenSystem(System):
    """Heals creatures with a RegenC component when they are injured."""
    def update(self, **args):
        if self.world.get_system(InitiativeSystem).tick:
            for entity, regen in self.world.get_component(RegenC):
                if self.world.has_component(entity, HealthC):
                    health = self.world.entity_component(entity, HealthC)
                    if health.current < health.max:
                        health.current = min(health.current + regen.amount, health.max)


class PickupSystem(System):
    """Allows carrier entities to pick up entities with a Pickup component as long it is not their turn."""

    def update(self, **args):
        for entity, comps in self.world.get_components(TilePositionC, InventoryC):
            if not self.world.has_component(entity, MyTurnC):
                pos = comps[0]
                inventory = comps[1]
                for item, item_comps in self.world.get_components(TilePositionC, ItemC):
                    if len(inventory.contents) < inventory.capacity:
                        item_pos = item_comps[0]
                        if (item_pos.x, item_pos.y) == (pos.x, pos.y):
                            self.world.remove_component(item, TilePositionC)
                            self.world.add_component(item, StoredC(entity))
                            inventory.contents.append(item)


class IdleSystem(System):
    """Makes AI controlled entities idle for a turn if no action was taken."""

    def update(self, **args):
        for entity, _ in self.world.get_components(AIC, MyTurnC):
            self.world.remove_component(entity, MyTurnC)
            if self.world.has_component(entity, InitiativeC):
                self.world.entity_component(entity, InitiativeC).nextturn = 1

class StairsSystem(System):
    """Handles the changing of level when the player steps on stairs."""

    def update(self, **args):
        player = self.world.tags.player
        player_pos = self.world.entity_component(player, TilePositionC)


        for _, comps in self.world.get_components(StairsC, TilePositionC):
            stair = comps[0]
            stair_pos = comps[1]
            if player_pos.x == stair_pos.x and player_pos.y == stair_pos.y:

                entities_to_remove = []

                if stair.direction == "down":
                    self.world.entity_component(player, LevelC).level_num += 1
                player_entities = [player]
                if self.world.has_component(player, InventoryC):
                    for entity in self.world.entity_component(player, InventoryC).contents:
                        player_entities.append(entity)
                for entity, _ in self.world.get_component(TilePositionC):
                    if entity not in player_entities:
                        entities_to_remove.append(entity)
                for entity, _ in self.world.get_component(StoredC):
                    if entity not in player_entities:
                        entities_to_remove.append(entity)
                self.game.generate_level()
                self.world.get_system(GridSystem).update()
                spawn_pos = self.world.get_system(GridSystem).random_free_pos()
                player_pos.x, player_pos.y = spawn_pos
                if not self.world.has_component(player, FreeTurnC):
                    self.world.add_component(player, FreeTurnC(1)) # stops player from getting hit at the beginning of the level.

                for entity in entities_to_remove:
                    self.remove_entity(entity)

    def remove_entity(self, entity):
        """TEMPORAY: A bit hacky

        Remove an entity from the world when you change level.
        """
        self.world.delete_entity(entity)
        if self.world.has_component(entity, StoredC): # Removes entity from inventories
            carrier = self.world.entity_component(entity, StoredC).carrier
            self.world.entity_component(carrier, InventoryC).contents.remove(entity)
        if self.world.has_component(entity, TilePositionC):
            self.world.get_system(GridSystem).remove_pos(entity)

class DeadSystem(System):
    """Handles any entities that have been tagged as dead and queues them for deletion."""

    def update(self, **args):
        for entity, _ in self.world.get_component(DeadC):
            self.world.delete_entity(entity)
            if self.world.has_component(entity, StoredC): # Removes entity from inventories
                carrier = self.world.entity_component(entity, StoredC).carrier
                self.world.entity_component(carrier, InventoryC).contents.remove(entity)
            if self.world.has_component(entity, TilePositionC):
                self.world.get_system(GridSystem).remove_pos(entity)



class AnimationSystem(System):
    """Updates Render components on entities with an Animation component."""

    ANIMATION_RATE = 1000/4

    def __init__(self):
        super().__init__()
        self.t_last_frame = 0

    def update(self, **args):

        self.t_last_frame += args["t_frame"]

        frames_elapsed = self.t_last_frame // self.ANIMATION_RATE

        self.t_last_frame = self.t_last_frame % self.ANIMATION_RATE

        for entity, comps in self.world.get_components(AnimationC, RenderC):
            animation = comps[0]
            render = comps[1]

            playing_animation = animation.animations["idle"]

            if self.world.has_component(entity, InitiativeC):
                entity_nextturn = self.world.entity_component(
                    entity, InitiativeC).nextturn
                player_nextturn = self.world.entity_component(
                    self.world.tags.player, InitiativeC).nextturn
                if entity_nextturn <= player_nextturn:
                    playing_animation = animation.animations["ready"]

            if animation.current_animation != playing_animation:
                animation.current_animation = playing_animation
                animation.pos = 0
            else:
                animation.pos = int((animation.pos + frames_elapsed) %
                                    len(animation.current_animation))

            render.imagename = animation.current_animation[animation.pos]
