from functools import partial
from tkinter import LAST, ROUND, Button, Canvas, Frame, Tk

import numpy as np

from neuron_game.controller import GameController
from neuron_game.display import PlotDisplay
from neuron_game.iaf_cond_alpha import IAFCondAlpha


class Panel:
    def __init__(self, root, nb_frames=1):
        self.root = root
        self.frames = [Frame(self.root) for _ in range(nb_frames)]
        for i, frame in enumerate(self.frames):
            frame.grid(row=i, column=0)
        self.controller = None

    def cleanup(self):
        self.root.unbind("<Key>")
        for frame in self.frames:
            frame.grid_forget()
            frame.destroy()

    def update(self):
        if self.controller is not None:
            self.controller.update()
        self.root.after(5, self.update)

    def start(self):
        if self.controller is not None:
            self.root.bind("<Key>", self.controller._keystroke)
        self.update()


class MultiplayerGame(Panel):
    def __init__(self, root):
        super().__init__(root, 2)
        nb_neuron = 3
        self.neurons = [IAFCondAlpha() for _ in range(nb_neuron)]
        titles = ["Excitatory neuron", "Inhibitory neuron", "Target neuron"]
        self.canvases = []
        for i, (neuron, title) in enumerate(zip(self.neurons, titles, strict=False)):
            root = self.frames[0]
            if i == len(self.neurons) - 1:
                root = self.frames[1]
            self.canvases.append(
                PlotDisplay(root, origin_value=neuron.V_m, ylims=[-90, -30], title=title)
            )
        self.simulation_time = 50.0  # in ms
        self.decrement = 0.1

        self.side_canvases = [Canvas(self.frames[1]) for _ in range(2)]
        self._side_display()

        connectome = np.zeros((nb_neuron, nb_neuron), dtype=float)
        connectome[0][2] = 100.0
        connectome[1][2] = -100.0
        self.controller = GameController(
            self.canvases,
            self.neurons,
            display_parameters=[False] * len(self.neurons),
            display_controls=[True, True, False],
            connectome=connectome,
            save_values=True,
        )
        self.controller.grid(rows=[0] * nb_neuron, columns=[0, 1, 1])

    def _side_display(self):
        self.side_canvases[0].grid(row=0, column=0, sticky="n")
        self.side_canvases[1].grid(row=0, column=2, sticky="n")
        self.side_canvases[0].create_text(240, 180, text="Excitatory Input")
        dict_arrows = dict(
            arrow=LAST,
            arrowshape=(20, 30, 10),
            width=7,
            fill="#99cfe0",
            capstyle=ROUND,
            joinstyle=ROUND,
        )
        points = [50, 0, 50, 200, 340, 200]
        self.side_canvases[0].create_line(*points, **dict_arrows)

        self.side_canvases[1].create_text(100, 180, text="Inhibitory Input")
        points = [310, 0, 310, 200, 20, 200, 20, 185, 20, 215]
        del dict_arrows["arrow"]
        dict_arrows["fill"] = "#ee7d7b"
        self.side_canvases[1].create_line(*points, **dict_arrows)

    def update(self):
        self.simulation_time -= self.decrement
        if self.simulation_time < 0:
            self.cleanup()
            self.root.quit()
            return
        super().update()


class SingleExploration(Panel):
    def __init__(self, root):
        super().__init__(root, 2)
        self.neuron = IAFCondAlpha()
        self.canvas = PlotDisplay(
            self.frames[0],
            origin_value=self.neuron.V_m,
            ylims=[-90, -30],
            title="Neuron membrane potential",
        )
        self.controller = GameController(
            [self.canvas],
            [self.neuron],
        )
        self.controller.grid(rows=[0], columns=[0])
        self.quit_button = Button(
            self.frames[1],
            padx=6,
            # bg=color,
            text="Return to main menu",
            command=self.quit,
        )
        self.quit_button.grid(column=0, row=0, padx=10, pady=10, sticky="n")
        self.has_quit = False

    def update(self):
        if self.has_quit:
            return
        super().update()

    def quit(self):
        self.cleanup()
        self.has_quit = True
        self.root.quit()


class MainMenu(Panel):
    def __init__(self, root):
        super().__init__(root)
        self.single_button = Button(
            self.frames[0],
            padx=6,
            # bg=color,
            text="Single neuron simulation",
            command=partial(self.choose_game, False),
        )
        self.multi_button = Button(
            self.frames[0],
            padx=6,
            # bg=color,
            text="Multiplayer neuron competition",
            command=partial(self.choose_game, True),
        )
        self.single_button.grid(column=0, row=0, padx=10, pady=10)
        self.multi_button.grid(column=0, row=1, padx=10, pady=10)
        self.choice = False

    def choose_game(self, choice):
        self.choice = choice
        self.cleanup()
        self.root.quit()


class NeuronGame:
    def __init__(self):
        self.root = Tk()
        self.root.title("Neuron Game")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=7)
        self.current_display = None
        self.stopped = False
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)

        current_choice = None
        while not self.stopped:
            if current_choice is None:
                self.root.geometry("960x570")
                self.current_display = MainMenu(self.root)
            elif current_choice:
                self.root.geometry("1920x1080")
                self.current_display = MultiplayerGame(self.root)
            else:
                self.root.geometry("960x620")
                self.current_display = SingleExploration(self.root)
            self.current_display.start()
            self.root.mainloop()
            current_choice = getattr(self.current_display, "choice", None)
            del self.current_display

    def cleanup(self):
        self.current_display.cleanup()
        self.root.destroy()
        self.stopped = True


NeuronGame()
