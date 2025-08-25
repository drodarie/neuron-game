# Tkinter game to simulate point-neurons 
This game displays the membrane potential of three neurons. 
Two are the source neurons that send input to the target neuron.
The input neuron on the left is an excitatory neuron connected to the target neuron with an excitatory synapse.
The other input neuron is inhibitory, is also connected to the target neuron with an inhibitory synapse.

Two players can interact with each source neuron by sending either an excitatory or inhibitory input, 
either using the buttons displayed or by linking one (or more) key to each input type.
Only alphanumerical keys can be used to stimulate neurons.

When a neuron receives enough excitation it will create a spike. 
A spike event will be highlighted with a vertical red line.
So, for every spike of the input neurons, you should see an effect on the target neuron.

The goal of the left player is to make the target neuron spike while the other player should prevent it.

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