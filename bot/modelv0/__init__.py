import json

import sc2
from torch.nn import LSTM

from .action_executioner import ActionExecutioner
from .state_view import StateView

class Bot(sc2.BotAI, StateView, ActionExecutioner):
    def __init__(self, in_state_path: str, out_ns: str):
        sc2.BotAI.__init__(self)

        self.history = {}

        self.in_state_path = in_state_path
        self.out_ns = out_ns

        print('TODO load from', self.in_state_path)  

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
        prediction = model.predict(view)
        #await executioner(prediction)

        self.history['viewer%d' % (iteration % 3)].append(view)
        self.history['predic%d' % (iteration % 3)].append(prediction)

    async def on_end(self, game_result: sc2.data.Result):
        print(game_result)
        print('TODO save to', self.out_ns)
