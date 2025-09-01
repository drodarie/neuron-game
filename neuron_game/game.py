from functools import partial
from tkinter import LAST, ROUND, Button, Canvas, Frame, Tk

import numpy as np

from neuron_game.controller import GameController
from neuron_game.display import PlotDisplay
from neuron_game.iaf_cond_alpha import IAFCondAlpha


class Panel:
    def __init__(self, root, nb_frames=1):
        self._root = root
        self.root = Frame(root)
        self.root.grid(row=0, column=0, sticky="nsew")
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.frames = [Frame(self.root) for _ in range(nb_frames)]
        for i, frame in enumerate(self.frames):
            frame.grid(row=i, column=0)
        self.has_quit = False

    def cleanup(self):
        self.root.grid_forget()
        self.root.destroy()

    def update(self):
        if not self.has_quit:
            self._root.after(5, self.update)

    def start(self):
        self.update()


class NeuronPanel(Panel):
    def __init__(
        self,
        root,
        titles: list[str] = None,
        display_control: list[bool] = None,
        display_parameters=True,
        save_values=False,
        simulation_duration: float = -1.0,
        start_paused: bool = False,
    ):
        if titles is None:
            titles = ["Neuron membrane potential"]
        super().__init__(root, len(titles))
        if display_control is None:
            display_control = [True]
        assert len(titles) > 0 and len(titles) == len(display_control)
        nb_neurons = len(titles)

        # model
        self.neurons = [IAFCondAlpha() for _ in range(nb_neurons)]
        self.connectome = np.zeros((nb_neurons, nb_neurons), dtype=float)

        # view
        self.canvases = [
            PlotDisplay(self.frames[i // 2], origin_value=neuron.V_m, ylims=[-90, -30], title=title)
            for i, (neuron, title) in enumerate(zip(self.neurons, titles, strict=False))
        ]
        self.controller = GameController(
            self.canvases,
            self.neurons,
            display_parameters=[display_parameters] * len(self.neurons),
            display_controls=display_control,
            connectome=self.connectome,
            save_values=save_values,
            simulation_duration=simulation_duration,  # in ms
            start_paused=start_paused,
        )

    def start(self):
        self.controller.grid()
        self._root.bind("<Key>", self.controller._keystroke)
        super().start()

    def update(self):
        done = False
        if not self.has_quit:
            done = self.controller.update()
            if not done:
                super().update()
        return done

    def cleanup(self):
        super().cleanup()
        self._root.unbind("<Key>")


class MultiplayerGame(NeuronPanel):
    def __init__(self, root):
        super().__init__(
            root,
            ["Excitatory neuron", "Inhibitory neuron", "Target neuron"],
            display_control=[True, True, False],
            display_parameters=False,
            save_values=True,
            simulation_duration=50.0,
            start_paused=True,
        )
        self.side_canvases = [Canvas(self.frames[1]) for _ in range(2)]
        self._side_display()

        self.connectome[0][2] = 100.0
        self.connectome[1][2] = -100.0

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
        if super().update():
            self.cleanup()
            self.root.quit()
            return True


class SingleExploration(NeuronPanel):
    def __init__(self, root):
        super().__init__(root)
        self.frames.append(Frame(self.root))
        self.quit_button = Button(
            self.frames[-1],
            padx=6,
            # bg=color,
            text="Return to main menu",
            command=self.quit,
        )
        self.frames[-1].grid(row=1, column=0, sticky="n")
        self.quit_button.grid(column=0, row=0, padx=10, pady=10, sticky="n")

    def quit(self):
        self.has_quit = True
        self.cleanup()
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
        self.root.protocol("WM_DELETE_WINDOW", self.cleanup)
        self.current_display = None
        self.stopped = False

        current_choice = None
        while not self.stopped:
            if current_choice is None:
                self.root.geometry("960x620")
                self.current_display = MainMenu(self.root)
            elif current_choice:
                self.root.geometry("1920x1075")
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
