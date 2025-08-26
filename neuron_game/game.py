from tkinter import LAST, ROUND, Canvas, Frame, Tk

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
        self.root.geometry(f"{960 * nb_player}x{570 if not multiplayer else 1080}")
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
        titles = (
            ["Neuron membrane potential"]
            if not multiplayer
            else ["Excitatory neuron", "Inhibitory neuron", "Target neuron"]
        )
        self.canvases = []
        for i, (neuron, title) in enumerate(zip(self.neurons, titles, strict=False)):
            root = self.frames[0]
            if i == len(self.neurons) - 1 and multiplayer:
                root = self.frames[1]
            self.canvases.append(
                PlotDisplay(root, origin_value=neuron.V_m, ylims=[-90, -30], title=title)
            )
        connectome = None
        if multiplayer:
            connectome = np.zeros((nb_neuron, nb_neuron), dtype=float)
            connectome[0][2] = 100.0
            connectome[1][2] = -100.0
            self.arrows = [Canvas(self.frames[1]) for _ in range(2)]
            self.arrows[0].grid(row=0, column=0, sticky="n")
            self.arrows[1].grid(row=0, column=2, sticky="n")
            self.arrows[0].create_text(240, 180, text="Excitatory Input")
            self.arrows[0].create_line(
                50,
                0,
                50,
                200,
                340,
                200,
                arrow=LAST,
                arrowshape=(20, 30, 10),
                width=7,
                fill="#99cfe0",
                capstyle=ROUND,
                joinstyle=ROUND,
            )
            self.arrows[1].create_text(100, 180, text="Inhibitory Input")
            self.arrows[1].create_line(
                310,
                0,
                310,
                200,
                20,
                200,
                20,
                185,
                20,
                215,
                width=7,
                fill="#ee7d7b",
                capstyle=ROUND,
                joinstyle=ROUND,
            )
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
        self.controller.grid(rows=[0] * nb_neuron, columns=[0] if not multiplayer else [0, 1, 1])
        self.update()
        self.root.mainloop()


NeuronGame(True)
