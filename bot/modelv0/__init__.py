import json
import logging

import sc2
from torch import Tensor
from torch.nn import LSTM

from .action_executioner import ActionExecutioner
from .state_view import StateView

class Bot(sc2.BotAI, StateView, ActionExecutioner):
    def __init__(self, in_state_path: str, out_ns: str):
        sc2.BotAI.__init__(self)
        
        self.in_state_path = in_state_path
        self.out_ns = out_ns

        self.history = {}
        self.general_logger = logging.getLogger(__name__)

        self.general_logger.info('TODO load from %s', self.in_state_path)

    def on_start(self):
        StateView.__init__(self)
        ActionExecutioner.__init__(self)

        self.build_model = LSTM(
            self.building_view_size, 
            self.building_action_size, 
            batch_first=True)
        self.production_model = LSTM(
            self.production_view_size, 
            self.production_action_size, 
            batch_first=True)
        self.military_model = LSTM(
            self.military_view_size, 
            self.military_action_size, 
            batch_first=True)
        
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

        view = viewer()
        output, (h_n, c_n) = model(Tensor(view.reshape((1,1,-1))))
        # **output** of shape `(seq_len, batch, num_directions * hidden_size)`
        # TODO dense reduce to (hidden_size)
        await executioner(output.detach().numpy()[0][0])

        self.history['viewer%d' % (iteration % 3)].append(view)
        self.history['predic%d' % (iteration % 3)].append(output)

    def on_end(self, game_result: sc2.data.Result):
        print(game_result)
        self.general_logger.info('TODO save to %s', self.out_ns)
