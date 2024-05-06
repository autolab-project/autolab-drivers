# -*- coding: utf-8 -*-
"""
Created on Fri May 17 16:36:53 2019

@author: quentin.chateiller
"""

from typing import Tuple, List
import time

import numpy as np
import pandas as pd


class Driver():

    def __init__(self):

        self.amp = 1

        self.slot1 = Slot(self, 1)
        self.slot2 = Slot(self, 2)

        self.option = True

        self.count = 0
        self.phrase = 'Hello there'
        self.sleep = 0
        #raise ValueError('Test error')
        self.constant = 0
        self._nbpts = 1000
        self._array_custom = np.array([[1, 2],
                                       [3, 6],
                                       [5, 4]])
        self._tuple = (["voltage", "current", "resistance"], 0)  # int correspond to index of selected item
        self._df = pd.DataFrame(self._array_custom, columns=['x', 'y'])

        self._verbose = False
        self._instance_active = True

    def set_sleep(self, value: float):
        self.sleep = float(value)

    def get_sleep(self) -> float:
        return float(self.sleep)

    def set_verbose(self, value: bool):
        if value == "False": value = False
        elif value == "True": value = True
        self._verbose = bool(int(float(value)))
        print("Activate verbose") if self._verbose else print("Deactivate verbose")

    def get_verbose(self) -> bool:
        return self._verbose

    def get_amplitude(self) -> float:
        time.sleep(self.sleep)
        if not self._instance_active: raise ValueError("DUMMY DEVICE IS CLOSED")
        value = self.amp + np.random.uniform(-1, 1)*0.01
        if self._verbose: print('get amplitude', value)
        return value

    def set_phrase(self, phrase: str):
        time.sleep(self.sleep)
        assert isinstance(phrase, str)
        self.phrase = str(phrase)
        if self._verbose: print('set phrase', self.phrase)

    def get_phrase(self) -> str:
        time.sleep(self.sleep)
        if self._verbose: print('get phrase', self.phrase)
        return str(self.phrase)

    def set_amplitude(self, value: float):
        time.sleep(self.sleep)
        if not self._instance_active:
            raise ValueError("DUMMY DEVICE IS CLOSED")
        self.amp = float(value)
        if self._verbose: print('set amplitude', self.amp)
        #raise ValueError('Test error')

    def get_phase(self) -> float:
        time.sleep(self.sleep)
        value = np.random.uniform(-1, 1)
        if self._verbose: print('get phase', value)
        return value

    def set_phase(self, value: float):
        time.sleep(self.sleep)
        self.phase = value
        if self._verbose: print('set phase', value)

    def do_sth(self):
        time.sleep(self.sleep)
        if self._verbose: print('do sth')
        #raise ValueError('Test error')

    def get_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame()
        df["x"] = np.linspace(1500, 1600, self._nbpts)
        mu = self.constant + df["x"].mean()
        sigma = 20
        df["y"] = ((1 + 0.6*np.random.random(len(df)))
                   * 50 / (sigma * np.sqrt(2 * np.pi))
                   * np.exp(-(df["x"] - mu)**2 / (2 * sigma**2)))
        time.sleep(self.sleep)
        return df

    def get_dataframe_custom(self) -> pd.DataFrame:
        time.sleep(self.sleep)
        return self._df

    def set_dataframe_custom(self, value: pd.DataFrame):
        time.sleep(self.sleep)
        self._df = pd.DataFrame(value)

    def set_option(self, value: bool):
        time.sleep(self.sleep)
        self.option = bool(value)
        if self._verbose: print('set option', self.option)

    def get_option(self) -> bool:
        time.sleep(self.sleep)
        if self._verbose: print('get option', self.option)
        return bool(self.option)

    def get_array_custom(self) -> np.ndarray:
        time.sleep(self.sleep)
        return np.array(self._array_custom)

    def set_array_custom(self, value: np.ndarray):
        time.sleep(self.sleep)
        value = np.array(value)
        self._array_custom = value

    def get_array_1D(self) -> np.ndarray:
        time.sleep(self.sleep)
        return np.random.random(self._nbpts) + self.constant

    def get_array_2D(self) -> np.ndarray:
        time.sleep(self.sleep)
        x = np.linspace(1500, 1600, self._nbpts)
        mu = self.constant + x.mean()
        sigma = 20
        y = ((1 + 0.6*np.random.random(len(x)))
                   * 50 / (sigma * np.sqrt(2 * np.pi))
                   * np.exp(-(x - mu)**2 / (2 * sigma**2)))
        array_2D = np.array([x, y]).T
        # array_2D = np.random.random((self._nbpts,2))
        return array_2D

    def get_array_3D(self) -> np.ndarray:
        return np.random.normal(size=(200, 200))

    def get_Image(self) -> np.ndarray:
        import os
        from PIL import Image
        img = np.asarray(Image.open(
            os.path.join(os.path.dirname(__file__), 'dummy_image.jpg')))
        lum_img = img[:, :, 0]
        return lum_img + np.random.normal(
            size=lum_img.shape, scale=10+self.constant).astype(np.int64)

    def open_filename(self, value: str):
        time.sleep(self.sleep)
        if self._verbose: print('Open', value)

    def save_filename(self, value: str):
        time.sleep(self.sleep)
        if self._verbose: print('Save', value)

    def user_input(self, value):
        if self._verbose: print('User input:', value)

    def get_constant(self) -> float:
        return float(self.constant)

    def set_constant(self, value: float):
        self.constant = float(value)

    def get_nbpts(self) -> int:
        return int(self._nbpts)

    def set_nbpts(self, value: int):
        self._nbpts = int(value)

    def get_tuple(self) -> Tuple[List[str], int]:
        if self._verbose: print('get tuple', self._tuple)
        return tuple(self._tuple)

    def set_tuple(self, value: Tuple[List[str], int]):
        if self._verbose: print('set tuple', value)
        self._tuple = tuple(value)
        if self._verbose: print('do something with tuple item:', value[0][value[1]])

    def get_tuple_item(self) -> str:
        tuple1 = self.get_tuple()
        tuple_item = tuple1[0][tuple1[1]]
        if self._verbose: print('get tuple item', tuple_item)
        return tuple_item

    # def get_me(self):
    #     if self._verbose: print('You got me!')
    #     return 'You got me!'

    # def set_me(self, value):
    #     if self._verbose: print('You set me!')



    def get_driver_model(self) -> List[dict]:

        model = []

        for i in range(10):
            if hasattr(self, f'slot{i}'):
                model.append({'element': 'module', 'name': f'slot{i}',
                              'object': getattr(self, f'slot{i}')})

        model.append({'element': 'variable', 'name': 'amplitude', 'type': float, 'unit': 'V',
                      'read': self.get_amplitude, 'write': self.set_amplitude,
                      'help':'This is the amplitude of the device...'})
        model.append({'element': 'variable', 'name': 'phrase', 'type': str,
                      'read': self.get_phrase, 'write': self.set_phrase})
        model.append({'element': 'variable', 'name': 'phase', 'type': float,
                      'read': self.get_phase, 'write': self.set_phase})
        model.append({'element': 'variable', 'name': 'option', 'type': bool,
                      'read_init': True, 'read': self.get_option, 'write': self.set_option})

        model.append({'element': 'variable', 'name': 'dataframe', 'type': pd.DataFrame,
                      'read': self.get_dataframe,
                      'help': 'pd.DataFrame with shape (nbpts,2)'})
        model.append({'element': 'variable', 'name': 'dataframe_custom', 'type': pd.DataFrame,
                      'read': self.get_dataframe_custom, 'write': self.set_dataframe_custom,
                      'help': 'Accept excel data drop'})
        model.append({'element': 'variable', 'name': 'array_1D', 'type': np.ndarray,
                      'read': self.get_array_1D,
                      'help': 'np.ndarray with shape (nbpts,)'})
        model.append({'element': 'variable', 'name': 'array_2D', 'type': np.ndarray,
                      'read': self.get_array_2D,
                      'help': 'np.ndarray with shape (nbpts,2)'})
        model.append({'element': 'variable', 'name': 'array_3D', 'type': np.ndarray,
                      'read': self.get_array_3D,
                      'help': 'np.ndarray with shape (200,200)'})
        model.append({'element': 'variable', 'name': 'Image', 'type': np.ndarray,
                      'read': self.get_Image,
                      'help': 'Black hole image with noise linked to constant, np.ndarray with shape (990,1980)'})
        model.append({'element': 'variable', 'name': 'array_custom', 'type': np.ndarray,
                      'read_init': True, 'read': self.get_array_custom, 'write': self.set_array_custom,
                      'help': 'Create an array by hand. Ex 1,2,3 or [[1,2],[3,4]]'})
        model.append({'element': 'variable', 'name': 'measure_mode', 'type': tuple,
                      'read_init': True, 'read': self.get_tuple, 'write': self.set_tuple,
                      'help': 'Select one item among a list'})
        model.append({'element': 'variable', 'name': 'tuple_item', 'type': str,
                      'read': self.get_tuple_item,
                      'help': 'See which item is selected in measure_mode'})
        # model.append({'element': 'variable', 'name': 'test space', 'type': str,
        #               'read': self.get_me, 'write': self.set_me,
        #               'help': 'Get or set this variable using $eval:dummy.testspace()'})

        model.append({'element': 'variable', 'name': 'sleep', 'type': float,
                      'read': self.get_sleep, 'write': self.set_sleep,
                      'help': 'Set delay in test functions (time.sleep) to mimic driver delay'})
        model.append({'element': 'variable', 'name': 'verbose', 'type': bool,
                      'read_init': True, 'read': self.get_verbose, 'write': self.set_verbose,
                      'help': 'Activate/deactivate verbose of test functions'})
        model.append({'element': 'variable', 'name': 'constant', 'type': float,
                      'read': self.get_constant, 'write': self.set_constant,
                      'help': 'Constant variable used in array_1D, 2D, Image, dataframe.'})
        model.append({'element': 'variable', 'name': 'nbpts', 'type': int,
                      'read': self.get_nbpts, 'write': self.set_nbpts,
                      'help': 'Set number of point for array_1D, array_2D and dataframe.'})

        model.append({'element': 'action', 'name': 'something',
                      'do': self.do_sth,
                      'help': 'This do something...'})
        model.append({'element': 'action', 'name': 'open_file',
                      "param_type": str, "param_unit": "open-file",
                      'do': self.open_filename,
                      'help': 'This minmic open file'})
        model.append({'element': 'action', 'name': 'save_file',
                      "param_type": str, "param_unit": "save-file",
                      'do': self.save_filename,
                      'help': 'This minmic save file'})
        model.append({'element': 'action', 'name': 'user_input',
                      "param_type": str, "param_unit": "user-input",
                      'do': self.user_input,
                      'help': 'Asks the user for input (can be used to pause scan until user presses enter)'})
        return model


class Driver_CONN(Driver):

    def __init__(self, address: str = '192.168.0.8', **kwargs):
        print('DUMMY DEVICE INSTANTIATED with address', address)

        Driver.__init__(self, **kwargs)

    def close(self):
        print('DUMMY DEVICE CLOSED')
        self._instance_active = False


class Slot():

    def __init__(self, dev: Driver, num: int):
        self.dev = dev
        self.num = num

    def get_power(self) -> float:
        time.sleep(self.dev.sleep)
        value = np.random.uniform()
        if self.dev._verbose: print(f'slot {self.num} get power', value)
        return value

    def get_wavelength(self) -> float:
        time.sleep(self.dev.sleep)
        value = np.random.uniform()
        if self.dev._verbose: print(f'slot {self.num} get wavelength', value)
        return value

    def get_driver_model(self) -> List[dict]:
        config = []
        config.append({'element': 'variable', 'name': 'power', 'type': float, 'unit': 'W',
                       'read': self.get_power})
        config.append({'element': 'variable', 'name': 'wavelength', 'type': float, 'unit': 'nm',
                       'read': self.get_wavelength})
        return config
