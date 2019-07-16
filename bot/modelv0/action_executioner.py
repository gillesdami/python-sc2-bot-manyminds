import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

from . import constants as C
from .utils import setup_logger

class ActionExecutioner():
    def __init__(self):
        self.action_logger = setup_logger('action', self.out_ns + '.action.log')

    def normal_to_mapscale(self, point2):
        # ([-1, 1], [-1, 1]) -> ([0, self.map_size[0] - 1], [0, self.map_size[1] -1])
        return Point2([((point2[0] + 1) / 2) * (self.map_size[0] - 1), ((point2[1] + 1) / 2) * (self.map_size[1] - 1)])

    def feed_interest_map(self, position: Point2):
        self.interest_map[int(round(position[0])), int(round(position[1]))] += 1

    def log_action(self, action, target='<none>', actor='<none>'):
        try:
            if isinstance(action, AbilityId):
                name = self._game_data.abilities[action.value].friendly_name
            else:
                name = self._game_data.units[action.value].name
            
            self.action_logger.info('%s at %s by %s' % (name, target, actor))
        
        except KeyError:
            self.action_logger.warn('%s at %s by %s' % (action.value, target, actor))

    @property
    def building_action_size(self):
        return len(C.ZERG_BUILDINGS_ZERGBUILD_TYPEIDS) * (1 + 1 + 1)

    async def building_executioner(self, actions):
        '''
        Actions is a vector with the nodes corresponding to:
        - for each building
          - priority
          - pos[0]
          - pos[1]

        They result in the following abilities:
        - self.build
        '''
        priorities = np.take(actions, range(0, self.building_action_size, 3))
        priorities_sorted_idxs = priorities.argsort()

        for idx in np.flip(priorities_sorted_idxs):
            unit_typeid = C.ZERG_BUILDINGS_ZERGBUILD_TYPEIDS[idx]
            position = self.normal_to_mapscale(Point2([round(actions[idx + 1]), round(actions[idx + 2])]))

            self.feed_interest_map(position)
            
            if priorities[idx] > 0.5 and self.can_afford(unit_typeid):
                await self.build(unit_typeid, near=position)
                self.log_action(unit_typeid, position)
                break
    
    @property
    def production_action_size(self):
        return len(C.ZERG_UNITS_LARVATRAINABLE_IDS)

    async def production_executioner(self, actions):
        '''
        Actions is a vector with the nodes corresponding to:
        - for each unit
          - priority

        They result in the following abilities:
        - self.do(self.units(LARVA).random.train(<Unit_type_id>))
        '''
        mask = actions > 0.5
        action_asort = actions.argsort()
        action_asort_filtered = action_asort[mask]
        action_asort_filtered = np.flip(action_asort_filtered)

        for action_idx in action_asort_filtered:
            unit_id = C.ZERG_UNITS_LARVATRAINABLE_IDS[action_idx]
            unit_type_id = UnitTypeId(unit_id)
            ability_id = self._game_data.units[unit_type_id.value].creation_ability.id

            larvas = self.units(UnitTypeId.LARVA)
            if larvas.exists:
                larva = larvas.random
                abilities = await self.get_available_abilities(larva)
                if ability_id in abilities:
                    await self.do(larva.train(unit_type_id))
                    self.log_action(unit_type_id)

    @property
    def military_action_size(self):
        return C.CONTROL_GROUPS_COUNT * len(C.ZERG_MILITARY_ABILITIES) * 3

    async def military_executioner(self, actions):
        '''
        Actions is a vector with the nodes corresponding to:
        - for each control_group
          - for each ability
            - priority
            - pos[0]
            - pos[1]

        They result in the following abilities:
        - to_actions(*)
        '''
        todo_actions = []
        idx = 0

        for control_group in self.control_groups:
            group_units = control_group.select_units(self.units)

            for ability_id in C.ZERG_MILITARY_ABILITIES_IDS:
                ability_id = AbilityId(ability_id)
                priority, pos0, pos1 = actions[idx], actions[idx + 1], actions[idx + 2]
                target = self.normal_to_mapscale(Point2([pos0, pos1]))

                self.feed_interest_map(target)

                if priority > 0.5:
                    for unit in group_units:
                        if ability["target"] == "None" and await self.can_cast(unit, ability_id):
                            todo_actions.append(unit(ability_id))
                        elif ability["target"] == "Unit":
                            target_unit = self.state.units.closest_to(target)
                            if await self.can_cast(unit, ability_id):
                                todo_actions.append(unit(ability_id, target_unit))
                    # end group_units
                    self.log_action(ability_id, target, control_group)
            # end abilities
                idx += 3
        # end control_groups
        await self.do_actions(todo_actions)

    # research_view
    # meta_view
    # queens_view
    # eco_view