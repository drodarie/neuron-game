from tkinter import END, RAISED, RIDGE, SUNKEN, Button, Frame, Text

from neuron_game.display import PlotDisplay
from neuron_game.iaf_cond_alpha import IAFCondAlpha


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

        self.exc_button = Button(
            self.controllerView,
            padx=6,
            bg="#add8e6",
            text="Excitatory Input",
            command=self.excitatory_input,
        )
        self.exc_button.grid(column=0, row=0, padx=10, pady=10, sticky="nw")
        self.excitatory_weight = excitatory_weight
        self.inh_button = Button(
            self.controllerView,
            padx=6,
            bg="#f1807e",
            text="Inhibitory Input",
            command=self.inhibitory_input,
        )
        self.inh_button.grid(column=1, row=0, padx=10, pady=10, sticky="ne")
        self.left_control_button = Button(
            self.controllerView,
            padx=6,
            bg="#add8e6",
            text="Add exc. control",
            command=self.add_exc_control,
        )
        self.left_control_button.grid(column=0, row=1, padx=10, pady=10, sticky="nw")
        self.right_control_button = Button(
            self.controllerView,
            padx=6,
            bg="#f1807e",
            text="Add inh. control",
            command=self.add_inh_control,
        )
        self.right_control_button.grid(column=1, row=1, padx=10, pady=10, sticky="ne")
        self.texts = [Text(self.controllerView, width=24, height=3) for _ in range(2)]
        self.texts[0].grid(column=0, row=2, padx=10, sticky="nw")
        self.texts[1].grid(column=1, row=2, padx=10, sticky="ne")
        self.inhibitory_weight = inhibitory_weight
        self.syn_delay = syn_delay
        self.pressed = None
        self.keys = [[], []]
        self.wait_for_key = -1

    def update(self, dt: float):
        self.current_time += dt
        spiked = self.neuron.update(self.current_time)
        self.plotView.update(self.current_time, self.neuron.V_m, spike=spiked)
        if self.pressed is not None:
            self._delay_button_raise(self.pressed)

    def _delay_button_raise(self, button):
        button.config(relief=RAISED)
        self.pressed = None

    def add_exc_control(self):
        if self.pressed is None and self.wait_for_key < 0:
            self.pressed = self.left_control_button
            self.left_control_button.config(relief=SUNKEN)
            self.wait_for_key = 0

    def add_inh_control(self):
        if self.pressed is None and self.wait_for_key < 0:
            self.pressed = self.right_control_button
            self.right_control_button.config(relief=SUNKEN)
            self.wait_for_key = 1

    def add_key(self, key):
        self.keys[self.wait_for_key].append(key)
        self.texts[self.wait_for_key].delete("1.0", END)
        self.texts[self.wait_for_key].insert(END, ", ".join(self.keys[self.wait_for_key]))
        self.wait_for_key = -1

    def strike(self, key):
        if key in self.keys[0]:
            self.excitatory_input()
        elif key in self.keys[1]:
            self.inhibitory_input()

    def excitatory_input(self):
        if self.pressed is None:
            self.pressed = self.exc_button
            self.exc_button.config(relief=SUNKEN)
            self.receive_spike(self.excitatory_weight, self.syn_delay)

    def inhibitory_input(self):
        if self.pressed is None:
            self.pressed = self.inh_button
            self.inh_button.config(relief=SUNKEN)
            self.receive_spike(self.inhibitory_weight, self.syn_delay)

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
                    self.controllers[self.wait_for_key].wait_for_key = -1
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
