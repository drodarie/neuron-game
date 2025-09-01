from functools import partial
from os import remove
from os.path import abspath, dirname, exists, join
from tkinter import BOTH, LEFT, RAISED, RIDGE, SUNKEN, Button, Frame, Label, Scale
from uuid import uuid4

import numpy as np

from neuron_game.display import EXCITATORY_BLUE, INHIBITORY_RED, PlotDisplay
from neuron_game.iaf_cond_alpha import PARAMETERS_NAME, RANGES, IAFCondAlpha


class InputController:
    def __init__(self, root, button_text, color, column, weight, delay, observer):
        self.pressed = False
        self.wait_for_key = False
        self.stim_button = Button(
            root,
            padx=6,
            bg=color,
            text=button_text,
            command=self.stim_input,
        )
        self.control_button = Button(
            root,
            padx=6,
            bg=color,
            text="Add control",
            command=self.add_control,
        )
        sticky = "nw" if column == 0 else "ne"
        self.text = Label(root, width=24, height=3, anchor=sticky, justify=LEFT)
        self.stim_button.grid(column=column, row=0, padx=10, pady=10, sticky=sticky)
        self.control_button.grid(column=column, row=1, padx=10, pady=10, sticky=sticky)
        self.text.grid(column=column, row=2, padx=10, sticky=sticky)
        self.weight = weight
        self.delay = delay
        self.observer = observer
        self.keys = []

    def stim_input(self):
        if not self.pressed:
            self.pressed = True
            self.stim_button.config(relief=SUNKEN)
            self.observer.receive_spike(self.weight, self.delay)

    def add_key(self, key):
        self.keys.append(key)
        self.text.config(text=", ".join(self.keys))
        self.end_wait_for_key()

    def end_wait_for_key(self):
        self.control_button.config(relief=RAISED)
        self.wait_for_key = False

    def add_control(self):
        self.wait_for_key = not self.wait_for_key
        self.control_button.config(relief=SUNKEN if self.wait_for_key else RAISED)

    def _delay_button_raise(self):
        if self.pressed:
            self.stim_button.config(relief=RAISED)
            self.pressed = False


class NeuronParams:
    def __init__(self, root, params: dict, observer):
        self.pressed = False
        self.observer = observer

        self.params_button = []
        self.labels = []
        self.tips = []
        loc_root = root
        while loc_root.master.master is not None:
            loc_root = loc_root.master

        for i, (k, v) in enumerate(params.items()):
            self.labels.append(Label(root, text=k))
            self.tips.append(Label(loc_root, text=PARAMETERS_NAME[k], bg="yellow"))
            self.labels[-1].bind("<Enter>", partial(self.show_tip, tip=self.tips[-1]))
            self.labels[-1].bind("<Leave>", partial(self.hide_tip, tip=self.tips[-1]))
            self.params_button.append(
                Scale(
                    root,
                    from_=RANGES[k][0],
                    to=RANGES[k][1],
                    resolution=(RANGES[k][1] - RANGES[k][0]) / 100,
                    showvalue=True,
                    orient="horizontal",
                    command=partial(self.slider_changed, k),
                )
            )
            self.params_button[-1].set(v)
            self.labels[-1].grid(column=(i * 2) % 6, row=i // 3, padx=0, pady=5, sticky="se")
            self.params_button[-1].grid(
                column=(i * 2) % 6 + 1, row=i // 3, padx=(0, 10), pady=5, sticky="nw"
            )

    def show_tip(self, event, tip):
        root = event.widget.master
        while root.master is not None:
            root = root.master
        tip.place(
            x=event.x_root - tip.master.winfo_rootx(),
            y=event.y_root - tip.master.winfo_rooty(),
        )
        tip.tkraise()

    def hide_tip(self, event, tip):
        tip.place_forget()

    def slider_changed(self, key, slider):
        self.observer.change_params(key, float(slider))


class NeuronController:
    def __init__(
        self,
        neuron: IAFCondAlpha,
        view: PlotDisplay,
        current_time: float = 0.0,
        excitatory_weight: float = 100.0,
        inhibitory_weight: float = -100.0,
        syn_delay: float = 0.1,
        display_parameters: bool = False,
        display_controls: bool = False,
        save_values: bool = False,
    ):
        assert syn_delay > 0
        assert inhibitory_weight < 0
        assert excitatory_weight > 0
        self.current_time = current_time
        self.neuron = neuron
        self.plotView = view
        self.controllerView = Frame(view.frame, relief=RIDGE, borderwidth=2)
        self.save_values = save_values
        if self.save_values:
            self.save_file = join(dirname(dirname(abspath(__file__))), f"vm_{uuid4()}.txt")
        if display_controls:
            self.buttonsView = Frame(self.controllerView, relief=RIDGE, borderwidth=2)
            self.stim_controllers = [
                InputController(
                    self.buttonsView, f"{text} Input", color, i, weight, syn_delay, self
                )
                for i, (text, color, weight) in enumerate(
                    zip(
                        ["Excitatory", "Inhibitory"],
                        [EXCITATORY_BLUE, INHIBITORY_RED],
                        [excitatory_weight, inhibitory_weight],
                        strict=False,
                    )
                )
            ]
        else:
            self.stim_controllers = []
        if display_parameters:
            self.paramsView = Frame(self.controllerView, relief=RIDGE, borderwidth=2)
            self.params_controller = NeuronParams(self.paramsView, self.neuron.get_params(), self)

        self.wait_for_key = -1

    def remove_files(self):
        if self.save_values and exists(self.save_file):
            remove(self.save_file)
            self.save_values = False

    def update(self, dt: float):
        spiked = self.neuron.update(self.current_time)
        if self.save_values:
            with open(self.save_file, "a") as f:
                f.write(f"{self.current_time}\t{self.neuron.V_m}\n")
        self.plotView.update(self.current_time, self.neuron.V_m, spike=spiked)
        self.update_keys()
        self.current_time += dt
        return spiked

    def update_keys(self):
        found_waiting = -1
        for i, controller in enumerate(self.stim_controllers):
            controller._delay_button_raise()
            if controller.wait_for_key:
                found_waiting = i
                if self.wait_for_key < 0:
                    self.wait_for_key = i
                elif self.wait_for_key != i:
                    controller.end_wait_for_key()
        if found_waiting < 0 <= self.wait_for_key:
            self.wait_for_key = -1

    def add_key(self, key):
        self.stim_controllers[self.wait_for_key].add_key(key)
        self.wait_for_key = -1

    def reset_add_key(self):
        if self.wait_for_key >= 0:
            self.stim_controllers[self.wait_for_key].end_wait_for_key()
            self.wait_for_key = -1

    def strike(self, key):
        for controller in self.stim_controllers:
            if key in controller.keys:
                controller.stim_input()
                break

    def receive_spike(self, weight: float, delay: float):
        self.neuron.receive_spike(self.current_time, weight, delay)

    def change_params(self, param, value):
        self.neuron.__setattr__(param, value)

    def grid(self, row, column, sticky):
        """
        Put the controller widget on the parent widget.
        """
        self.plotView.grid(row=row, column=column, sticky=sticky)
        self.controllerView.grid(row=1, column=0)  # place CanvasImage widget on the grid
        self.controllerView.grid(sticky=sticky)  # make frame container sticky
        self.controllerView.rowconfigure(0, weight=1)  # make canvas expandable
        self.controllerView.columnconfigure(0, weight=1)
        self.controllerView.columnconfigure(1, weight=2)
        if hasattr(self, "paramsView"):
            self.paramsView.grid(row=0, column=1, sticky=sticky)  # make frame container sticky
        if hasattr(self, "buttonsView"):
            self.buttonsView.grid(row=0, column=0, sticky=sticky)


class GameController:
    def __init__(
        self,
        views: list[PlotDisplay],
        neurons: list[IAFCondAlpha],
        display_parameters: list[bool] = None,
        display_controls: list[bool] = None,
        connectome=None,
        save_values: bool = False,
        simulation_duration: float = -1.0,
        start_paused: bool = False,
    ):
        assert len(views) > 0
        assert len(views) == len(neurons)
        if display_controls is None:
            display_parameters = [True] * len(neurons)
        assert len(display_parameters) == len(neurons)
        if display_controls is None:
            display_controls = [True] * len(neurons)
        assert len(display_controls) == len(neurons)
        if connectome is None:
            connectome = np.zeros((len(neurons), len(neurons)), dtype=float)
        assert connectome.shape == (len(neurons), len(neurons))
        self.connectome = connectome
        self.save_values = save_values

        self.current_time = 0
        self.simulation_duration = simulation_duration
        self.dt = 0.1
        self.is_paused = start_paused

        self.delays = [0.1] * len(neurons)
        for neuron, delay in zip(neurons, self.delays, strict=False):
            neuron.dt = self.dt
            neuron.init_buffers(delay)
        self.weights = [100.0] * len(neurons)
        self.controllers = [
            NeuronController(
                neuron,
                view,
                excitatory_weight=weight,
                inhibitory_weight=-weight,
                display_parameters=show_params,
                display_controls=show_controls,
                save_values=self.save_values,
            )
            for neuron, view, weight, show_params, show_controls in zip(
                neurons, views, self.weights, display_parameters, display_controls, strict=False
            )
        ]
        if len(neurons) > 0:
            root = views[0].frame.master
            self.pause_frame = Frame(root)
            self.pause_frame.tkraise()
            self.pause_frame.rowconfigure(0, weight=1)  # make canvas expandable
            self.pause_frame.columnconfigure(0, weight=1)
            self.time_label = Label(self.pause_frame, text="PAUSE", font=("Arial", 30, "bold"))
            self.time_label.pack(fill=BOTH, expand=True)
        self.wait_for_key = -1
        self.keys = {}

    def cleanup(self):
        self.reset_wait_for_key()
        for controller in self.controllers:
            controller.remove_files()

    def update(self):
        found_waiting = -1
        for i, controller in enumerate(self.controllers):
            if self.is_paused:
                controller.update_keys()
            else:
                spiked = controller.update(self.dt)
                if spiked:
                    for target, weight in enumerate(self.connectome[i]):
                        if np.absolute(weight) >= 1e-3:
                            self.controllers[target].receive_spike(weight, self.delays[target])
            if controller.wait_for_key >= 0:
                found_waiting = True
                if self.wait_for_key != i:
                    if self.wait_for_key >= 0:
                        self.controllers[self.wait_for_key].reset_add_key()
                    self.wait_for_key = i
        if found_waiting < 0 <= self.wait_for_key:
            self.wait_for_key = -1
        self.show_pause()
        if not self.is_paused:
            self.current_time += self.dt
        return 0 < self.simulation_duration <= self.current_time

    def grid(self):
        for i, controller in enumerate(self.controllers):
            column = 1 if i > 0 and i == len(self.controllers) - 1 else i % 2
            controller.grid(row=0, column=column, sticky="nsw" if i == 0 else "nse")

    def reset_wait_for_key(self):
        self.wait_for_key = -1
        for controller in self.controllers:
            controller.reset_add_key()

    def show_pause(self):
        if self.is_paused:
            if self.time_label.config()["text"][-1] != "PAUSE":
                self.time_label.config(text="PAUSE")
            if not self.pause_frame.winfo_viewable():
                sticky = {} if len(self.controllers) <= 1 else {"sticky": "s"}
                self.pause_frame.grid(
                    row=0,
                    column=0,
                    rowspan=1,
                    columnspan=2,
                    **sticky,
                )
        else:
            if self.simulation_duration <= 0.0:
                self.pause_frame.grid_forget()
            else:
                self.time_label.config(
                    text=f"Time left\n{(self.simulation_duration - self.current_time):.1f}"
                )

    def _keystroke(self, event):
        key_stroke = event.char.upper()
        if event.keysym == "space":
            self.is_paused = not self.is_paused
        if not key_stroke.isalnum():
            return
        if self.wait_for_key >= 0 and key_stroke not in self.keys:
            self.keys[key_stroke] = self.wait_for_key
            self.controllers[self.wait_for_key].add_key(key_stroke)
            self.wait_for_key = -1
        elif self.wait_for_key < 0 and not self.is_paused and key_stroke in self.keys:
            self.controllers[self.keys[key_stroke]].strike(key_stroke)
