# SC2 LSTM bot

WIP

## Dependencies

Dependencies are managed using pipenv:

```bash
pipenv install
```

Download Stracraft 2 and the maps as documented [here](https://github.com/Dentosal/python-sc2).

## Train

train_locally.py allow to train the bot against other bots or version of himself.

```bash
python3 train_locally.py --help
# example
python3 train_locally.py --train modelv0/Zerg/KingsCoveLE/test.pkl --against dronerush/Zerg/KingsCoveLE/test.pkl --output test
```

## Run

WIP

Refer to [Dentosal/sc2-bot-match-runner](https://github.com/Dentosal/sc2-bot-match-runner)
