"""
Description: This script is the implementation of the Real-time plotting function if openSVP. Therefore, you can find
his GUI creation, how does it access to data and everything

note :
The link between this module and ui.py is situated in the op_run method of the EntityTreeEntry Class
"""

import os
import wx
import pandas as pd

import matplotlib
import json

matplotlib.use('WXAgg')
from matplotlib import lines
from matplotlib.figure import Figure
from matplotlib.figure import Axes
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas
import numpy as np
import pylab
import seaborn as sns
import time
import ctypes


info_values = {
    'Single phase': ['1'],
    'Three phase': ['1', '2', '3']

}
X_POINTS = list(np.arange(55, 155, 1))

Y1_CURVES = [
    [140] * 25 + list(np.arange(140, 290, 3)) + [290] * 25,
    [290] * 25 + list(np.arange(290, 140, -3)) + [140] * 25,
    list(500 * np.sin(np.deg2rad([e * 3.6 for e in X_POINTS]))),
    list(np.arange(100, 400, 3)),
    list(np.arange(400, 100, -3)),
    [100]*50 + [200]*50,
    [400]*33 + [350]*34 + [300]*33,
    list(250 * np.sin(np.deg2rad([e * 3.6 for e in X_POINTS])) + 250),
    [((e - 55)/4) ** 2 for e in X_POINTS],
    [((e - 55)/12) ** 3 for e in X_POINTS]
]

Y_COLORS = ['Black',
            'Red',
            'Blue',
            'Green',
            'Cyan',
            'Magenta',
            'brown',
            'purple',
            'gray',
            'olive'
]

XY_X_POINTS = [90, 91, 92, 93, 95, 97, 98, 99, 100, 102, 103, 105, 106, 108, 110, 112]

XY_Y_POINTS = [
    [44, 44, 44, 44, 29, 11, 6, 1, 0, -2, -10, -26, -36, -44, -44, -44],
    [-44, -44, -44, -44, -36, -26, -10, -2, 0, 1, 6, 11, 29, 44, 44, 44],
    [44, 44, 44, 44, 44, 44, 44, 43, 45, 44, 46, 44, 45, 47, 44, 44],
    [-44, -41, -44, -44, -44, -44, -45, -45, -44, -47, -46, -44, -44, -41, -42, -44],
    [50, 50, 50, 50, 50, 50, 50, 50, 43.75, 37.5, 31.25, 25, 18.75, 12.5, 6.25, 0],
    [43.75, 37.5, 31.25, 25, 18.75, 12.5, 6.25, 0, -6.25, -12.50, -18.75, -25, -31.25, -37.5, -43.75, -50],
    [-50, -43.75, -37.5, -31.25, -25, -18.75, -12.5, -6.25, 0, 6.25, 12.50, 18.75, 25, 31.25, 37.5, 43.75],
    [15, 15, 11.66, 8.33, 5, 5, 5, 1.66, -1.66, -5, -5, -5, -8.33, -11.66, -15, -15],
    [5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    [-5, -5, -5, -5, -5, -5, -5, -5, -5, -5, -5, -5, -5, -5, -5, -5],
]

MARKER = [
    '.',
    'o',
    '^',
    '2',
    '8',
    's',
    'p',
    '*',
    'D',
    'P'
]

NOMINAL = {
    'AC_VRMS': 'der.v_nom',
    'AC_FREQ': 'der.f_nom',
    'AC_Q': 'der.var_rated',
    'AC_P': 'der.p_rated',
    'AC_S': 'der.s_rated'
}

NOMENCLATURE = {
    'V': 'AC_VRMS',
    'I': 'AC_IRMS',
    'P': 'AC_P',
    'S': 'AC_S',
    'Q': 'AC_Q',
    'PF': 'AC_PF',
    'F': 'AC_FREQ'
}


class Preference_canvas(FigCanvas):
    def __init__(self, panel=wx.Panel, size=(0, 0), title='tab'):
        height = 1*size[1]/400
        width = 2*size[0]/300
        self.pref_figure = Figure(figsize=(width, height))
        FigCanvas.__init__(self, panel, -1, self.pref_figure)
        self.second_axes = None
        self.title = title
        self.nbr_of_plots = 0
        sns.set_theme(style='darkgrid')

    def Create_Figure(self, type=None, parameters={}):

        self.type = type
        self.parameters = parameters

        if self.type == 'Time-based':
            self.Time_based_Figure()
        elif self.type == 'XY':
            self.XY_Figure()

    def Time_based_Figure(self):

        self.axes = self.pref_figure.add_subplot(111)
        self.axes.set_title(self.title)
        self.axes.set_ylabel(self.parameters['Y1 axis title'])
        self.axes.set_xlabel(self.parameters['X axis title'])
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        self.axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))

        if self.parameters['Y2 axis value'] != 'Disabled':
            self.second_axes = self.axes.twinx()
            self.second_axes.set_ylabel(self.parameters['Y2 axis title'])
            pylab.setp(self.second_axes.get_yticklabels(), fontsize=8)
            self.second_axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))

        self.axes.grid(self.parameters['Grid'] == 'True')
        self.Time_based_refresh_lines_axes()

        if self.parameters['Y2 axis value'] != 'Disabled':
            self.Time_based_refresh_lines_second_axes()

    def Time_based_add_second_axes(self):
        self.second_axes = self.axes.twinx()
        self.second_axes.set_ylabel(self.parameters['Y2 axis title'])
        pylab.setp(self.second_axes.get_yticklabels(), fontsize=8)
        self.second_axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))
        self.Time_based_refresh_lines_second_axes()
        self.pref_figure.tight_layout()
        self.draw()

    def Time_based_refresh_lines_axes(self):

        for line in self.axes.get_lines():
            line.remove()
            self.nbr_of_plots -= 1
        specific_values = self.parameters['Y1 axis specific value']

        if self.parameters['Y2 axis value'] != 'Disabled':
            for line in self.second_axes.get_lines():
                line.remove()
                self.nbr_of_plots -= 1

        for specific_value in specific_values:
            if specific_values[specific_value] == 'True':
                plot = lines.Line2D(X_POINTS,
                                    Y1_CURVES[self.nbr_of_plots],
                                    color=Y_COLORS[self.nbr_of_plots],
                                    label=specific_value
                                    )
                self.axes.add_line(plot)
                self.nbr_of_plots += 1
                if self.nbr_of_plots >= 10:
                    print('The limit of 10 signal has been exceeded')
        if self.parameters['Legend'] == 'True':
            lns = self.axes.get_lines()
            if self.second_axes:
                lns += self.second_axes.get_lines()
            labels = [l.get_label() for l in lns]
            self.axes.legend(lns, labels, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        self.axes.relim()
        self.axes.autoscale()
        self.pref_figure.tight_layout()
        self.draw()

        if self.parameters['Y2 axis value'] != 'Disabled':
            self.Time_based_refresh_lines_second_axes()

    def Time_based_refresh_lines_second_axes(self):
        for line in self.second_axes.get_lines():
            line.remove()
            self.nbr_of_plots -= 1
        specific_values = self.parameters['Y2 axis specific value']

        for specific_value in specific_values:
            if specific_values[specific_value] == 'True':
                plot = lines.Line2D(X_POINTS,
                                    [e * 10 for e in Y1_CURVES[self.nbr_of_plots]],
                                    color=Y_COLORS[self.nbr_of_plots],
                                    label=specific_value
                                    )
                self.second_axes.add_line(plot)
                self.nbr_of_plots += 1
                if self.nbr_of_plots >= 10:
                    print('The limit of 10 signal has been exceeded')
        if self.parameters['Legend'] == 'True':
            lns = self.axes.get_lines()
            lns += self.second_axes.get_lines()
            labels = [l.get_label() for l in lns]
            self.axes.legend(lns, labels, bbox_to_anchor=(1.20, 1), loc=2, borderaxespad=0.)

        self.second_axes.autoscale()
        self.second_axes.grid(None)
        self.pref_figure.tight_layout()
        self.draw()

    def Time_based_refresh_legend(self):
        lns = self.axes.get_lines()
        if self.parameters['Y2 axis value'] != 'Disabled':
            lns += self.second_axes.get_lines()
        labels = [l.get_label() for l in lns]
        self.axes.legend(lns, labels, bbox_to_anchor=(1.20, 1), loc=2, borderaxespad=0.)

    def XY_Figure(self):
        self.axes = self.pref_figure.add_subplot(111)
        self.axes.set_title(self.title)
        self.axes.set_ylabel(self.parameters['Y1 axis title'])
        self.axes.set_xlabel(self.parameters['X axis title'])
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        self.axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))

        if self.parameters['Y2 axis value'] != 'Disabled':
            self.second_axes = self.axes.twinx()
            self.second_axes.set_ylabel(self.parameters['Y2 axis title'])
            pylab.setp(self.second_axes.get_yticklabels(), fontsize=8)
            self.second_axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))

        self.XY_refresh_lines_axes()

        if self.parameters['Y2 axis value'] != 'Disabled':
            self.XY_refresh_lines_second_axes()

    def XY_add_second_axes(self):
        self.second_axes = self.axes.twinx()
        self.second_axes.set_ylabel(self.parameters['Y2 axis title'])
        pylab.setp(self.second_axes.get_yticklabels(), fontsize=8)
        self.second_axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))
        self.XY_refresh_lines_second_axes()
        self.pref_figure.tight_layout()
        self.draw()

    def XY_refresh_lines_axes(self):

        for line in self.axes.get_lines():
            line.remove()
            self.nbr_of_plots -= 1
        specific_values = self.parameters['Y1 axis specific value']

        if self.parameters['Y2 axis value'] != 'Disabled':
            for line in self.second_axes.get_lines():
                line.remove()
                self.nbr_of_plots -= 1


        for specific_value in specific_values:
            if specific_values[specific_value] == 'True':
                plot = lines.Line2D(XY_X_POINTS,
                                    XY_Y_POINTS[self.nbr_of_plots],
                                    linewidth=0,
                                    marker=MARKER[self.nbr_of_plots],
                                    color=Y_COLORS[self.nbr_of_plots],
                                    label=specific_value
                                    )
                self.axes.add_line(plot)
                self.nbr_of_plots += 1
                if self.nbr_of_plots >= 10:
                    print('The limit of 10 signal has been exceeded')
        if self.parameters['Legend'] == 'True':
            lns = self.axes.get_lines()
            if self.second_axes:
                lns += self.second_axes.get_lines()
            labels = [l.get_label() for l in lns]
            self.axes.legend(lns, labels, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        self.axes.grid(self.parameters['Grid'] == 'True')
        self.axes.relim()
        self.axes.autoscale()
        self.pref_figure.tight_layout()
        self.draw()

        if self.parameters['Y2 axis value'] != 'Disabled':
            self.XY_refresh_lines_second_axes()

    def XY_refresh_lines_second_axes(self):
        for line in self.second_axes.get_lines():
            line.remove()
            self.nbr_of_plots -= 1
        specific_values = self.parameters['Y2 axis specific value']

        for specific_value in specific_values:
            if specific_values[specific_value] == 'True':
                plot = lines.Line2D(XY_X_POINTS,
                                    [e * 10 for e in XY_Y_POINTS[self.nbr_of_plots]],
                                    linewidth=0,
                                    marker=MARKER[self.nbr_of_plots],
                                    color=Y_COLORS[self.nbr_of_plots],
                                    label=specific_value
                                    )
                self.second_axes.add_line(plot)
                self.nbr_of_plots += 1
                if self.nbr_of_plots >= 10:
                    print('The limit of 10 signal has been exceeded')
        if self.parameters['Legend'] == 'True':
            lns = self.axes.get_lines()
            lns += self.second_axes.get_lines()
            labels = [l.get_label() for l in lns]
            self.axes.legend(lns, labels, bbox_to_anchor=(1.20, 1), loc=2, borderaxespad=0.)

        self.axes.grid(self.parameters['Grid'] == 'True')
        self.second_axes.autoscale()
        self.second_axes.grid(None)
        self.pref_figure.tight_layout()
        self.draw()

    def XY_refresh_legend(self):
        lns = self.axes.get_lines()
        if self.parameters['Y2 axis value'] != 'Disabled':
            lns += self.second_axes.get_lines()
        labels = [l.get_label() for l in lns]
        self.axes.legend(lns, labels, bbox_to_anchor=(1.20, 1), loc=2, borderaxespad=0.)

class Time_based_plot:
    """
    Class representing a single time-based plot
    """
    def __init__(self, figure=None, configName=None, configFile=None, params=None):
        self.figure = figure
        self.configName = configName
        self.configFile = configFile
        self.params = params
        sns.set_theme(style='darkgrid')
        self.axes = self.figure.add_subplot(int(self.configFile['MainTab']['Row']),
                                             int(self.configFile['MainTab']['Column']), int(self.configName[-1]) + 1)

        self.second_axes = None
        self.lines = None
        self.ynom = []
        self.axes_init()
        self.last_index = 0
        self.x = []
        self.ymin = 0.0
        self.ymax = 0.0
        self.y2min = 0.0
        self.y2max = 0.0
        self.time_window_active = self.configFile[configName]['Time-based']['Time display option'] == 'Specific time window (s)'
        self.time_window = float(self.configFile[configName]['Time-based']['Time window'])
        sample_interval = [value for key, value in self.params.items() if 'sample_interval' in key][0]
        self.sample_per_time_window = int(round(self.time_window * 1000 / sample_interval))

    def axes_init(self):
        self.axes.set_title(self.configFile[self.configName]['Plot title'])
        self.axes.set_xlabel(self.configFile[self.configName]['Time-based']['X axis title'])
        self.axes.set_ylabel(self.configFile[self.configName]['Time-based']['Y1 axis title'])
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        self.axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))

        specific_values = self.configFile[self.configName]['Time-based']['Y1 axis specific value']
        i = 0
        for specific_value in specific_values:
            if specific_values[specific_value] == 'True':
                plot = lines.Line2D([0],
                                    [0],
                                    color=Y_COLORS[i],
                                    label=specific_value
                                    )
                self.axes.add_line(plot)
                i += 1

        self.axes.relim()
        self.axes.autoscale()
        if self.configFile[self.configName]['Time-based']['Y2 axis value'] != 'Disabled':
            self.second_axes = self.axes.twinx()
            self.second_axes.set_ylabel(self.configFile[self.configName]['Time-based']['Y2 axis title'])
            pylab.setp(self.second_axes.get_yticklabels(), fontsize=8)
            self.second_axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))
            specific_values = self.configFile[self.configName]['Time-based']['Y2 axis specific value']
            for specific_value in specific_values:
                if specific_values[specific_value] == 'True':
                    plot = lines.Line2D([0],
                                        [0],
                                        color=Y_COLORS[i],
                                        label=specific_value
                                        )
                    self.second_axes.add_line(plot)
                    i += 1

        self.lines = self.axes.get_lines()
        if self.second_axes:
            self.lines += self.second_axes.get_lines()
        if self.configFile[self.configName]['Time-based']['Legend'] == 'True':
            labels = [l.get_label() for l in self.lines]
            self.axes.legend(self.lines, labels, bbox_to_anchor=(1.1, 1), loc=2, borderaxespad=0.)

        for line in self.lines:
            y_line_name = line.get_label()
            if y_line_name[:-2] in ['AC_VRMS', 'AC_FREQ', 'AC_Q', 'AC_P', 'AC_S']:
                self.ynom.append(self.params[NOMINAL[y_line_name[:-2]]])
            elif y_line_name[:-2] == 'AC_IRMS':
                self.ynom.append(self.params[NOMINAL['AC_S']]/self.params[NOMINAL['AC_VRMS']])
            elif y_line_name[:-2] == 'AC_PF':
                self.ynom.append(1.00)


    def get_type(self):

        return self.configFile[self.configName]['Plot type']

    def data_update(self, data=None):

        for i in range(self.last_index, len(data)):
            self.x.append((data.index[i] - data.index[0]))
        self.last_index = len(data)

        if self.x[-1] - self.x[0] > self.time_window and self.time_window_active:
            xmin = self.x[-1] - self.time_window
        else:
            xmin = 0

        i = 0

        for line in self.axes.get_lines():
            y_line_name = line.get_label()
            if self.time_window_active is False or self.x[-1] - self.x[0] < self.time_window:
                if data[y_line_name].values[-1] < self.ymin +  0.1 * self.ynom[i] or self.ymin == 0.0:
                    self.ymin = data[y_line_name].values[-1] - 0.1 * self.ynom[i]
                if data[y_line_name].values[-1] > self.ymax - 0.1 *self.ynom[i] or self.ymax == 0.0:
                    self.ymax = data[y_line_name].values[-1] + 0.1 * self.ynom[i]
            else:
                new_ymin = min(data[y_line_name].values[-self.sample_per_time_window:]) - 0.1 * self.ynom[i]
                new_ymax = max(data[y_line_name].values[-self.sample_per_time_window:]) + 0.1 * self.ynom[i]
                if self.lines.index(line) == 0 or new_ymin < self.ymin:
                    self.ymin = new_ymin
                if  self.lines.index(line) == 0 or new_ymax > self.ymax:
                    self.ymax = new_ymax
            i += 1

            line.set_xdata(np.array(self.x))
            line.set_ydata(data[y_line_name].values)
        if np.isinf(self.ymin) or np.isnan(self.ymin):
            self.ymin = 0.0
        if np.isinf(self.ymax) or np.isnan(self.ymax):
            self.ymax = 0.0
        self.axes.set_xbound(lower=xmin, upper=self.x[-1] + 0.01)
        self.axes.set_ybound(lower=self.ymin, upper=self.ymax)

        if self.second_axes:
            for line in self.second_axes.get_lines():
                y_line_name = line.get_label()
                if self.time_window_active is False or self.x[-1] - self.x[0] < self.time_window:
                    if data[y_line_name].values[-1] < self.y2min + 0.1 * self.ynom[i] or self.y2min == 0.0:
                        self.y2min = data[y_line_name].values[-1] - 0.1 * self.ynom[i]
                    if data[y_line_name].values[-1] > self.y2max - 0.1 * self.ynom[i] or self.y2max == 0.0:
                        self.y2max = data[y_line_name].values[-1] + 0.1 * self.ynom[i]
                else:
                    new_ymin = min(data[y_line_name].values[-self.sample_per_time_window:]) - 0.1 * self.ynom[i]
                    new_ymax = max(data[y_line_name].values[-self.sample_per_time_window:]) + 0.1 * self.ynom[i]
                    if self.lines.index(line) == 0 or new_ymin < self.y2min:
                        self.y2min = new_ymin
                    if self.lines.index(line) == 0 or new_ymax > self.y2max:
                        self.y2max = new_ymax
                i += 1

                line.set_xdata(np.array(self.x))
                line.set_ydata(data[y_line_name].values)

            if np.isinf(self.y2min) or np.isnan(self.y2min):
                self.y2min = 0.0
            if np.isinf(self.y2max) or np.isnan(self.y2max):
                self.y2max = 0.0
            self.second_axes.set_ybound(lower=self.y2min, upper=self.y2max)



class XY_plot:
    """
    Class representing a single XY plot
    """

    def __init__(self, figure=None, configName=None, configFile=None, params=None):
        self.figure = figure
        self.configName = configName
        self.configFile = configFile
        self.params = params
        sns.set_theme(style='darkgrid')
        self.axes = self.figure.add_subplot(int(self.configFile['MainTab']['Row']),
                                             int(self.configFile['MainTab']['Column']), int(self.configName[-1]) + 1)
        self.second_axes = None
        self.lines = None
        self.ynom = []
        self.xnom = 0.0
        self.axes_init()
        self.xmax = 0.0
        self.xmin = 0.0
        self.y1_max = 0.0
        self.y1_min = 0.0
        self.y2_max = 0.0
        self.y2_min = 0.0

    def axes_init(self):
        self.axes.set_title(self.configFile[self.configName]['Plot title'])
        self.axes.set_xlabel(self.configFile[self.configName]['XY']['X axis title'])
        self.axes.set_ylabel(self.configFile[self.configName]['XY']['Y1 axis title'])
        pylab.setp(self.axes.get_xticklabels(), fontsize=8)
        pylab.setp(self.axes.get_yticklabels(), fontsize=8)
        self.axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))

        specific_values = self.configFile[self.configName]['XY']['Y1 axis specific value']
        i = 0
        for specific_value in specific_values:
            if specific_values[specific_value] == 'True':
                plot = lines.Line2D([],
                                    [],
                                    linewidth=0,
                                    marker=MARKER[i],
                                    color=Y_COLORS[i],
                                    label=specific_value
                                    )
                self.axes.add_line(plot)
                i += 1

        self.axes.relim()
        self.axes.autoscale()
        if self.configFile[self.configName]['XY']['Y2 axis value'] != 'Disabled':
            self.second_axes = self.axes.twinx()
            self.second_axes.set_ylabel(self.configFile[self.configName]['XY']['Y2 axis title'])
            pylab.setp(self.second_axes.get_yticklabels(), fontsize=8)
            self.second_axes.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(11))
            specific_values = self.configFile[self.configName]['XY']['Y2 axis specific value']
            for specific_value in specific_values:
                if specific_values[specific_value] == 'True':
                    plot = lines.Line2D([],
                                        [],
                                        linewidth=0,
                                        marker=MARKER[i],
                                        color=Y_COLORS[i],
                                        label=specific_value
                                        )
                    self.second_axes.add_line(plot)
                    i += 1

        self.lines = self.axes.get_lines()
        if self.second_axes:
            self.lines += self.second_axes.get_lines()
        if self.configFile[self.configName]['XY']['Legend'] == 'True':
            labels = [l.get_label() for l in self.lines]
            self.axes.legend(self.lines, labels, bbox_to_anchor=(1.1, 1), loc=2, borderaxespad=0.)

        for line in self.lines:
            y_line_name = line.get_label()
            if y_line_name[:-2] in ['AC_VRMS', 'AC_FREQ', 'AC_Q', 'AC_P', 'AC_S']:
                self.ynom.append(self.params[NOMINAL[y_line_name[:-2]]])
            elif y_line_name[:-2] == 'AC_IRMS':
                self.ynom.append(self.params[NOMINAL['AC_S']] / self.params[NOMINAL['AC_VRMS']])
            elif y_line_name[:-2] == 'AC_PF':
                self.ynom.append(1.00)
        x_value_name = self.configFile[self.configName]['XY']['X axis value']
        if x_value_name in ['V', 'F', 'Q', 'P', 'S']:
            self.xnom = self.params[NOMINAL[NOMENCLATURE[x_value_name]]]
        elif x_value_name == 'I':
            self.xnom = self.params[NOMINAL[NOMENCLATURE[x_value_name]]] / self.params[NOMINAL[NOMENCLATURE[x_value_name]]]
        elif x_value_name == 'PF':
            self.xnom = 1.00

    def get_type(self):

        return self.configFile[self.configName]['Plot type']

    def data_update(self, data=None, event_column_name=''):
        # formatting the dataframe depending on the filter and duplicate options
        indexs = None
        if self.configFile[self.configName]['XY']['filters']:
            for filter in self.configFile[self.configName]['XY']['filters']:
                if data[event_column_name].dtype == float:
                    indexs = None
                    pass
                else:
                    if indexs is None:
                        indexs = data[event_column_name].str.contains(filter, regex=True)
                        indexs = indexs.fillna(False)
                    else:
                        new_indexs = data[event_column_name].str.contains(filter, regex=True)
                        new_indexs = new_indexs.fillna(False)
                        indexs = new_indexs | indexs
            if indexs is None:
                data = pd.DataFrame()
            else:
                data = data[indexs]

        if self.configFile[self.configName]['XY']['Remove duplicates'] == 'True':
            data = data.drop_duplicates(subset=event_column_name, keep='first', inplace=False).reset_index(drop=True)

        #Determining the plots boundaries:

        if data.empty is False:
            i = 0
            for line in self.axes.get_lines():
                y_line_name = line.get_label()
                if data[y_line_name].values[-1] / self.ynom[i] < self.y1_min + 0.05 or self.y1_min == 0.0:
                    self.y1_min = data[y_line_name].values[-1] / self.ynom[i] - 0.1
                if data[y_line_name].values[-1] / self.ynom[i] > self.y1_max - 0.05 or self.y1_max == 0.0:
                    self.y1_max = data[y_line_name].values[-1] / self.ynom[i] + 0.1
                x_line_name = NOMENCLATURE[self.configFile[self.configName]['XY']['X axis value']] + y_line_name[-2:]
                if data[x_line_name].values[-1] / self.xnom < self.xmin + 0.05 or self.xmin == 0.0:
                    self.xmin = data[x_line_name].values[-1] / self.xnom - 0.1
                if data[x_line_name].values[-1] / self.xnom > self.xmax - 0.05 or self.xmax == 0.0:
                    self.xmax = data[x_line_name].values[-1] / self.xnom + 0.1

                line.set_xdata(data[x_line_name].values / self.xnom)
                line.set_ydata(data[y_line_name].values / self.ynom[i])

                i += 1
            if np.isinf(self.y1_min) or np.isnan(self.y1_min):
                self.y1_min = 0.0
            if np.isinf(self.y1_max) or np.isnan(self.y1_max):
                self.y1_max = 0.0
            if np.isinf(self.xmin) or np.isnan(self.xmin):
                self.xmin = 0.0
            if np.isinf(self.xmax) or np.isnan(self.xmax):
                self.xmax = 0.0
            self.axes.set_xbound(lower=self.xmin, upper=self.xmax)
            self.axes.set_ybound(lower=self.y1_min, upper=self.y1_max)

            if self.second_axes:
                for line in self.second_axes.get_lines():
                    y_line_name = line.get_label()
                    if data[y_line_name].values[-1] / self.ynom[i] < self.y2_min + 0.05 or self.y2_min == 0.0:
                        self.y2_min = data[y_line_name].values[-1] / self.ynom[i] - 0.1
                    if data[y_line_name].values[-1] / self.ynom[i] > self.y2_max - 0.05 or self.y2_max == 0.0:
                        self.y2_max = data[y_line_name].values[-1] / self.ynom[i] + 0.1
                    x_line_name = NOMENCLATURE[self.configFile[self.configName]['XY']['X axis value']] + y_line_name[
                                                                                                         -2:]
                    if data[x_line_name].values[-1] / self.xnom < self.xmin + 0.05 or self.xmin == 0.0:
                        self.xmin = data[x_line_name].values[-1] / self.xnom - 0.1
                    if data[x_line_name].values[-1] / self.xnom > self.xmax - 0.05 or self.xmax == 0.0:
                        self.xmax = data[x_line_name].values[-1] / self.xnom + 0.1

                    line.set_xdata(data[x_line_name].values / self.xnom)
                    line.set_ydata(data[y_line_name].values / self.ynom[i])

                    i += 1
                if np.isinf(self.y2_min) or np.isnan(self.y2_min):
                    self.y2_min = 0.0
                if np.isinf(self.y2_max) or np.isnan(self.y2_max):
                    self.y2_max = 0.0

                self.second_axes.set_xbound(lower=self.xmin, upper=self.xmax)
                self.second_axes.set_ybound(lower=self.y2_min, upper=self.y2_max)


class Library_plot:
    """
    Class representing a disabled plot
    """
    def __init__(self, figure=None, configFile=None, rtp_conn=None):
        self.figure = figure
        self.configFile = configFile
        self.rtp_conn = rtp_conn
        sns.set_theme(style='darkgrid')

        while self.rtp_conn.poll() is False:
            time.sleep(0.5)

        data = self.rtp_conn.recv()
        self.library_name = self.configFile['MainTab']['Standard tested']
        self.library = data['data']

    def get_type(self):

        return 'Library'

    def data_update(self, data=None):
        a = 0

class Disabled_plot:
    """
    Class representing a disabled plot
    """
    def __init__(self, figure=None, configName=None, configFile=None):
        self.figure = figure
        self.configName = configName
        self.configFile = configFile
        self.axes = self.figure.add_subplot(int(self.configFile['MainTab']['Row']),
                                             int(self.configFile['MainTab']['Column']), int(self.configName[-1]) + 1)

    def get_type(self):

        return self.configFile[self.configName]['Plot type']

    def data_update(self):
        pass


class GraphFrame(wx.Frame):
    """ The main frame of the application
    """
    title = 'Real-time plotting'

    def __init__(self, parent=None, filename=None, env=None, config=None, params=None, lib_path=None, rtp_conn=None):
        wx.Frame.__init__(self, None, -1, self.title)

        self.event_col_name = None
        self.parent = parent
        self.filename = filename
        self.env = env
        self.config = config
        self.lib_path = lib_path
        self.rtp_conn = rtp_conn
        if params is None:
            self.params = self.config.params
        else:
            self.params = params
        self.configFile = json.loads(self.params['rtp_config'].replace('\'', '\"'))
        self.library = None
        self.panel = wx.Panel(self)
        dpi = 100.0
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        self.figure = Figure(figsize=(0.333*width/dpi, height/dpi-1.5), dpi=dpi)
        self.canvas = None
        self.df = pd.DataFrame()
        self.df_xy = None
        self.plots = []

        self.dpi = 100

        self.create_main_panel()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(25)

        self.Bind(wx.EVT_CLOSE, self.on_exit)


    def create_main_panel(self):

        #Initialisation of every subplots inside the figure
        if self.configFile['MainTab']['Standard tested'] == 'Custom':
            for i in range(0, int(self.configFile['MainTab']['Number of other tab'])):
                configName = 'Tab_' + str(i)
                if self.configFile[configName]['Plot type'] == 'Time-based':
                    self.plots.append(Time_based_plot(figure=self.figure, configName=configName, configFile=self.configFile,
                                                      params=self.params))
                elif self.configFile[configName]['Plot type'] == 'XY':
                    self.plots.append(XY_plot(figure=self.figure, configName=configName, configFile=self.configFile,
                                              params=self.params))
                elif self.configFile[configName]['Plot type'] == 'Disabled':
                    self.plots.append(Disabled_plot(figure=self.figure, configName=configName, configFile=self.configFile))
        else:
            self.plots.append(Library_plot(figure=self.figure, configFile=self.configFile, rtp_conn=self.rtp_conn))

        self.canvas = FigCanvas(self.panel, -1, self.figure)

        self.figure.tight_layout()

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, wx.EXPAND | wx.ALL, 5)

        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def data_read(self):
        data = None
        try:
            if self.rtp_conn:
                if self.rtp_conn.poll() is True:
                    data = self.rtp_conn.recv()
        except Exception as e:
            raise
        if data is not None:
            if data['name'] == 'new XY':
                self.df_xy = pd.DataFrame()

            elif data['name'] == 'Data':
                if self.event_col_name is None:
                    self.event_col_name = data['data'].index[-1]
                if self.df_xy is not None:
                    self.df_xy = self.df_xy.append(data['data'])
                self.df = self.df.append(data['data'])

            elif data['name'] == 'end loop':
                self.redraw_timer.Stop()

    def draw_plot(self):
        """ Redraws the plot
        """
        for plot in self.plots:
            if plot.get_type() == 'XY' and self.df_xy is not None:
                if self.df_xy.empty is False:
                    plot.data_update(self.df_xy, self.event_col_name)
            elif (plot.get_type() == 'Time-based' or plot.get_type() == 'Library') and self.df.empty is False:
                plot.data_update(self.df)

        self.figure.tight_layout()
        self.canvas.draw()

    def on_redraw_timer(self, event):
        if self.rtp_conn.poll():
            self.data_read()
            self.draw_plot()


    def on_exit(self, event):
        self.rtp_conn.send('terminate')
        self.Show(False)
        self.Destroy()
        self.parent.ExitMainLoop()




def RealTimePlottingDialog(filename, env, config, params, lib_path, rtp_conn):
    app = wx.App()
    app.frame = GraphFrame(app, filename, env, config, params, lib_path, rtp_conn)
    #alignToBottomRight(app.frame)
    app.SetTopWindow(app.frame)
    app.frame.Show()
    app.MainLoop()

