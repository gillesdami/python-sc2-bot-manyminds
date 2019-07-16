from torch import randn, sigmoid, Tensor
from torch.nn import LSTM, Linear, Module
from torch.nn.modules.activation import Sigmoid
from torch.nn.init import uniform

class AttentionLSTM(Module):
    def __init__(self, view_size, hidden_size, action_size, num_layer=1):
        super(AttentionLSTM, self).__init__()

        self.view_size = view_size
        self.hidden_size = hidden_size
        self.action_size = action_size
        self.num_layer = num_layer

        self.reset_hidden()
        
        self.lstm = LSTM(view_size, hidden_size, num_layer)
        self.dense = Linear(hidden_size, action_size)
    
    def reset_hidden(self):
        self.hidden = (
            randn(self.num_layer, 1, self.hidden_size) / self.hidden_size ** .5, 
            randn(self.num_layer, 1, self.hidden_size) / self.hidden_size ** .5
        )

    def backward():
        loss_function = nn.NLLLoss()
        optimizer = optim.SGD(model.parameters(), lr=0.1)


        model.zero_grad()

        tag_scores = model(sentence_in)

        loss = loss_function(tag_scores, targets)
        loss.backward()
        optimizer.step()

    def forward(self, input):
        input = Tensor(input).view(1, 1, -1)
        output, self.hidden = self.lstm(input, self.hidden)
        output = self.dense(output.view(1, -1))
        
        return sigmoid(output)

