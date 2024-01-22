# -*- coding: utf-8 -*-
"""
Created on Sun Jan 21 18:16:00 2024

@author: jonathan

Minimal example to plot data from driver using Autolab GUI
"""

import matplotlib.pyplot as plt
import numpy as np


class Driver:

    def __init__(self, gui=None):  # Autolab GUI will detect if put gui=None as argument
        self.gui = gui  # GUI can be Control Panel or Plotter
        # Best to only use createWidget and removeWidget methods from gui to avoid messing with it

        self.fig = None

    def plot_GUI(self):
        x = np.linspace(0, 1000, 1001)
        y = np.random.random(x.shape)
        if self.gui:
            if self.fig is not None and plt.fignum_exists(self.fig.number):
                self.plot.set_data(x, y)
            else:
                # Widgets (plot) needs to be created by gui to have correct connection to thread
                # Need to wait until gui returns a widget because they are created on a different thread
                self.fig = self.gui.createWidget(plt.figure, figsize=(13, 6))

                self.ax = self.fig.add_subplot(111)

                self.plot, = self.ax.plot([], [], alpha=0.8)
                self.plot.set_data(x, y)

            self.ax.relim()
            self.ax.autoscale_view(True, True, True)

            try:
                self.fig.tight_layout()
            except:
                pass

            self.fig.canvas.draw()
        else:
            print("No gui found, skip plot")

    def plot_loop_GUI(self):
        Continue = True
        while Continue:
            self.plot_GUI()
            Continue = plt.fignum_exists(self.fig.number)
        self.fig = None

    def get_driver_model(self):

        config = []

        if self.gui:
            config.append({'element': 'action', 'name': 'plot_in_GUI',
                           'do': self.plot_GUI,
                           "help": "Minimal plot example that work in GUI"})

            config.append({'element': 'action', 'name': 'plot_loop_GUI',
                           'do': self.plot_loop_GUI,
                           "help": "Minimal loop plot example that work in GUI"})

        return config

    def close(self):
            self.gui.removeWidget(self.fig)  # optional but it is nice to remove record from GUI when not used anymore


class Driver_EXAMPLE(Driver):
    def __init__(self, **kwargs):

        Driver.__init__(self, **kwargs)
