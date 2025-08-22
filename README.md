# Tkinter game to simulate point-neurons 
This game displays the membrane potential of two neurons. 
The players can interact with each neuron by sending either an excitatory or inhibitory input, 
either with the buttons displayed or by linking one (or more) key to each input type.
Only alphanumerical keys can be used to stimulate neurons.

The goal for each player is to make their neuron spike while preventing the other neuron to spike.
A spike event will be highlighted with a vertical red line.

## Installation

### Install tkinter:
```bash
sudo apt-get install python3-tk
```
### Install neuron-game:
Install the game inside a python3 environment

```bash
cd neuron-game
pip install -e.
```

### Dev install

```bash
cd neuron-game
pip install -e.[dev]
pre-commit install 
```

## Run the game
```bash
python neuron_game/game.py
```