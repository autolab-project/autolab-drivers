# -*- coding: utf-8 -*-
"""
"""

from typing import Tuple, List, Union

import numpy as np


class Driver():

    def __init__(self, ID: str, max_voltage_range: Tuple[float, float],
                 channel_list: List[int]):

        self.fs = 1000
        self.channels = (0,)
        self.ID = ID
        self.max_range = max_voltage_range
        self.channel_list = channel_list
        self.set_range(max_voltage_range)


    def get_data(self, nb_samples: int = 1) -> np.ndarray:
        min_val, max_val = self.range
        with self.nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                self.format_channels(), min_val=min_val, max_val=max_val)
            if nb_samples == 1:
                V = task.read()
            else:
                task.timing.cfg_samp_clk_timing(self.fs, samps_per_chan=nb_samples)
                V = task.read(nb_samples)
        V = np.array(V)
        return V.T

    def get_sample(self) -> np.ndarray:
        min_val, max_val = self.range
        with self.nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(
                self.format_channels(), min_val=min_val, max_val=max_val)
            V = task.read()
        V = np.array(V)
        return V.T


    def set_sampling_rate(self, fs: int):
        self.fs = fs

    def get_sampling_rate(self) -> int:
        return self.fs


    def set_channels(self, channels: Union[int, Tuple[int], List[int]]):
        if isinstance(channels, int): channels = (channels,)
        if not isinstance(channels, (tuple, list)):
            raise AssertionError("'channels' should be an integer, or a list of integers.")

        for channel in channels:
            if not isinstance(channel, int):
                raise AssertionError("'channels' should be an integer, or a list of integers.")
            if f"{self.ID}/ai{channel}" not in self.channel_list:
                raise AssertionError(f"No channel '{self.ID}/ai{channel}' found on the device.")
        self.channels = channels

    def get_channels(self) -> Tuple[int]:
        return self.channels

    def get_channel_gui(self) -> int:
        return self.channels[0]

    def format_channels(self) -> str:
        channel_str = ""
        for channel in self.channels:
            channel_str += f"{self.ID}/ai{channel}, "
        return channel_str[: -2]


    def get_range(self) -> Tuple[float, float]:
        return self.range

    def set_range(self, voltage_range: Tuple[float, float]):
        min_val, max_val = voltage_range
        range_min, range_max = self.max_range
        if min_val > max_val: min_val, max_val = max_val, min_val
        self.range = (max(min_val, range_min), min(max_val, range_max))


    def get_range_min(self) -> float:
        return self.range[0]

    def set_range_min(self, min_val: float):
        max_val = self.range[1]
        self.set_range((min_val, max_val))


    def get_range_max(self) -> float:
        return self.range[1]

    def set_range_max(self, max_val: float):
        min_val = self.range[0]
        self.set_range((min_val, max_val))


    def get_driver_model(self):
        model = []
        model.append({'element': 'variable', 'name': 'channel', 'type': int,
                      'read': self.get_channel_gui, 'write': self.set_channels,
                      'help': 'Sets the channel.'})
        model.append({'element': 'variable', 'name': 'data', 'type': float,
                      'read': self.get_sample, 'units': 'V',
                      'help': 'Reads the selected channel.'})
        model.append({'element':'variable', 'name': 'range_min', 'type': float,
                      'read':self.get_range_min, 'write': self.set_range_min,
                      'units': 'V', 'help': 'Set minimal voltage.'})
        model.append({'element': 'variable', 'name': 'range_max', 'type': float,
                      'read': self.get_range_max, 'write': self.set_range_max,
                      'units': 'V', 'help': 'Set maximal voltage.'})
        return model


###############################################################################
############################ Connections classes ##############################
class Driver_NI(Driver):

    def __init__(self, daq_id: str = "Dev1"):

        import nidaqmx
        self.nidaqmx = nidaqmx

        dev = self.nidaqmx.system.device.Device(daq_id)
        ranges = dev.ai_voltage_rngs
        max_voltage_range = (min(ranges), max(ranges))
        channel_list = dev.ai_physical_chans.channel_names
        Driver.__init__(self, daq_id, max_voltage_range, channel_list)

    def close(self):
        pass
############################ Connections classes ##############################
###############################################################################
