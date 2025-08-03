from tkinter import Tk

from neuron_game.controller import GameController
from neuron_game.display import PlotDisplay
from neuron_game.iaf_cond_alpha import IAFCondAlpha


class NeuronGame:
    def update(self):
        self.controller.update()
        self.root.after(5, self.update)

    def __init__(self, nb_player: int = 1):
        self.root = Tk()
        self.root.title("Neuron Game")
        self.root.geometry(f"{1000 * nb_player}x600")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=7)

        self.neurons = [IAFCondAlpha() for _ in range(nb_player)]
        self.canvases = [
            PlotDisplay(self.root, origin_value=neuron.V_m, ylims=[-85, -40])
            for neuron in self.neurons
        ]
        self.controller = GameController(self.canvases, self.neurons)
        self.controller.grid()
        self.update()
        self.root.mainloop()


NeuronGame(1)
