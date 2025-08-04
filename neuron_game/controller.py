import threading
import time
from tkinter import RAISED, RIDGE, SUNKEN, Button, Frame

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
        syn_delay: float = 2.0,
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
            bg="blue",
            text="Excitatory Input",
            command=self.excitatory_input,
        )
        self.exc_button.grid(column=0, row=0, padx=10, pady=10, sticky="nw")
        self.excitatory_weight = excitatory_weight
        self.inh_button = Button(
            self.controllerView,
            padx=6,
            bg="red",
            text="Inhibitory Input",
            command=self.inhibitory_input,
        )
        self.inh_button.grid(column=1, row=0, padx=10, pady=10, sticky="w")
        self.inhibitory_weight = inhibitory_weight
        self.syn_delay = syn_delay
        self.pressed = False

    def update(self, dt: float):
        self.current_time += dt
        spiked = self.neuron.update(self.current_time)
        self.plotView.update(self.current_time, self.neuron.V_m, spike=spiked)

    def _delay_button_raise(self, button):
        time.sleep(0.1)
        button.config(relief=RAISED)
        self.pressed = False

    def excitatory_input(self):
        if not self.pressed:
            self.pressed = True
            self.exc_button.config(relief=SUNKEN)
            self.receive_spike(self.excitatory_weight, self.syn_delay)
            thread = threading.Thread(target=self._delay_button_raise, args=(self.exc_button,))
            thread.start()

    def inhibitory_input(self):
        if not self.pressed:
            self.pressed = True
            self.inh_button.config(relief=SUNKEN)
            self.receive_spike(self.inhibitory_weight, self.syn_delay)
            thread = threading.Thread(target=self._delay_button_raise, args=(self.inh_button,))
            thread.start()

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
        assert len(views) == len(neurons)
        self.current_time = 0
        self.dt = 0.1
        self.delays = [2.0] * len(neurons)
        for neuron, delay in zip(neurons, self.delays, strict=False):
            neuron.dt = self.dt
            neuron.init_buffers(delay)
        self.weights = [100.0] * len(neurons)
        self.controllers = [
            NeuronController(neuron, view, excitatory_weight=weight, inhibitory_weight=-weight)
            for neuron, view, weight in zip(neurons, views, self.weights, strict=False)
        ]

    def update(self):
        for controller in self.controllers:
            controller.update(self.dt)
        self.current_time += self.dt

    def grid(self):
        for i, controller in enumerate(self.controllers):
            controller.grid(row=0, column=i)
