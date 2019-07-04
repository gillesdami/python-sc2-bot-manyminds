from functools import reduce
import json

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId

with open("bot/modelv0/const.json", "r") as h:
    RAW = json.load(h)

## TRAINING_SETTINGS
LR = 0.01

## SHARED_SETTINGS
CONTROL_GROUPS_COUNT = 10
CONTROL_GROUPS_MAX_UNIT_COUNT = 25

## VIEW_SETTINGS
MAX_ZERG_BUILDINGS_VIEWED_PER_TYPE = 16
MAX_ENEMY_UNITS_VIEWED = 100
HEALTH_VIEWED_SIZE = 4

## LISTS
### ZERG
ZERG_UNITS = list(filter(lambda u: u['race'] == 'Zerg', RAW['Unit']))
ZERG_WORKERS = list(filter(lambda u: u['is_worker'], ZERG_UNITS))
ZERG_MILITARY = list(filter(lambda u: not (u['is_structure'] or u['is_worker']), ZERG_UNITS))
#### ABILITIES
ZERG_ABILITIES_IDS = list(reduce(
    lambda acc, val: acc.update(map(lambda a: a['ability'], val['abilities'])) or acc,
    ZERG_UNITS,
    set()))
ZERG_MILITARY_ABILITIES_IDS = list(reduce(
    lambda acc, val: acc.update(map(lambda a: a['ability'], val['abilities'])) or acc,
    ZERG_MILITARY,
    set()))
ZERG_MILITARY_ABILITIES = list(map(
    lambda a_id: next(filter(lambda a: a['id'] == a_id, RAW['Ability'])), 
    ZERG_MILITARY_ABILITIES_IDS))
ZERG_LARVATRAIN_ABILITIES = list(filter(lambda a: a['name'].startswith('LARVATRAIN_'), RAW['Ability']))
#### UNITS
ZERG_UNITS_IDS = list(map(lambda u: u['id'], ZERG_UNITS))
ZERG_UNITS_LARVATRAINABLE_IDS = list(map(lambda a: a['target']['Morph']['produces'], ZERG_LARVATRAIN_ABILITIES))
ZERG_UNITS_LARVATRAINABLE = list(map(
    lambda u_id: next(filter(lambda u: u['id'] == u_id, ZERG_UNITS)), 
    ZERG_UNITS_LARVATRAINABLE_IDS))
#### BUILDINGS
ZERG_BUILDINGS = list(filter(lambda u: u['is_structure'], ZERG_UNITS))
ZERG_BUILDINGS_IDS = list(map(lambda u: u['id'], ZERG_BUILDINGS))
