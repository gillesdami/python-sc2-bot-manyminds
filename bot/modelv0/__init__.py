import json
import logging

import numpy as np
import sc2

from . import constants as C
from .action_executioner import ActionExecutioner
from .model import AttentionLSTM
from .state_view import StateView
from .utils import setup_logger

class Bot(sc2.BotAI, StateView, ActionExecutioner):
    def __init__(self, in_state_path: str, out_ns: str):
        sc2.BotAI.__init__(self)
        
        self.in_state_path = in_state_path
        self.out_ns = out_ns

        self.history = {}
        self.general_logger = logging.getLogger(__name__)
        self.learning_logger = setup_logger('learning', self.out_ns + 'learning.log')

        self.general_logger.info('TODO load from %s', self.in_state_path)

    def on_start(self):
        StateView.__init__(self)
        ActionExecutioner.__init__(self)

        self.learning_logger.info('map size: %s', str(self.map_size))

        # heatmap of actions location
        self.interest_map = np.zeros((self.map_size[0], self.map_size[1]), dtype=np.int) 

        self.build_model = AttentionLSTM(
            self.building_view_size,
            C.MODEL_HIDDEN_SIZE,
            self.building_action_size)
        
        self.production_model = AttentionLSTM(
            self.production_view_size,
            C.MODEL_HIDDEN_SIZE,
            self.production_action_size)

        self.military_model = AttentionLSTM(
            self.military_view_size,
            C.MODEL_HIDDEN_SIZE,
            self.military_action_size)
        
        self.general_logger.info('Model initialization succeed')

    async def on_step(self, iteration: int):
        if iteration == 0:
            return await self.chat_send(f"glhf !")
        elif iteration % 3 == 0:
            viewer = self.building_viewer
            model = self.build_model
            executioner = self.building_executioner
        elif iteration % 3 == 1:
            viewer = self.production_viewer
            model = self.production_model
            executioner = self.production_executioner
        elif iteration % 3 == 2:
            viewer = self.military_viewer
            model = self.military_model
            executioner = self.military_executioner
        
        if not ('predic%d' % (iteration % 3)) in self.history:
            self.history['viewer%d' % (iteration % 3)] = []
            self.history['predic%d' % (iteration % 3)] = []
            self.history['reward%d' % (iteration % 3)] = []

        model.zero_grad()

        view = viewer()
        output = model(view)
        
        await executioner(output.detach().numpy()[0])

        self.history['viewer%d' % (iteration % 3)].append(view)
        self.history['predic%d' % (iteration % 3)].append(output)

    def on_end(self, game_result: sc2.data.Result):
        print(game_result)
        self.general_logger.info('TODO save to %s', self.out_ns)

        interest_map = '\n'.join([','.join([str(cell) for cell in row]) for row in self.interest_map])
        self.learning_logger.info('Action heatmap:\n' + interest_map)