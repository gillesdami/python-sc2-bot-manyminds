import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.position import Point2

from . import constants as C

class ActionExecutioner():
    def __init__(self):
        pass

    @property
    def building_action_size(self):
        return len(C.ZERG_BUILDINGS_IDS) * (1 + 1 + 1)

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

        for idx in reversed(priorities_sorted_idxs):
            if priorities[idx] < 0.5:
                return
            if self.can_afford(C.ZERG_BUILDINGS_IDS[idx]):
                position = Point2([idx + 1, idx + 2])
                await self.build(C.ZERG_BUILDINGS_IDS[idx], near=position)
                return
    
    @property
    def production_action_size(self):
        return len(C.ZERG_UNITS_LARVATRAINABLE_IDS)

    async def production_executioner(self, actions):
        '''
        Actions is a vector with the nodes corresponding to:
        - for each unit
          - priority

        They result in the following abilities:
        - self.do(larvae.random.train(<Unit_type_id>))
        '''
        mask = actions > 0.5
        action_sorted_idxs = actions.argsort()
        units_to_prod_idxs = action_sorted_idxs[mask]

        for unit_idx in units_to_prod_idxs:
            unit_type_id = UnitTypeId(unit_idx)
            if self.can_afford(unit_type_id):
                # could produce multiple of the same type
                await self.do(larvae.random.train(unit_type_id))

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
        actions_vec_idx = 0

        for control_group in self.control_groups:
            group_units = control_group.select_units(self.units)

            for ability in C.ZERG_MILITARY_ABILITIES:
                if actions[actions_vec_idx] > 0.5:
                    ability_id = AbilityId(ability_id)
                    target = Point2([actions[actions_vec_idx + 1], actions[actions_vec_idx + 2]])
                    
                    for unit in group_units:
                        if ability["target"] == "None" and await self.can_cast(unit, ability_id):
                            todo_actions.append(unit(ability_id))
                        elif ability["target"] == "Unit":
                            target_unit = self.state.units.closest_to(target)
                            if await self.can_cast(unit, ability_id):
                                todo_actions.append(unit(ability_id, target_unit))
                    # end group_units
            # end abilities
                actions_vec_idx += 3
        # end control_groups
        await self.do_actions(todo_actions)

    # research_view
    # meta_view
    # queens_view
    # eco_view