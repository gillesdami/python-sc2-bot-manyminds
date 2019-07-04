import argparse
import importlib

from sc2 import run_game, maps, Race
from sc2.player import Bot

parser = argparse.ArgumentParser(description='Train a bot against one or many other')
parser.add_argument('--train', 
    help='Should be <ModelName>/<race>/<map>/<statefile>')
parser.add_argument('--against',    nargs='+', 
    help='List of bot used as oponents <ModelName>/<race>/<map>/<statefile> or ')
parser.add_argument('--output', 
    help='Base name of the resulting state and log files')
parser.add_argument('--epochs',                 default=1,      type=int,
    help='Number of games played')
parser.add_argument('--step-time-limit',        default=1.0,    type=float,
    help="Max seconds per step")
parser.add_argument('--game-time-limit',        default=3600,   type=int,
    help="Max seconds per game")
args = parser.parse_args()

train_parameters = args.train.split('/')
oponents_parameters = [oponent.split('/') for oponent in args.against]

the_map = maps.get(train_parameters[2])
base_dir = 'saves/' + '/'.join(train_parameters[0:3]) + '/'
out_ns = base_dir + args.output

for i in range(args.epochs):
    oponent_parameters = oponents_parameters[i % len(oponents_parameters)]

    TrainingBot = importlib.import_module('bot.' + train_parameters[0]).Bot
    OposingBot = importlib.import_module('bot.' + oponent_parameters[0]).Bot

    run_game(
        the_map,
        [
            Bot(Race[train_parameters[1]], TrainingBot(
                in_state_path='saves/' + args.train, out_ns=out_ns + str(i))),
            Bot(Race[oponent_parameters[1]], OposingBot(
                in_state_path='saves/' + '/'.join(oponent_parameters)))
        ],
        realtime=False, 
        step_time_limit=args.step_time_limit, 
        game_time_limit=args.game_time_limit,
        save_replay_as= base_dir + args.output + '.SC2Replay')
