from tkinter import LEFT, RAISED, RIDGE, SUNKEN, Button, Frame, Label

from neuron_game.display import PlotDisplay
from neuron_game.iaf_cond_alpha import IAFCondAlpha


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
        sticky = "nw" if column == 0 else "ne"
        self.stim_button.grid(column=column, row=0, padx=10, pady=10, sticky=sticky)
        self.control_button = Button(
            root,
            padx=6,
            bg=color,
            text="Add control",
            command=self.add_control,
        )
        self.control_button.grid(column=column, row=1, padx=10, pady=10, sticky=sticky)
        self.text = Label(root, width=24, height=3, anchor=sticky, justify=LEFT)
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
        self.wait_for_key = True
        self.control_button.config(relief=SUNKEN)

    def _delay_button_raise(self):
        self.stim_button.config(relief=RAISED)
        self.pressed = False


class NeuronController:
    def __init__(
        self,
        neuron: IAFCondAlpha,
        view: PlotDisplay,
        current_time: float = 0.0,
        excitatory_weight: float = 100.0,
        inhibitory_weight: float = -100.0,
        syn_delay: float = 0.1,
    ):
        assert syn_delay > 0
        assert inhibitory_weight < 0
        assert excitatory_weight > 0
        self.current_time = current_time
        self.neuron = neuron
        self.plotView = view
        self.controllerView = Frame(view.frame, relief=RIDGE, borderwidth=2)
        self.stim_controllers = [
            InputController(self.controllerView, f"{text} Input", color, i, weight, syn_delay, self)
            for i, (text, color, weight) in enumerate(
                zip(
                    ["Excitatory", "Inhibitory"],
                    ["#add8e6", "#f1807e"],
                    [excitatory_weight, inhibitory_weight],
                    strict=False,
                )
            )
        ]
        self.wait_for_key = -1

    def update(self, dt: float):
        self.current_time += dt
        spiked = self.neuron.update(self.current_time)
        self.plotView.update(self.current_time, self.neuron.V_m, spike=spiked)
        for i, controller in enumerate(self.stim_controllers):
            controller._delay_button_raise()
            if controller.wait_for_key:
                if self.wait_for_key < 0:
                    self.wait_for_key = i
                elif self.wait_for_key != i:
                    controller.end_wait_for_key()

    def add_key(self, key):
        self.stim_controllers[self.wait_for_key].add_key(key)
        self.wait_for_key = -1

    def reset_add_key(self):
        self.stim_controllers[self.wait_for_key].end_wait_for_key()
        self.wait_for_key = -1

    def strike(self, key):
        for controller in self.stim_controllers:
            if key in controller.keys:
                controller.stim_input()
                break

    def receive_spike(self, weight: float, delay: float):
        self.neuron.receive_spike(self.current_time, weight, delay)

    def grid(self, **kw):
        """
        Put the controller widget on the parent widget.
        """
        self.plotView.frame.grid(**kw)

        self.plotView.canvas.get_tk_widget().grid(row=0, column=0)
        self.plotView.canvas.get_tk_widget().grid(sticky="nswe")
        self.plotView.canvas.get_tk_widget().rowconfigure(0, weight=1)
        self.plotView.canvas.get_tk_widget().columnconfigure(0, weight=1)

        self.controllerView.grid(row=1, column=0)  # place CanvasImage widget on the grid
        self.controllerView.grid(sticky="nw")  # make frame container sticky
        self.controllerView.rowconfigure(0, weight=1)  # make canvas expandable
        self.controllerView.columnconfigure(0, weight=1)


class GameController:
    def __init__(self, views: list[PlotDisplay], neurons: list[IAFCondAlpha]):
        assert len(views) > 0
        assert len(views) == len(neurons)
        self.current_time = 0
        self.dt = 0.1
        self.delays = [0.1] * len(neurons)
        for neuron, delay in zip(neurons, self.delays, strict=False):
            neuron.dt = self.dt
            neuron.init_buffers(delay)
        self.weights = [100.0] * len(neurons)
        self.controllers = [
            NeuronController(neuron, view, excitatory_weight=weight, inhibitory_weight=-weight)
            for neuron, view, weight in zip(neurons, views, self.weights, strict=False)
        ]
        self.wait_for_key = -1
        self.keys = {}

    def update(self):
        for i, controller in enumerate(self.controllers):
            controller.update(self.dt)
            if controller.wait_for_key >= 0 and self.wait_for_key != i:
                if self.wait_for_key >= 0:
                    self.controllers[self.wait_for_key].reset_add_key()
                self.wait_for_key = i

        self.current_time += self.dt

    def grid(self):
        for i, controller in enumerate(self.controllers):
            controller.grid(row=0, column=i)

    def _keystroke(self, event):
        key_stroke = event.char.upper()
        if self.wait_for_key >= 0 and key_stroke not in self.keys:
            self.keys[key_stroke] = self.wait_for_key
            self.controllers[self.wait_for_key].add_key(key_stroke)
            self.wait_for_key = -1
        elif self.wait_for_key < 0 and key_stroke in self.keys:
            self.controllers[self.keys[key_stroke]].strike(key_stroke)
