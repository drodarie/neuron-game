from functools import partial
from tkinter import LAST, LEFT, ROUND, Button, Canvas, Frame, Label, Tk

import numpy as np

from neuron_game.controller import GameController
from neuron_game.display import EXCITATORY_BLUE, INHIBITORY_RED, PlotDisplay, ResultsDisplay
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
        colors: list[str] = None,
        display_control: list[bool] = None,
        display_parameters=True,
        save_values=False,
        simulation_duration: float = -1.0,
        start_paused: bool = False,
    ):
        if titles is None:
            titles = ["Neuron membrane potential"]
        if colors is None:
            colors = ["blue"]
        super().__init__(root, len(titles))
        if display_control is None:
            display_control = [True]
        assert (
            len(titles) > 0 and len(titles) == len(display_control) and len(titles) == len(colors)
        )
        nb_neurons = len(titles)

        # model
        self.neurons = [IAFCondAlpha() for _ in range(nb_neurons)]
        self.connectome = np.zeros((nb_neurons, nb_neurons), dtype=float)

        # view
        self.canvases = [
            PlotDisplay(
                self.frames[i // 2],
                origin_value=neuron.V_m,
                ylims=[-90, -30],
                color=color,
                title=title,
            )
            for i, (neuron, color, title) in enumerate(
                zip(self.neurons, colors, titles, strict=False)
            )
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
        self.controller.cleanup()


class MultiplayerGame(NeuronPanel):
    def __init__(self, root):
        self.titles = ["Excitatory neuron", "Inhibitory neuron", "Target neuron"]
        self.colors = [EXCITATORY_BLUE, INHIBITORY_RED, "purple"]
        super().__init__(
            root,
            self.titles,
            display_control=[True, True, False],
            display_parameters=False,
            colors=self.colors,
            save_values=True,
            simulation_duration=50.0,
            start_paused=True,
        )
        self.side_canvases = [Canvas(self.frames[1]) for _ in range(2)]
        self._side_display()

        self.connectome[0][2] = 100.0
        self.connectome[1][2] = -100.0
        self.show_results = False

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

    def display_results(self):
        self.controller.is_paused = True
        self.controller.reset_wait_for_key()
        for canvas in self.side_canvases:
            canvas.grid_forget()
            canvas.destroy()
        for canvas in self.canvases:
            canvas.frame.grid_forget()
            canvas.frame.destroy()
        self._root.unbind("<Key>")
        self.canvases = [
            ResultsDisplay(
                self.frames[0],
                [n.save_file for n in self.controller.controllers],
                self.neurons[0].V_th,
                colors=self.colors,
                ylims=[-90, -30],
                titles=self.titles,
            )
        ]
        self.canvases[0].grid(row=0, column=0, sticky="nsew")
        result_text = f"Mean {self.titles[-1]} V_m: {self.canvases[0].means[-1]:.2f} mV"
        label_results = Label(self.frames[-1], text=result_text, font=("Arial", 15), justify=LEFT)
        quit_button = Button(
            self.frames[-1],
            padx=6,
            # bg=color,
            text="Return to main menu",
            command=self.quit,
        )
        self.frames[-1].grid(row=1, column=0, sticky="nswe")
        self.frames[-1].rowconfigure(0, weight=1)
        self.frames[-1].columnconfigure(0, weight=1)
        label_results.grid(row=0, column=0, sticky="nwe")
        quit_button.grid(column=0, row=1, padx=10, pady=10, sticky="n")
        self.show_results = True

    def update(self):
        if not self.has_quit:
            done = self.controller.update()
            if done and not self.show_results:
                self.display_results()
            super(NeuronPanel, self).update()
        else:
            self.cleanup()
            self.root.quit()
            return True
        return False

    def quit(self):
        self.has_quit = True


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
            command=partial(self.choose_game, 0),
        )
        self.multi_button = Button(
            self.frames[0],
            padx=6,
            # bg=color,
            text="Multiplayer neuron competition",
            command=partial(self.choose_game, 1),
        )
        self.quit_button = Button(
            self.frames[0],
            padx=6,
            # bg=color,
            text="Quit the game",
            command=partial(self.choose_game, 2),
        )
        self.single_button.grid(column=0, row=0, padx=10, pady=10)
        self.multi_button.grid(column=0, row=1, padx=10, pady=10)
        self.quit_button.grid(column=0, row=2, padx=10, pady=10)
        self.choice = None

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
            if current_choice == 2:
                self.root.destroy()
                break
            elif current_choice == 1:
                self.root.geometry("1920x1075")
                self.current_display = MultiplayerGame(self.root)
            elif current_choice == 0:
                self.root.geometry("960x620")
                self.current_display = SingleExploration(self.root)
            else:
                self.root.geometry("960x620")
                self.current_display = MainMenu(self.root)
            self.current_display.start()
            self.root.mainloop()
            current_choice = getattr(self.current_display, "choice", None)
            del self.current_display

    def cleanup(self):
        self.current_display.cleanup()
        self.root.destroy()
        self.stopped = True


NeuronGame()
