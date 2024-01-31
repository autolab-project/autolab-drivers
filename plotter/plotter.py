# -*- coding: utf-8 -*-
"""
Created on Mon Jun 13 21:26:10 2022

@author: jonathan
"""

import csv
import sys

import numpy as np
import pandas as pd

try:
    from pandas._libs.lib import no_default
except:
    no_default = None


def find_delimiter(filename):
    sniffer = csv.Sniffer()
    with open(filename) as fp:
        try:
            text = fp.read(5000)
            if text.startswith("#"):
                text = text[len(text.split("\n")[0])+len("\n"):]
            delimiter = sniffer.sniff(text).delimiter
        except:
            # delimiter = ","  # only 1 column
            delimiter = no_default
        if delimiter in ("e", "."):  # sniffer got it wrong
            delimiter = no_default
    return delimiter


def _skiprows(filename):
    with open(filename) as fp:
        if fp.read(1) not in ("#", "!", "\n"):
            skiprows = None
        else:
            skiprows = 1
            fp.readline()
            while fp.read(1) in ("#", "!", "\n"):
                skiprows += 1
                fp.readline()
    return skiprows


def find_header(filename, sep=no_default, skiprows=None):
    try:
        df = pd.read_csv(filename, sep=sep, header=None, nrows=5, skiprows=skiprows)
    except Exception:
        if type(skiprows) is not None: skiprows += 1
        df = pd.read_csv(filename, sep=sep, header=None, nrows=5, skiprows=skiprows)
    else:
        if skiprows == 1:
            try:
                df_columns = pd.read_csv(filename, sep=sep, header="infer", skiprows=0, nrows=0)
            except Exception:
                pass
            else:
                columns = list(df_columns.columns)
                if columns[0] == "#":
                    columns.pop(0)
                    if len(columns) == len(df):
                        return (0, 1, columns)  # (header, skiprows, columns)

    try:
        first_row = df.iloc[0].values.astype("float")
        return ("infer", skiprows, no_default) if tuple(first_row) == tuple([i for i in range(len(first_row))]) else (None, skiprows, no_default)
    except:
        pass
    df_header = pd.read_csv(filename, sep=sep, nrows=5, skiprows=skiprows)

    return ("infer", skiprows, no_default) if tuple(df.dtypes) != tuple(df_header.dtypes) else (None, skiprows, no_default)


def formatData(data):
    """ Format data """
    try:
        data = pd.DataFrame(data)
    except ValueError:
        data = pd.DataFrame([data])
    data.columns = data.columns.astype(str)
    data_type = data.values.dtype

    try:
        data[data.columns] = data[data.columns].apply(pd.to_numeric, errors="coerce")
    except ValueError:
        pass  # OPTIMIZE: This happens when their is identical column name
    if len(data) != 0:
        assert not data.isnull().values.all(), f"Datatype '{data_type}' not supported"
        if data.iloc[-1].isnull().values.all():  # if last line is full of nan, remove it
            data = data[:-1]
    if data.shape[1] == 1:
        data.rename(columns = {'0':'1'}, inplace=True)
        data.insert(0, "0", range(data.shape[0]))
    return data


def importData(filename):
    """ This function open the data with the provided filename """

    skiprows = _skiprows(filename)
    sep = find_delimiter(filename)
    (header, skiprows, columns) = find_header(filename, sep, skiprows)
    try:
        data = pd.read_csv(filename, sep=sep, header=header, skiprows=skiprows, names=columns)
    except TypeError:
        data = pd.read_csv(filename, sep=sep, header=header, skiprows=skiprows, names=None)  # for pandas 1.2: names=None but sep=no_default
    except:
        data = pd.read_csv(filename, sep="\t", header=header, skiprows=skiprows, names=columns)

    assert len(data) != 0, "Can't import empty DataFrame"
    data = formatData(data)
    return data


class Driver :

    def __init__(self, gui=None):

        if gui:
            import pyqtgraph as pg
            # Best practice with gui would be to only use addToQueue, getFromGui and setStatus to avoid messing with plotter
            self.gui = gui

            pen_gray = pg.mkPen(color=0.2, style=pg.QtCore.Qt.DashLine)
            pen_gray_2 = pg.mkPen(color=0.2, style=pg.QtCore.Qt.DashLine)
            pen_r = pg.mkPen(color="r", style=pg.QtCore.Qt.DashLine)
            pen_g = pg.mkPen(color=(50, 180, 10), style=pg.QtCore.Qt.DashLine)  # darker green
            pen_b = pg.mkPen(color="b", style=pg.QtCore.Qt.DashLine)

            # Widgets (InfiniteLine) needs to be created by gui to have correct connection to thread
            # Need to wait until gui returns a widget because they are created on a different thread
            self.cursor_left_vertical = self.gui.createWidget(pg.InfiniteLine, angle=90, pen=pen_b, hoverPen="b", name='Cursor left vertical',
                **{'movable': True, 'label': 'x={value:.7g}', 'labelOpts': {
                    'position': 0.1, 'color': 'b', 'movable': True, 'fill': (200, 200, 200, 50)}})
            if self.cursor_left_vertical: self.cursor_left_vertical.hide()

            self.cursor_right_vertical = self.gui.createWidget(pg.InfiniteLine, angle=90, pen=pen_r, hoverPen="r", name='Cursor right vertical',
                **{'movable': True, 'label': 'x={value:.7g}', 'labelOpts': {
                    'position': 0.2, 'color': 'r', 'movable': True, 'fill': (200, 200, 200, 50)}})
            if self.cursor_right_vertical: self.cursor_right_vertical.hide()

            self.cursor_extremum_horizontal = self.gui.createWidget(pg.InfiniteLine, angle=0, pen=pen_g, hoverPen=(50, 180, 10), name='Cursor extremum horizontal',
                **{'movable': True, 'label': 'y={value:.7g}', 'labelOpts': {
                    'position': 0.5, 'color': (50, 180, 10), 'movable': True, 'fill': (200, 200, 200, 50)}})
            if self.cursor_extremum_horizontal: self.cursor_extremum_horizontal.hide()

            self.cursor_left_horizontal = self.gui.createWidget(pg.InfiniteLine, angle=0, pen=pen_gray, hoverPen=0.2, name='Cursor left horizontal',
                **{'movable': True, 'label': 'y={value:.7g}', 'labelOpts': {
                    'position': 0.5, 'color': 0.2, 'movable': True, 'fill': (200, 200, 200, 50)}})
            if self.cursor_left_horizontal: self.cursor_left_horizontal.hide()

            self.cursor_right_horizontal = self.gui.createWidget(pg.InfiniteLine, angle=0, pen=pen_gray_2, hoverPen=0.7, name='Cursor right horizontal',
                **{'movable': True, 'label': 'y={value:.7g}', 'labelOpts': {
                    'position': 0.6, 'color': 0.7, 'movable': True, 'fill': (200, 200, 200, 50)}})
            if self.cursor_right_horizontal: self.cursor_right_horizontal.hide()

            self.cursor_list = [
                self.cursor_left_vertical, self.cursor_right_vertical,
                self.cursor_extremum_horizontal, self.cursor_left_horizontal,
                self.cursor_right_horizontal]
        else:
            self.gui = None

        self.data = pd.DataFrame()
        self.x_label = ""
        self.y_label = ""
        self.isDisplayCursor = False

        self.info = DataModule(self)
        self.min = MinModule(self)
        self.max = MaxModule(self)
        self.mean = MeanModule(self)
        self.std = StdModule(self)
        self.bandwidth = BandwidthModule(self)

    def get_cursor_movable(self):
        if self.gui: return bool(self.cursor_list[0].movable)

    def set_cursor_movable(self, value):
        value = bool(int(float(value)))
        for cursor in self.cursor_list:
            cursor.setMovable(value)

    def get_displayCursor(self):
        return bool(self.isDisplayCursor)

    def set_displayCursor(self, value):
        value = bool(int(float(value)))
        self.isDisplayCursor = value
        self.refresh(self.data)

    def get_x_label(self):
        return self.x_label

    def set_x_label(self, value):
        key = str(value)
        keys = self.get_keys()
        if key in keys:
            self.x_label = key
        else:
            self.x_label = ""


    def get_y_label(self):
        return self.y_label

    def set_y_label(self, value):
        key = str(value)
        keys = self.get_keys()
        if key in keys:
            self.y_label = key
        else:
            self.y_label = ""


    def get_keys(self):
        if self.data is not None:
            return str(list(self.data.keys()))

    def get_data(self):
        return pd.DataFrame(self.data)


    def set_data(self, value):
        """  Open data from DataFrame """

        df = formatData(value)
        self._open(df)


    def open(self, filename):
        """  Open data from file """

        data = importData(filename)

        self._open(data)

    def _open(self, df):
        """  Add data to dict """

        self.data = df

        try:
            self.set_x_label(df.keys()[0])
        except:
            self.set_x_label("")

        try:
            self.set_y_label(df.keys()[-1])
        except:
            self.set_y_label("")

    def refresh(self, data):
        """ Called by plotter"""

        if self.gui:
            self.set_data(data)

            if self.isDisplayCursor:
                target_x = self.bandwidth.target_x
                level = self.bandwidth.level
                comparator = self.bandwidth._comparator
                depth = self.bandwidth.depth
                try:
                    self.bandwidth.search_bandwitdh(target_x, level=level, comparator=comparator, depth=depth)
                except Exception as error:
                    if str(error) == "Empty dataframe":
                        self.displayCursors([(None,None)]*3)
                    else:
                        self.gui.setStatus(f"Can't display markers: {error}",10000, False)
            else:
                self.displayCursors([(None,None)]*3)

    def refresh_gui(self):
        if self.gui:
            results = self.bandwidth.results
            cursors_coordinate = (results["left"], results["extremum"], results["right"])

            try:
                self.displayCursors(cursors_coordinate)
            except Exception as error:
                self.gui.setStatus(f"Can't display markers: {error}",10000, False)

            if not self.isDisplayCursor:
                for cursor in self.cursor_list: cursor.hide()

    def displayCursors(self, cursors_coordinate):

        if self.gui:
            assert len(cursors_coordinate) == 3, f"This function only works with 3 cursors, {len(cursors_coordinate)} were given"
            (left, extremum, right) = cursors_coordinate

            if len(self.data) != 0:
                if self.x_label == self.y_label:
                    x_data = np.array(self.data.values[:,0])
                    y_data = x_data
                else:
                    x_data = self.data[self.x_label]
                    y_data = self.data[self.y_label]

                bounds_vertical = [np.nextafter(x_data.min(), x_data.min()-1),
                                   np.nextafter(x_data.max(), x_data.max()+1)]
                bounds_horizontal = [np.nextafter(y_data.min(), y_data.min()-1),
                                     np.nextafter(y_data.max(), y_data.max()+1)]

                self.cursor_left_vertical.setBounds(bounds_vertical)
                self.cursor_right_vertical.setBounds(bounds_vertical)

                self.cursor_left_horizontal.setBounds(bounds_horizontal)
                self.cursor_right_horizontal.setBounds(bounds_horizontal)
                self.cursor_extremum_horizontal.setBounds(bounds_horizontal)

            # left cursor
            if left[0] is None or np.isnan(left[0]):
                self.cursor_left_vertical.hide()
            else:
                self.cursor_left_vertical.setValue(left[0])
                self.cursor_left_vertical.show()
                # WARNING: pyqtgraph is very susceptible with nan value, will stop working if plot nan due to ang = round(item.transformAngle()) in ViewBox with item being InfiniteLine

            # right cursor
            if right[0] is None or np.isnan(right[0]):
                self.cursor_right_vertical.hide()
            else:
                self.cursor_right_vertical.setValue(right[0])
                self.cursor_right_vertical.show()

            # extremum cursor
            if extremum[1] is None or np.isnan(extremum[1]):
                self.cursor_extremum_horizontal.hide()
            else:
                self.cursor_extremum_horizontal.setValue(extremum[1])
                self.cursor_extremum_horizontal.show()

            # left 3db marker
            if left[1] is None or np.isnan(left[1]):
                self.cursor_left_horizontal.hide()
            else:
                self.cursor_left_horizontal.setValue(left[1])
                self.cursor_left_horizontal.show()

            # right 3db marker
            if right[1] is None or np.isnan(right[1]):
                self.cursor_right_horizontal.hide()
            else:
                self.cursor_right_horizontal.setValue(right[1])
                self.cursor_right_horizontal.show()

            # remove right 3db marker if same as left
            if left[1] == right[1]:
                self.cursor_right_horizontal.hide()

            if extremum[1] == right[1]:
                self.cursor_right_horizontal.hide()

    def get_driver_model(self):

        config = []

        if self.gui:
            config.append({'element':'variable','name':'cursor_movable','type':bool,
                           'read_init':True,'read':self.get_cursor_movable, 'write':self.set_cursor_movable,
                           "help": "Select if cursors are movable"})
            config.append({'element':'variable','name':'displayCursor','type':bool,
                           'read':self.get_displayCursor, 'write':self.set_displayCursor,
                           "help": "Select if want to display cursors"})

        # else:
        config.append({'element':'module','name':'info','object':getattr(self,'info')})

        config.append({'element':'action','name':'open',
                       'do':self.open,
                       "param_type":str,
                       "param_unit":"open-file",
                       'help':'Open DataFrame with the provided filename'})

        config.append({'element':'variable','name':'data','type':pd.DataFrame,
                       'read':self.get_data,
                       "help": "Return DataFrame stored"})

        config.append({'element':'action','name':'set_data',
                        'do':self.set_data,
                        'param_type':pd.DataFrame,
                        'help':'Add DataFrame to device. In GUI, use $eval:df with df being for example dummy.array_1D() or any other df from another device.'})

        config.append({'element':'module','name':'min','object':getattr(self,'min')})
        config.append({'element':'module','name':'max','object':getattr(self,'max')})
        config.append({'element':'module','name':'mean','object':getattr(self,'mean')})
        config.append({'element':'module','name':'std','object':getattr(self,'std')})
        config.append({'element':'module','name':'bandwidth','object':getattr(self,'bandwidth'),
                       'help': 'Control bandwidth search options'})

        return config

    def close(self):
        for cursor in self.cursor_list:
            self.gui.removeWidget(cursor)

class Driver_DEFAULT(Driver):
    def __init__(self, **kwargs):

        Driver.__init__(self, **kwargs)


class DataModule:

    def __init__(self, analyzer):

        self.analyzer = analyzer


    def get_driver_model(self):

        config = []

        config.append({'element':'variable','name':'keys',
                       'read':self.analyzer.get_keys,
                       'type':str,
                       'help':'Data keys'})

        config.append({'element':'variable','name':'x_label',
                       'read':self.analyzer.get_x_label,'write':self.analyzer.set_x_label,
                       'type':str,
                       'help':'Set x_label to consider in analyze functions'})

        config.append({'element':'variable','name':'y_label',
                       'read':self.analyzer.get_y_label,'write':self.analyzer.set_y_label,
                       'type':str,
                       'help':'Set y_label to consider in analyze functions'})


        return config



class MinModule:

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def x(self):
        index = np.argmin(self.analyzer.data[self.analyzer.y_label])
        return self.analyzer.data[self.analyzer.x_label][index]

    def y(self):
        return np.min(self.analyzer.data[self.analyzer.y_label])


    def get_driver_model(self):

        config = []

        config.append({'element':'variable','name':'x',
                       'read':self.x,
                       "type":float,
                       'help':'Returns the x value at which y is min'})

        config.append({'element':'variable','name':'y',
                        'read':self.y,
                        "type":float,
                        'help':'Returns the min y value'})

        return config


class MaxModule:

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def x(self):
        index = np.argmax(self.analyzer.data[self.analyzer.y_label])
        return self.analyzer.data[self.analyzer.x_label][index]

    def y(self):
        return np.max(self.analyzer.data[self.analyzer.y_label])


    def get_driver_model(self):

        config = []

        config.append({'element':'variable','name':'x',
                       'read':self.x,
                       "type":float,
                       'help':'Returns the x value at which y is max'})

        config.append({'element':'variable','name':'y',
                        'read':self.y,
                        "type":float,
                        'help':'Returns the max y value'})

        return config


class MeanModule:

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def x(self):
        return np.mean(self.analyzer.data[self.analyzer.x_label])  # OPTIMIZE: if y_label has none, return wrong value

    def y(self):
        return np.mean(self.analyzer.data[self.analyzer.y_label])


    def get_driver_model(self):

        config = []

        config.append({'element':'variable','name':'x',
                        'read':self.x,
                        "type":float,
                        'help':'Returns the mean value of x array'})

        config.append({'element':'variable','name':'y',
                        'read':self.y,
                        "type":float,
                        'help':'Returns the mean value of y array'})


        return config


class StdModule:

    def __init__(self, analyzer):
        self.analyzer = analyzer

    def x(self):
        return np.std(self.analyzer.data[self.analyzer.x_label])

    def y(self):
        return np.std(self.analyzer.data[self.analyzer.y_label])


    def get_driver_model(self):

        config = []

        config.append({'element':'variable','name':'x',
                        'read':self.x,
                        "type":float,
                        'help':'Returns the standard deviation of x array'})

        config.append({'element':'variable','name':'y',
                        'read':self.y,
                        "type":float,
                        'help':'Returns the standard deviation of y array'})

        return config


class BandwidthModule:

    def __init__(self, analyzer):

        self.analyzer = analyzer
        self.results = self.init_variables()
        self.target_x = -1
        self.level = -3.
        self.depth = 1
        self.comparator = True
        self._comparator = np.greater
        self._remove_zero = False


    def init_variables(self) -> dict:
        return {"left": (0, -99), "extremum": (0, -99), "right": (0, -99)}


    def get_x_left(self) -> float:
        if self.analyzer.gui: return float(self.analyzer.cursor_left_vertical.value())
        else: return self.results["left"][0]

    def get_y_left(self) -> float:
        if self.analyzer.gui and len(self.analyzer.data) != 0: return self._get_y_from_x(
                self.analyzer.data, float(self.analyzer.cursor_left_vertical.value()))
        else: return self.results["left"][1]

    def get_x_extremum(self) -> float:
        return self.results["extremum"][0]

    def get_y_extremum(self) -> float:
        if self.analyzer.gui: return float(self.analyzer.cursor_extremum_horizontal.value())
        else: return self.results["extremum"][1]

    def get_x_right(self) -> float:
        if self.analyzer.gui: return float(self.analyzer.cursor_right_vertical.value())
        else: return self.results["right"][0]

    def get_y_right(self) -> float:
        if self.analyzer.gui and len(self.analyzer.data) != 0: return self._get_y_from_x(
                self.analyzer.data, float(self.analyzer.cursor_right_vertical.value()))
        else: return self.results["right"][1]

    def get_x_width(self):
        return abs(self.get_x_right() - self.get_x_left())

    def _get_y_from_x(self, data, value):

        x_label = self.analyzer.x_label
        y_label = self.analyzer.y_label

        if x_label == y_label:
            y_i = value  # assume same values for same key
        else:
            # WARNING: bad because assume regular spacing
            two_closest = data.iloc[(data[x_label] - value).abs().argsort()[:2]]

            x1 = two_closest[x_label].iloc[0]
            x2 = two_closest[x_label].iloc[1]
            y1 = two_closest[y_label].iloc[0]
            y2 = two_closest[y_label].iloc[1]

            if x2 == x1:
                y_i = y1
            else:
                a = (y2 - y1) / (x2 - x1)
                b = y1 - a*x1
                y_i = a*value + b

        return y_i


    def get_target_x(self):
        """ This function returns the value of the target x value to find the local extremum """

        return float(self.target_x)

    def get_depth(self):
        """ This function returns the value of the algorithm depth to find the local extremum """

        return int(self.depth)

    def set_depth(self,value):
        """ This function set the value of the algorithm depth to find the local extremum """

        self.depth = int(value)
        self.analyzer.refresh(self.analyzer.data)

    def get_level(self):
        """ This function returns the value of the drop in dB for the bandwitdh """

        return float(self.level)

    def set_level(self,value):
        """ This function set the value of the drop in dB for the bandwitdh """

        self.level = float(value)
        self.analyzer.refresh(self.analyzer.data)


    def get_comparator(self):
        """ This function returns the comparator state """

        return bool(int(float(self.comparator)))

    def set_comparator(self,value):
        """ This function set the comparator state """

        self.comparator = bool(int(float(value)))
        self._comparator = np.greater if self.comparator is True else np.less
        self.analyzer.refresh(self.analyzer.data)


    def search_bandwitdh(self, target_x=-1, level="default", comparator="default", depth="default"):
        """ This function compute the bandwidth around target_x and return the x,y coordinate of the left, center and right"""

        self.target_x = target_x

        if depth == "default":
            depth = self.depth

        if level == "default":
            level = self.level

        if comparator == "default":
            comparator = self._comparator

        data = self.analyzer.data
        variable_x = self.analyzer.x_label
        variable_y = self.analyzer.y_label

        assert len(data) != 0, "Empty dataframe"

        try:
            if variable_x == variable_y:
                x_data = np.array(data.values[:,0])
                y_data = x_data
            else:
                x_data, y_data = np.array(data[variable_x]), np.array(data[variable_y])

            self.results = sweep_analyse(x_data, y_data, target_x=target_x, level=level, comparator=comparator, depth=depth, remove_zero=self._remove_zero)

        except Exception as error:
            print("Couldn't find the bandwitdh:", error, file=sys.stderr)
            self.results = self.init_variables()

        self.analyzer.refresh_gui()

        return self.results


    def get_driver_model(self):

        config = []

        config.append({'element':'action','name':'search_bandwitdh',
                        'do':self.search_bandwitdh,
                        "param_type":float,
                        'help':'Find the bandwitdh around the local peak closed to the defined x value. Set -1 for global extremum'})

        config.append({'element':'variable','name':'x_left',
                       'read':self.get_x_left,
                       'type':float,
                       'help':'Return x_left value'})

        config.append({'element':'variable','name':'y_left',
                       'read':self.get_y_left,
                       'type':float,
                       'help':'Return y_left value'})

        config.append({'element':'variable','name':'x_extremum',
                       'read':self.get_x_extremum,
                       'type':float,
                       'help':'Return x_max value'})

        config.append({'element':'variable','name':'y_extremum',
                       'read':self.get_y_extremum,
                       'type':float,
                       'help':'Return y_max value'})

        config.append({'element':'variable','name':'x_right',
                       'read':self.get_x_right,
                       'type':float,
                       'help':'Return x_right value'})

        config.append({'element':'variable','name':'y_right',
                       'read':self.get_y_right,
                       'type':float,
                       'help':'Return y_right value'})

        config.append({'element':'variable','name':'x_width',
                       'read':self.get_x_width,
                       'type':float,
                       'help':'Return x_width value'})

        config.append({'element':'variable','name':'depth',
                       'read_init':True,
                       'read':self.get_depth,
                       'write':self.set_depth,
                       'type':int,
                       'help':'Set algorithm depth to find the local extremum'})

        config.append({'element':'variable','name':'comparator',
                       'read_init':True,
                       'read':self.get_comparator,
                       'write':self.set_comparator,
                       'type':bool,
                       'help':'Set comparator state. True for greater and False for less'})

        config.append({'element':'variable','name':'level',
                       'read_init':True,
                       'read':self.get_level,
                       'write':self.set_level,
                       'type':float,
                       'help':'Set drop level in dB for the bandwidth'})

        return config


def sweep_analyse(x_data, y_data, target_x=-1, level=-3, comparator=np.greater, depth=1, remove_zero=False):
    """ target_x : x value close to the desired local extremum y. If -1, consider default and choose global extremum y"""
    # OPTIMIZE: put back this line -> data = data.dropna()  # BUG: crash python if ct400 dll loaded
    if comparator is True:
       comparator = np.greater
    elif comparator is False:
       comparator = np.less

    x_data, y_data = np.array(x_data), np.array(y_data)

    if np.all(x_data[:-1] >= x_data[1:]):  # change decreasing order to increasing
        x_data = x_data[::-1]
        y_data = y_data[::-1]

    assert np.all(x_data[:-1] <= x_data[1:]), "x axis is not sorted"

    if remove_zero:
        if y_data.any():  # don't remove if have only 0
            keep_data = y_data != 0
            y_data = y_data[keep_data]
            x_data = x_data[keep_data]

    if target_x != -1:

        order = lambda x: (((x-1) % 3)**2 + 1)*10**abs((x-1)//3)
        order_array = order(np.arange(1, depth+1))
        # order_array = np.array([1, 2, 5, 10, 20, 50, 100, 200])  # result if depth=6
        data = list()

        for order in order_array:  # search local extremum with different filter setting
            extremum_filter = find_local_extremum(x_data, y_data, target_x, level, order, comparator=comparator)
            point = {"x": extremum_filter[0], "y": extremum_filter[1]}
            data.append(point)

        df = pd.DataFrame(data)

        x_candidates = df['x'].mode().values  # wavelength with the most occurences (could have several wavelength with same occurance)

        index = abs(x_candidates - target_x).argmin()  # take wavelength closer to target_x if several x points found
        extremum_x = x_candidates[index]

        index2 = np.where(x_data == extremum_x)[0][0]
        extremum = (extremum_x, y_data[index2])

    else:
        # get extremum y_data and change it only if user want a different x_max
        if comparator is np.greater:
            extremum_index = np.argmax(y_data)
        elif comparator is np.less:
            extremum_index = np.argmin(y_data)
        else:
            raise TypeError(f"Comparator must be of type np.greater or np.less or bool. Given {comparator} of type {type(comparator)}")

        extremum = (x_data[extremum_index], y_data[extremum_index])

    # df.hist()  # used to see the selection process
    bandwidth_left, bandwidth_right = find_bandwidth(x_data, y_data, level, extremum, interp=True, comparator=comparator)

    results = {"left": bandwidth_left, "extremum": extremum, "right": bandwidth_right}

    return results


def find_local_extremum(x_data, y_data, target_x, level, order, comparator=np.greater):

    """ Find local extremum with closest x value to target_x.
        order is used to filter local extremums. """

    from scipy.signal import argrelextrema

    extremum_array_index = argrelextrema(y_data, comparator, order=order)[0]

    if len(y_data) > 1:
        if y_data[-1] > y_data[-2]:
            extremum_array_index = np.append(extremum_array_index, len(y_data)-1)

        if y_data[0] > y_data[1]:
            extremum_array_index = np.insert(extremum_array_index, 0, 0)

    if extremum_array_index.shape[0] != 0:
        extremum_array_x = x_data[extremum_array_index]
        extremum_array_y = y_data[extremum_array_index]

        index = abs(extremum_array_x - target_x).argmin()
        extremum_filter = (extremum_array_x[index], extremum_array_y[index])  # data from filter extremum list
        extremum = find_extremum_from_extremum_filter(x_data, y_data, level, extremum_filter, interp=False, comparator=comparator)
    else:
        extremum_raw_index = np.argmax(y_data)
        extremum_raw = (x_data[extremum_raw_index], y_data[extremum_raw_index])
        extremum = extremum_raw

    return extremum


def find_extremum_from_extremum_filter(x_data, y_data, level, extremum_filter, interp, comparator=np.greater):

    bandwidth_left_filter, bandwidth_right_filter = find_bandwidth(x_data, y_data, level, extremum_filter, interp, comparator=comparator)

    interval_low_index = np.where(x_data <= bandwidth_left_filter[0])[0][-1]
    interval_high_index = np.where(x_data >= bandwidth_right_filter[0])[0][0]

    if interval_high_index == 0:
        new_interval_x = x_data[interval_low_index: None]
        new_interval_y = y_data[interval_low_index: None]
    else:
        new_interval_x = x_data[interval_low_index: interval_high_index+1]
        new_interval_y = y_data[interval_low_index: interval_high_index+1]

    if comparator is np.greater:
        extremum_index = np.argmax(new_interval_y)
    elif comparator is np.less:
        extremum_index = np.argmin(new_interval_y)

    extremum = (new_interval_x[extremum_index], new_interval_y[extremum_index])

    return extremum


def find_bandwidth(x_data, y_data, level, extremum, interp, comparator=np.greater):
    """ Find the bandwidth """
    x_data, y_data = np.array(x_data), np.array(y_data)

    if len(x_data) == 0:
        bandwidth_left = (None, None)
        return bandwidth_left, bandwidth_left
    elif len(x_data) == 1:
        bandwidth_left = (x_data[0], y_data[0])
        return bandwidth_left, bandwidth_left

    index_extremum = abs(x_data - extremum[0]).argmin()

    x_left = x_data[:index_extremum+1][::-1]  # Reverse order to start at extremum
    y_left= y_data[:index_extremum+1][::-1]

    x_right = x_data[index_extremum:]
    y_right = y_data[index_extremum:]

    target_y = extremum[1] + level

    bandwidth_left = find_bandwidth_side(x_left, y_left, target_y, level, extremum, interp)
    bandwidth_right = find_bandwidth_side(x_right, y_right, target_y, level, extremum, interp)

    return bandwidth_left, bandwidth_right


def find_bandwidth_side(x_side, y_side, target_y, level, extremum, interp):
    """ Find (x,y) coordinate of bandwith for the given side """
    if len(x_side) == 1:
        bandwidth_side = (x_side[0], y_side[0])
    else:
        if level == 0:
            bandwidth_side = extremum
        else:
            if level < 0:
                index_side_list1 = np.where(y_side <= target_y)[0]
            else:
                index_side_list1 = np.where(y_side >= target_y)[0]

            if index_side_list1.shape[0] == 0:
                bandwidth_side = (x_side[-1], y_side[-1])
            else:
                index_side1 = index_side_list1[0]
                x_side_cut1 = x_side[:index_side1+1][::-1]
                y_side_cut1 = y_side[:index_side1+1][::-1]

                if level < 0:
                    index_side_list2 = np.where(y_side_cut1 > target_y)[0]
                else:
                    index_side_list2 = np.where(y_side_cut1 < target_y)[0]

                if index_side_list2.shape[0] == 0 or len(x_side_cut1) == 1:
                    bandwidth_side = (x_side_cut1[0], y_side_cut1[0])
                else:
                    index_side2 = index_side_list2[0]
                    x_side_cut2 = x_side_cut1[:index_side2+1]
                    y_side_cut2 = y_side_cut1[:index_side2+1]

                    if interp:
                        bandwidth_side = interp_lin(x_side_cut2, y_side_cut2, target_y)
                    else:
                        bandwidth_side = (x_side_cut2[0], y_side_cut2[0])

    return bandwidth_side


def interp_lin(x_data, y_data, target_y):
    """ Interpolate between two points """
    assert len(x_data) == 2 and len(y_data) == 2, (f"Two points were expected for interpolation, {len(x_data)} were given")

    a = (y_data[-1] - y_data[0]) / (x_data[-1] - x_data[0])
    b = y_data[0] - a*x_data[0]
    y = target_y
    x = (y - b) / a

    return (x, y)
