# -*- coding: utf-8 -*-

"""
Supported instruments (identified): MS2690A/MS2691A/MS2692A and
MS2830A/MS2840A/MS2850A
- Spectrum Analyzer
"""

import time
import numpy as np
import pandas as pd


class Driver():
    """ This Driver contains only few functions available for this device """

    def __init__(self):
        self.write("SYST:LANG SCPI")  # force SCPI language to avoid errors
        self.write("inst spect")  # spectrum mode
        self.write('FORM ASC')  # set ASCii format (Default) to data

        self.frequency = Frequency(self)  # Module frequency

        # OPTIMIZE: assume operation on trace 1 (A) could allow different trace
        # If so, you can use trace_dict={'A':'1', 'B':'2', 'C':'3', 'D':'4', 'E':'5', 'F':'6'}
        # trace_name=self.query('TRAC:ACT?') -> 'A' then trace_num=trace_dict[trace_name] then self.query(f'TRAC? TRAC{trace_num}')


    def get_id(self) -> str:
        return self.query('*IDN?')


    def get_power_marker(self, marker_num: int) -> float:
        value = int(marker_num)
        return float(self.query(f"CALC:MARK{value}:Y?"))

    def get_power_marker_1(self) -> float:
        return self.get_power_marker(1)

    def get_power_marker_2(self) -> float:
        return self.get_power_marker(2)

    def get_power_marker_3(self) -> float:
        return self.get_power_marker(3)


    def repeat_sweep(self):
        self.write("INIT:CONT ON")

    def single_sweep(self):
        old_timeout = self.controller.timeout
        if old_timeout < 30000:
            self.controller.timeout = 30000
        self.write("INIT:CONT OFF")
        self.write("INIT:MODE:SING")
        self.query("*OPC?")
        self.controller.timeout = old_timeout


    def get_timeout(self) -> float:
        return float(self.controller.timeout)

    def set_timeout(self, value: float):
        value = float(value)
        self.controller.timeout = value


    def save_waveform(self, name: str = "default"):  # Note that as a Device, (in autolab GUI), name="" by default
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.write(f'MMEM:STOR:TRAC TRACe1,"{timestamp}_{name}"')

    def frequency_array(self) -> np.ndarray:
        freq_start = self.frequency.get_frequency_start()  # GHz
        freq_stop = self.frequency.get_frequency_stop()  # GHz
        freq_point = self.frequency.get_points()

        freq = np.linspace(float(freq_start), float(freq_stop), int(freq_point))
        return freq

    def power_array(self) -> np.ndarray:
        power = self.query("TRAC? TRAC1").rstrip('\r\n').split(',')
        power = np.array(power, dtype=float)  # convert str to float
        return power

    def get_waveform(self) -> pd.DataFrame:
        """ Returns the trace 1 as a pd.DataDrame({"frequency(GHz)":np.ndarray, "power":np.ndarray}) """
        data = pd.DataFrame()
        data["frequency(GHz)"] = self.frequency_array()
        data["power"] = self.power_array()
        return data


    def get_driver_model(self):
        model = []

        model.append({'element': 'module', 'name': 'frequency',
                      'object': getattr(self, 'frequency'),
                      'help': 'Frequency module'})

        model.append({'element': 'variable', 'name': 'power1', 'type': float, 'unit': 'dBm',
                      'read': self.get_power_marker_1,
                      'help': 'Power of the marker 1 (dBm)'})

        model.append({'element': 'variable', 'name': 'power2', 'type': float, 'unit': 'dBm',
                      'read': self.get_power_marker_2,
                      'help': 'Power of the marker 2 (dBm)'})

        model.append({'element': 'variable', 'name': 'power3', 'type': float, 'unit': 'dBm',
                      'read': self.get_power_marker_3,
                      'help': 'Power of the marker 3 (dBm)'})

        model.append({'element':'action', 'name': 'single_sweep',
                      'do':self.single_sweep,
                      'help':'Start a single measurement'})

        model.append({'element':'action', 'name': 'repeat_sweep',
                      'do':self.repeat_sweep,
                      'help':'Repeat measurement forever'})

        model.append({'element': 'action', 'name': 'save_waveform',
                      'param_type': str, # 'param_unit': 'filename', <- only useful if save on same computer! Here not the case
                      'do': self.save_waveform,
                      'help':'Saves waveform to instrument'})

        model.append({'element': 'variable', 'name': 'waveform', 'type': pd.DataFrame,
                      'read': self.get_waveform,
                      'help':'Returns waveform as DataFrame with "frequency(GHz)" and "power" keys'})

        model.append({'element': 'variable', 'name': 'timeout', 'type': float, 'unit': 's',
                      'read': self.get_timeout, 'write': self.set_timeout,
                      'help': 'Change the controller timeout. Usefull if single measure too long'})
        return model

#################################################################################
############################## Connections classes ##############################
class Driver_VISA(Driver):
    def __init__(self, address='GPIB0::1::INSTR', **kwargs):
        import pyvisa as visa

        rm = visa.ResourceManager()
        self.controller = rm.open_resource(address)
        self.controller.timeout = 3000

        Driver.__init__(self)

    def close(self):
        self.controller.close()
    def query(self, command):
        return self.controller.query(command).strip('\r\n')
    def write(self, command):
        self.controller.write(command)
############################## Connections classes ##############################
#################################################################################


class Frequency:

    def __init__(self, dev):

        self.query = dev.query
        self.write = dev.write


    def get_frequency_start(self) -> float:
        return float(self.query('FREQ:STARt?')) * 1e-9  # convert to GHz

    def set_frequency_start(self, value: float):
        value = float(value)
        self.write(f'FREQ:STAR {value}GHZ')


    def get_frequency_stop(self) -> float:
        return float(self.query('FREQ:STOP?')) * 1e-9  # convert to GHz

    def set_frequency_stop(self, value: float):
        value = float(value)
        self.write(f'FREQ:STOP {value}GHZ')


    def get_frequency_step(self) -> float:
        return float(self.query('FREQ:CENT:STEP?'))

    def set_frequency_step(self, value):
        value = float(value)
        self.write(f'FREQ:CENT:STEP {value}')


    def get_frequency_span(self) -> float:
        return float(self.query('FREQ:SPAN?')) * 1e-9  # convert to GHz

    def set_frequency_span(self, value: float):
        value = float(value)
        self.write(f'FREQ:SPAN {value}GHZ')


    def get_frequency_center(self) -> float:
        return float(self.query("FREQ:CENT?")) * 1e-9  # convert to GHz

    def set_frequency_center(self, value: str):
        value = float(value)
        self.write(f"FREQ:CENT {value}GHZ")
        self.query('*OPC?')


    def get_points(self):
        return int(self.query(':SENS:SWEep:POINts?'))

    def set_points(self, value: int):
        value = int(value)
        self.write(f'SENS:SWEep:POINts {value}')


    def get_driver_model(self):
        model = []

        model.append({'element':'variable', 'name':'start', 'type': float, 'unit': 'GHz',
                      'read': self.get_frequency_start, 'write': self.set_frequency_start,
                      'help': 'Set the start frequency (GHz)'})

        model.append({'element':'variable', 'name':'stop', 'type': float, 'unit':'GHz',
                      'read':self.get_frequency_stop, 'write':self.set_frequency_stop,
                      'help':'Set the stop frequency (GHz)'})

        model.append({'element': 'variable', 'name': 'step', 'type': float, 'unit': 'Hz',
                      'read': self.get_frequency_step, 'write': self.set_frequency_step,
                      'help':' Set the frequency step (GHz)'})

        model.append({'element': 'variable', 'name': 'span', 'type': float, 'unit': 'GHz',
                      'read': self.get_frequency_span, 'write': self.set_frequency_span,
                      'help': 'Set the frequency span (GHz)'})

        model.append({'element': 'variable', 'name': 'center', 'type': float, 'unit': 'GHz',
                      'read': self.get_frequency_center, 'write': self.set_frequency_center,
                      'help': 'Set the center frequency (GHz)'})

        model.append({'element':'variable', 'name':'points', 'type': int,
                      'read': self.get_points, 'write': self.set_points,
                      'help': 'Set the number of points for the scan'})

        return model
