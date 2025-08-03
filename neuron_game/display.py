from tkinter import Frame

import numpy as np
from matplotlib import pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PlotDisplay:
    def __init__(
        self,
        placeholder,
        points_displayed: int = 50,
        origin_value: float = 0.0,
        dt: float = 0.1,
        ylims: list[float] = None,
        color="blue",
    ):
        self.points_displayed = points_displayed
        self.dt = dt
        self.x = np.arange(-self.points_displayed * dt, -dt + 1e-5, dt).tolist()
        self.y = [origin_value] * self.points_displayed
        self.figure, self.ax = plt.subplots(1, 1, figsize=(10, 4))
        (self.line,) = self.ax.plot(self.x, self.y, color=color)
        self.ax.set_xlim([self.x[0], self.x[-1] + self.points_displayed * dt])
        if ylims is not None:
            self.ax.set_ylim(ylims)
        self.frame = Frame(placeholder)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.spikes = []

    def grid(self, **kw):
        """
        Put CanvasImage widget on the parent widget
        """
        self.frame.grid(**kw)  # place CanvasImage widget on the grid
        self.frame.grid(sticky="nswe")  # make frame container sticky
        self.frame.rowconfigure(0, weight=1)  # make canvas expandable
        self.frame.columnconfigure(0, weight=1)

    def update(self, t: float, new_value: float, spike=False):
        buffer_idx = int(t / self.dt) % self.points_displayed
        self.x[buffer_idx] = t
        self.y[buffer_idx] = new_value
        diplayed_x = self.x[buffer_idx + 1 :] + self.x[: buffer_idx + 1]
        self.line.set_xdata(diplayed_x)
        self.line.set_ydata(self.y[buffer_idx + 1 :] + self.y[: buffer_idx + 1])
        if spike:
            ylims = self.ax.get_ylim()
            line = self.ax.axvline(x=t, ymin=ylims[0], ymax=ylims[1], linewidth=0.5, color="red")
            self.spikes.append((t, line))
        self.ax.set_xlim([diplayed_x[0], diplayed_x[-1] + self.points_displayed * self.dt])
        if len(self.spikes) > 0 and self.spikes[0][0] < diplayed_x[0]:
            _, line = self.spikes.pop(0)
            line.remove()

        self.canvas.draw()
