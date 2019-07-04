from keras.layers import LSTM, Input
from keras.models import Sequential

class StepViewGenerator(viewer, executer):
    


def LSTM(input_size, output_size):
    model = Sequential()
    model.add(Input(input_size))
    model.add(LSTM(output_size, return_sequences=True))
    model.compile(loss=lambda p,t: t, optimizer='adam')

    return model