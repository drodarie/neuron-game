# Simulation game of point-neurons 

This educational game should help players to understand neuron electrical activity through simulation.

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

## Context
In this game, we simulate neurons as integrate and fire point-neurons and display their membrane potential in a plot.  
The plots are automatically updated according to time. Simulation can be paused pressing the `spacebar` button.  
Each neuron's spike events are highlighted with light green vertical lines.  

Players can interact with neurons by sending either an excitatory or inhibitory input.
These inputs can be sent using the corresponding buttons displayed.

This game has two modes that you can choose from the main menu:
- A single neuron simulation where the user can manipulate each parameter of the neuron 
to understand its behavior
- A two player mode where each player competes with their own neuron on the result of a target one.

### Single neuron simulation

In this mode, only one neuron will be simulated.
You can control any of its input by linking one (or more) key.
Only alphanumerical keys can be used as control to stimulate the neuron.

### Two player mode
In the two player mode, each player can interface with one of the top source neurons.
Each source neuron is connected to the target neuron with a synapse. 
So, their spike event will produce an input on the target neuron.

The neuron on the left is excitatory, and produce an excitatory input on its target.
The neuron on the right is inhibitory, and produce an inhibitory input on its target.

The goal of each player is to drive the membrane potential of the target neuron towards their own extrema 
(bottom for the right player and top for the left player).

This mode starts in a paused state to let time for each player to prepare themselves.
A random letter key will be chosen to stimulate each neuron. After each spike, this letter will change.
The simulation will last 30 ms (simulation time) after which the game will be over.

The winner is designated as the player who would have deviated the membrane potential of the target neuron 
the most, with respect to its equilibrium value: the leakage potential (E_L=-70 mV)
