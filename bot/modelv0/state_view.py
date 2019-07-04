import math

import numpy as np
from sc2.ids.unit_typeid import UnitTypeId
from sc2.helpers.control_group import ControlGroup
from sklearn.cluster import KMeans

from . import constants as C

class StateView():
    def __init__(self):
        self.map_size = [int(round(size)) for size in self.game_info.map_size]
        self.map_size_sum = self.map_size[0] + self.map_size[1]
        self.meta = np.zeros(16) #TODO move
        self.control_groups = [ControlGroup([]) for i in range(C.CONTROL_GROUPS_COUNT)]
        # todo add units to control_groups

    ## utils
    @staticmethod
    def one_hot_encode(value, size):
        return np.eye(1, size, value)

    @staticmethod
    def get_unit_rouded_position(unit):
        return unit.position.rounded

    @staticmethod
    def get_zerg_unit_id(unit):
        return C.ZERG_UNITS_IDS.index(unit.type_id)

    @staticmethod
    def get_unit_health(unit):
        return math.floor(unit.health_percentage * (C.HEALTH_VIEWED_SIZE - 1))

    @staticmethod
    def zero_pad_1d(array, final_length):
        return np.pad(array, (0, final_length - len(array)), mode='constant')

    ## views
    def eco_viewer(self):
        '''
        WIP
        Projection of the game state for an AI controlling the workers in the gathering group.

        It uses data from:
        - known_enemy_units         Units
        - townhalls                 Units
        - geysers                   Units
        - gathering_workers_group   ControlGroup
        - mineral_field             Units

        And return the following structure:

        '''
        self.known_enemy_units #Units
        self.townhalls #Units
        self.geysers #Units
        self.workers #> filter worker building #Units
        self.mineral_field #Units
    
    def queens_viewer(self):
        pass

    @property
    def building_view_size(self):
        return 16 + 1 + 1 + len(C.ZERG_BUILDINGS_IDS) + (self.map_size_sum + len(C.ZERG_UNITS_IDS)) * C.MAX_ENEMY_UNITS_VIEWED

    def building_viewer(self):
        '''
        Projection of the game state for an AI controlling the construction of buildings.

        It uses data from:
        - meta                      number[]
        - units                     Units
        - workers                   Units
        - minerals                  number
        - vespene                   number
        - known_enemy_units         Units

        And return the following structure:
        - meta                      16
        - minerals                  1
        - vespene                   1
        - structure_units           C.ZERG_BUILDINGS_IDS
        - known_enemy_units         (self.map_size_sum + C.ZERG_UNITS_IDS_LEN) * C.MAX_ENEMY_UNITS_VIEWED
        '''
        def structure_units_to_view():
            view = np.array([])

            for unit_type in C.ZERG_BUILDINGS_IDS:
                ability = self._game_data.units[unit_type.value].creation_ability

                amount = len(self.units(unit_type).not_ready)
                amount += sum([o.ability == ability for w in self.workers for o in w.orders])

                view = np.concatenate((
                    view,
                    np.eye(1, C.MAX_ZERG_BUILDINGS_VIEWED_PER_TYPE, max([amount, C.MAX_ZERG_BUILDINGS_VIEWED_PER_TYPE - 1]))
                ))
            
            return StateView.zero_pad_1d(view, len(C.ZERG_BUILDINGS_IDS))

        def known_enemy_units_to_view():
            known_enemy_units = self.known_enemy_units.take(C.MAX_ENEMY_UNITS_VIEWED)
            view_size = (self.map_size_sum + len(C.ZERG_UNITS_IDS)) * C.MAX_ENEMY_UNITS_VIEWED

            view = np.array([])

            for known_enemy_unit in known_enemy_units:
                if known_enemy_unit.type_id in C.ZERG_UNITS_IDS:
                    position = StateView.get_unit_rouded_position(known_enemy_unit)
                    unit_id_idx = StateView.get_zerg_unit_id(known_enemy_unit)

                    view = np.concatenate((
                        view,
                        np.eye(1, len(C.ZERG_UNITS_IDS), unit_id_idx),
                        np.eye(1, self.map_size[0], position[0]),
                        np.eye(1, self.map_size[1], position[1])
                    ))
                
            return StateView.zero_pad_1d(view, view_size)

        return np.concatenate((
            self.meta, 
            [self.minerals],
            [self.vespene],
            structure_units_to_view(),
            known_enemy_units_to_view()
        ))
    
    @property
    def production_view_size(self):
        return 16 + 1 + 1 + len(C.ZERG_UNITS_IDS) + len(C.ZERG_UNITS_IDS)

    def production_viewer(self):
        '''
        Projection of the game state for an AI controlling the production of units.

        It uses data from:
        - meta                          number[]
        - units                         Units
        - known_enemy_units             Units
        - already_pending(UnitTypeId)   number
        - minerals                      number
        - vespene                       number

        And return the following structure:
        - meta                      16
        - minerals                  1
        - vespene                   1
        - known_enemy_units_count   C.ZERG_UNITS_IDS_LEN
        - units_count               C.ZERG_UNITS_IDS_LEN
        '''
        def known_enemy_units_to_view():
            view = np.zeros(len(C.ZERG_UNITS_IDS))

            for known_enemy_unit in self.known_enemy_units:
                if known_enemy_unit.type_id in C.ZERG_UNITS_IDS:
                    view[C.get_zerg_unit_id(known_enemy_unit)] += 0.01
            
            return view #softmax ?

        def units_including_pending():
            np.zeros(len(C.ZERG_UNITS_IDS))

            for unit in self.units.filter(lambda u: not u.structure):
                if unit.type_id in C.ZERG_UNITS_IDS:
                    view[C.get_zerg_unit_id(known_enemy_unit)] += 0.01
            
            for unit_id_idx, unit_type_idx in enumerate(C.ZERG_UNITS_IDS):
                view[unit_id_idx] += self.already_pending(unit_type_idx) / 100
                
            return view #softmax ?

        return np.concatenate((
            self.meta,
            [self.minerals],
            [self.vespene],
            known_enemy_units_to_view(),
            units_including_pending()
        ))
    
    @property
    def military_view_size(self):
        return (16 + 
            C.MAX_ZERG_BUILDINGS_VIEWED_PER_TYPE * self.map_size_sum +
            C.MAX_ENEMY_UNITS_VIEWED * (len(C.ZERG_UNITS_IDS) + self.map_size_sum + C.HEALTH_VIEWED_SIZE) +
            C.CONTROL_GROUPS_MAX_UNIT_COUNT * (len(C.ZERG_UNITS_IDS) + self.map_size_sum + C.HEALTH_VIEWED_SIZE) * C.CONTROL_GROUPS_COUNT
        )

    def military_viewer(self):
        '''
        Projection of the game state for an AI controlling the military units.

        It uses data from:
        - meta                          number[]
        - units                         Units
        - known_enemy_units             Units
        - control_groups                ControlGroup

        And return the following structure:
        - meta                      16
        - townhall                  C.MAX_ZERG_BUILDINGS_VIEWED_PER_TYPE * self.map_size_sum
        - known_enemy_units         C.MAX_ENEMY_UNITS_VIEWED * (len(C.ZERG_UNITS_IDS) + self.map_size_sum + C.HEALTH_VIEWED_SIZE)
        - units_groups               C.CONTROL_GROUPS_MAX_UNIT_COUNT * (len(C.ZERG_UNITS_IDS) + self.map_size_sum + C.HEALTH_VIEWED_SIZE) * C.CONTROL_GROUPS_COUNT
        '''
        def townhalls_to_view():
            max_encoded_townhalls = C.MAX_ZERG_BUILDINGS_VIEWED_PER_TYPE
            view_size = max_encoded_townhalls * self.map_size_sum

            townhalls = self.townhalls.take(max_encoded_townhalls)

            view = np.array([])

            for townhall in townhalls:
                position = get_unit_rouded_position(townhall)

                view = np.concatenate((
                    view,
                    np.eye(1, self.map_size[0], position[0]),
                    np.eye(1, self.map_size[1], position[1])
                ))
            
            return StateView.zero_pad_1d(view, view_size)

        def known_enemy_units_to_view():
            known_enemy_units = self.known_enemy_units.take(C.MAX_ENEMY_UNITS_VIEWED)
            view_size = C.MAX_ENEMY_UNITS_VIEWED * (len(C.ZERG_UNITS_IDS) + self.map_size_sum + C.HEALTH_VIEWED_SIZE)

            view = np.array([])
            for unit in known_enemy_units:
                if unit.type_id in C.ZERG_UNITS_IDS:
                    position = get_unit_rouded_position(unit)

                    view = np.concatenate((
                        view,
                        np.eye(1, len(C.ZERG_UNITS_IDS), StateView.get_zerg_unit_id(unit)),
                        np.eye(1, self.map_size[0], position[0]),
                        np.eye(1, self.map_size[1], position[1]),
                        np.eye(1, C.HEALTH_VIEWED_SIZE, StateView.get_unit_health(unit))
                    ))

            return StateView.zero_pad_1d(view, view_size)

        def units_groups_to_view():
            # create control groups via kmeans
            military_units = self.units.filter(lambda u: (not u.structure) and (not u.worker))
            self.control_groups = KMeans(n_clusters=10).fit_predict([u.position for u in military_units])
            
            # view creation
            view = np.array([])
            control_group_view_size = C.CONTROL_GROUPS_MAX_UNIT_COUNT * (len(C.ZERG_UNITS_IDS) + self.map_size_sum + C.HEALTH_VIEWED_SIZE)
            view_size =  control_group_view_size * C.CONTROL_GROUPS_COUNT

            for control_group in self.control_groups:
                units = control_group.select_units(self.units)
                control_group_view = np.array([])

                for unit in control_group:
                    if unit.type_id in C.ZERG_UNITS_IDS:
                        position = StateView.get_unit_rouded_position(unit)

                        view = np.concatenate((
                            view,
                            np.eye(1, len(C.ZERG_UNITS_IDS), StateView.get_zerg_unit_id(unit)),
                            np.eye(1, self.map_size[0], position[0]),
                            np.eye(1, self.map_size[1], position[1]),
                            np.eye(1, C.HEALTH_VIEWED_SIZE, StateView.get_unit_health(unit))
                        ))

                view = np.concatenate((
                    view,
                    StateView.zero_pad_1d(control_group_view, control_group_view_size)
                ))
            
            return StateView.zero_pad_1d(view, view_size)
        
        return np.concatenate((
            self.meta,
            townhalls_to_view(),
            known_enemy_units_to_view(),
            units_groups_to_view()
        ))

    def research_viewer(self):
        pass
    
    def meta_viewer(self):
        pass