from tkinter import Frame, Tk

import numpy as np

from neuron_game.controller import GameController
from neuron_game.display import PlotDisplay
from neuron_game.iaf_cond_alpha import IAFCondAlpha


class NeuronGame:
    def update(self):
        self.controller.update()
        self.root.after(5, self.update)

    def __init__(self, multiplayer: bool = False):
        self.root = Tk()
        self.root.title("Neuron Game")
        nb_player = 2 if multiplayer else 1
        self.root.geometry(f"{1000 * nb_player}x{500 * nb_player}")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=7)

        self.frames = (
            [Frame(self.root)] if not multiplayer else [Frame(self.root) for _ in range(2)]
        )
        for i, frame in enumerate(self.frames):
            frame.grid(row=i, column=0)

        nb_neuron = 3 if multiplayer else 1
        self.neurons = [IAFCondAlpha() for _ in range(nb_neuron)]
        self.canvases = []
        for i, neuron in enumerate(self.neurons):
            root = self.frames[0]
            if i == len(self.neurons) - 1 and multiplayer:
                root = self.frames[1]
            self.canvases.append(
                PlotDisplay(
                    root, origin_value=neuron.V_m, ylims=[-90, -30], title=f"Neuron {i + 1}"
                )
            )
        connectome = None
        if multiplayer:
            connectome = np.zeros((nb_neuron, nb_neuron), dtype=float)
            connectome[0][2] = 100.0
            connectome[1][2] = -100.0
        display_controls = [True] if not multiplayer else [True, True, False]
        display_parameters = [True] if not multiplayer else [False] * len(self.neurons)
        self.controller = GameController(
            self.canvases,
            self.neurons,
            display_parameters=display_parameters,
            display_controls=display_controls,
            connectome=connectome,
        )
        self.root.bind("<Key>", self.controller._keystroke)
        self.controller.grid()
        self.update()
        self.root.mainloop()


NeuronGame(True)
