from tkinter import Frame

import numpy as np
from matplotlib import gridspec
from matplotlib import pylab as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PlotDisplay:
    def __init__(
        self,
        placeholder,
        points_displayed: int = 50,
        origin_values=None,
        titles=None,
        dt: float = 0.1,
        ylims: list[float] = None,
        color="blue",
    ):
        if titles is None:
            titles = ["Neuron"]
        if origin_values is None:
            origin_values = [0.0]
        assert len(origin_values) == len(titles)
        self.frame = Frame(placeholder)

        self.points_displayed = points_displayed
        self.dt = dt
        self.x = np.arange(-self.points_displayed * dt, -dt + 1e-5, dt)
        self.y = np.full(
            (len(origin_values), self.points_displayed), np.array(origin_values)[..., np.newaxis]
        )

        nb_rows = (len(origin_values) // 2 + 1) * 3 + 1
        nb_cols = 3 if len(origin_values) < 2 else 7
        self.figure = plt.figure(
            figsize=(9.7 * (1 if len(origin_values) < 2 else 2), 1.5 * nb_rows)
        )
        self.gs0 = gridspec.GridSpec(nb_rows, nb_cols, figure=self.figure)

        self.axes = []
        self.lines = []
        hidden_ax = self.figure.add_subplot(self.gs0[:, :])
        hidden_ax.axis("off")
        for i, title in enumerate(titles):
            if i > 0:
                idx = (i // 2) * 4
                idy = (i % 2) * 4
                if i % 2 == 0 and i == len(titles) - 1:
                    idy = 2
                ax = self.figure.add_subplot(
                    self.gs0[idx : idx + 2, idy : idy + 3], sharex=self.axes[0], sharey=self.axes[0]
                )
            else:
                ax = self.figure.add_subplot(self.gs0[:2, :3])
                ax.set_xlim([self.x[0], self.x[-1] + self.points_displayed * dt])
                if ylims is not None:
                    ax.set_ylim(ylims)

            plt.setp(ax.get_xticklabels(), ha="right")
            ax.set_title(title)

            ax.set_ylabel("Membrane potential (mV)")
            ax.set_xlabel("Time (ms)")
            self.axes.append(ax)
            self.lines.append(ax.plot(self.x, self.y[i], color=color, linewidth=2.0)[0])

        self.figure.set_tight_layout(True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.spikes = [[]] * len(origin_values)

    def grid(self, **kw):
        """
        Put CanvasImage widget on the parent widget
        """
        self.frame.grid(**kw)  # place CanvasImage widget on the grid
        self.frame.grid(sticky="nswe")  # make frame container sticky
        self.frame.rowconfigure(0, weight=1)  # make canvas expandable
        self.frame.columnconfigure(0, weight=1)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nswe")

    def update(self, t: float, new_values: list[float], spikes: list[bool]):
        buffer_idx = int(np.round(t / self.dt)) % self.points_displayed
        self.x[buffer_idx] = t
        self.y[:, buffer_idx] = new_values
        displayed_x = np.roll(self.x, -buffer_idx - 1)

        self.axes[0].set_xlim([displayed_x[0], t + self.points_displayed * self.dt])
        for i, (line, y, spike) in enumerate(zip(self.lines, self.y, spikes, strict=False)):
            line.set_xdata(displayed_x)
            line.set_ydata(np.roll(y, -buffer_idx - 1))
            if spike:
                vline = self.axes[i].axvline(x=t, linewidth=2.0, color="red")
                self.spikes[i].append((t, vline))
            if len(self.spikes[i]) > 0 and self.spikes[i][0][0] < displayed_x[0]:
                _, vline = self.spikes[i].pop(0)
                vline.remove()

        self.canvas.draw()
