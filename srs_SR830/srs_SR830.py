"""
Driver for the SRS SR810 and SR830 lockin amplifiers
Mainly derived from pymeasure - limited function set implemented so far
"""

import numpy as np
import time
import re


class Driver():

    def __init__(self):
        self.SAMPLE_FREQUENCIES = [
            62.5e-3, 125e-3, 250e-3, 500e-3, 1, 2, 4, 8, 16,
            32, 64, 128, 256, 512
        ]
        self.SENSITIVITIES = [
            2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9,
            500e-9, 1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6,
            200e-6, 500e-6, 1e-3, 2e-3, 5e-3, 10e-3, 20e-3,
            50e-3, 100e-3, 200e-3, 500e-3, 1
        ]
        self.TIME_CONSTANTS = [
            10e-6, 30e-6, 100e-6, 300e-6, 1e-3, 3e-3, 10e-3,
            30e-3, 100e-3, 300e-3, 1, 3, 10, 30, 100, 300, 1e3,
            3e3, 10e3, 30e3
        ]
        self.FILTER_SLOPES = [6, 12, 18, 24]
        self.EXPANSION_VALUES = [1, 10, 100]
        self.RESERVE_VALUES = ['High Reserve', 'Normal', 'Low Noise']
        self.CHANNELS = ['X', 'Y', 'R']
        self.INPUT_CONFIGS = ['A', 'A - B', 'I (1 MOhm)', 'I (100 MOhm)']
        self.INPUT_GROUNDINGS = ['Float', 'Ground']
        self.INPUT_COUPLINGS = ['AC', 'DC']
        self.INPUT_NOTCH_CONFIGS = ['None', 'Line', '2 x Line', 'Both']
        self.REFERENCE_SOURCES = ['External', 'Internal']
        self.SNAP_ENUMERATION = {"x": 1, "y": 2, "r": 3, "theta": 4,
                            "aux in 1": 5, "aux in 2": 6, "aux in 3": 7, "aux in 4": 8,
                            "frequency": 9, "ch1": 10, "ch2": 11}
        

    
    def set_sine_voltage(self, volt):
        """ A floating point property that represents the reference sine-wave
        voltage in Volts. This property can be set. """
        self.write(f'SLVL{volt:%0.3f}')
    def get_since_voltage(self):
        """ A floating point property that represents the reference sine-wave
        voltage in Volts"""
        ret = self.query('SLVL?')
        return ret
    
    def get_frequency(self):
        """ A floating point property that represents the lock-in frequency
        in Hz"""
        freq = float(self.query("FREQ?"))
        return freq
    def set_frequency(self, f):
        """ A floating point property that represents the lock-in frequency
        in Hz. This property can be set. """
        self.write(f'FREQ{f:%0.5e}')
        
    def set_phase(self, phase):
        """ A floating point property that represents the lock-in phase
        in degree. This property can be set. """
        self.write(f'PHAS{phase:%0.2f}')    
    def get_phase(self):
        """ A floating point property that represents the lock-in phase
        in degree."""
        phase = float(self.query('PHAS?'))
        return phase

    def get_x(self):
        """ Reads the X value in Volts. """
        x = float(self.query('OUTP?1'))
        return x
    def get_y(self):
        """ Reads the Y value in Volts. """
        y = float(self.query('OUTP?2'))
        return y
    def get_magnitude(self):
        """ Reads the magnitude in Volts. """
        magnitude = float(self.query("OUTP?3"))
        return magnitude
    def get_theta(self):
        """ Reads the theta value in degrees. """
        theta = float(self.query("OUTP?4"))
        return theta
    

    def get_sensitivity(self):
        """ A floating point property that controls the sensitivity in Volts,
        which can take discrete values from 2 nV to 1 V."""
        idx = int(self.query('SENS?'))
        return self.SENSITIVITIES[idx]
    def set_sensitivity(self, sens):
        """ A floating point property that controls the sensitivity in Volts,
        which can take discrete values from 2 nV to 1 V. Values are truncated 
        to the closest level if they are not exact. """
        idx = int(np.abs(np.array(self.SENSITIVITIES)-sens).argmin())
        self.write(f'SENS{idx}')
        
    def get_time_constant(self):
        idx = int(self.query("OFLT?"))
        return self.TIME_CONSTANTS[idx]
    def set_time_constant(self, tc):
        """ A floating point property that controls the time constant
        in seconds, which can take discrete values from 10 microseconds
        to 30,000 seconds. Values are truncated to the closest
        level if they are not exact. """
        idx = int(np.abs(np.array(self.TIME_CONSTANTS)-tc).argmin())
        self.write(f'OFLT{idx}')
        

    def get_filter_slope(self):
        idx = int(self.query("OFSL?"))
        return self.FILTER_SLOPES[idx]
    def set_filter_slopes(self, slope):
        """ An integer property that controls the filter slope, which
        can take on the values 6, 12, 18, and 24 dB/octave. Values are
        truncated to the closest level if they are not exact. """
        idx = int(np.abs(np.array(self.FILTER_SLOPES)-slope).argmin())
        self.write(f"OFSL{idx}")

    def get_harmonic(self):
        ret = int(self.query("HARM?"))
        return ret
    def set_harmonic(self, h):
        """ An integer property that controls the harmonic that is measured.
        Allowed values are 1 to 19999. Can be set. """
        self.write(f'HARM{int(h)}'),
        
    def get_input_config(self):
        idx = int(self.query("ISRC?"))
        return self.INPUT_CONFIGS[idx]
    def set_input_config(self, conf):
        """ An string property that controls the input configuration. Allowed
        values are: {}""".format(self.INPUT_CONFIGS)
        if conf in self.INPUT_CONFIGS:
            idx = self.INPUT_CONFIGS(conf)
        else:
            idx = 0
        self.write(f"ISRC {idx}")
    
    def get_input_coupling(self):
        idx = int(self.query("ICPL?"))
        return self.INPUT_COUPLINGS[idx]
    def set_input_coupling(self, cpl):
        """ An string property that controls the input coupling. Allowed
        values are: {}""".format(self.INPUT_COUPLINGS)
        if cpl in self.INPUT_COUPLINGS:
            idx = self.INPUT_COUPLINGS.index(cpl)
        else:
            idx = 0
        self.write(f"ICPL {idx}")


    
    def auto_gain(self):
        self.write("AGAN")

    def auto_reserve(self):
        self.write("ARSV")

    def auto_phase(self):
        self.write("APHS")

    def auto_offset(self, channel):
        """ Offsets the channel (X, Y, or R) to zero """
        if channel not in self.CHANNELS:
            raise ValueError('SR830 channel is invalid')
        channel = self.CHANNELS.index(channel) + 1
        self.write("AOFF %d" % channel)


    def output_conversion(self, channel):
        """ Returns a function that can be used to determine
        the signal from the channel output (X, Y, or R)
        """
        offset, expand = self.get_scaling(channel)
        sensitivity = self.sensitivity
        return lambda x: (x/(10.*expand) + offset) * sensitivity



 
    def aquireOnTrigger(self, enable=True):
        self.write("TSTR%d" % enable)

 

    def is_out_of_range(self):
        """ Returns True if the magnitude is out of range
        """
        return int(self.query("LIAS?2")) == 1

    def quick_range(self):
        """ While the magnitude is out of range, increase
        the sensitivity by one setting
        """
        self.write('LIAE 2,1')
        while self.is_out_of_range():
            self.write("SENS%d" % (int(self.query("SENS?"))+1))
            time.sleep(5.0*self.get_time_constant())
            self.write("*CLS")
        # Set the range as low as possible
        newsensitivity = 1.15*abs(self.get_magnitude())
        if self.get_input_config() in('I (1 MOhm)','I (100 MOhm)'):
            newsensitivity = newsensitivity*1e6
        self.set_sensitivity(newsensitivity)

    @property
    def buffer_count(self):
        query = self.ask("SPTS?")
        if query.count("\n") > 1:
            return int(re.match(r"\d+\n$", query, re.MULTILINE).group(0))
        else:
            return int(query)

    def fill_buffer(self, count, has_aborted=lambda: False, delay=0.001):
        ch1 = np.empty(count, np.float32)
        ch2 = np.empty(count, np.float32)
        currentCount = self.buffer_count
        index = 0
        while currentCount < count:
            if currentCount > index:
                ch1[index:currentCount] = self.buffer_data(1, index, currentCount)
                ch2[index:currentCount] = self.buffer_data(2, index, currentCount)
                index = currentCount
                time.sleep(delay)
            currentCount = self.buffer_count
            if has_aborted():
                self.pause_buffer()
                return ch1, ch2
        self.pauseBuffer()
        ch1[index:count+1] = self.buffer_data(1, index, count)
        ch2[index:count+1] = self.buffer_data(2, index, count)
        return ch1, ch2

    def buffer_measure(self, count, stopRequest=None, delay=1e-3):
        self.write("FAST0;STRD")
        ch1 = np.empty(count, np.float64)
        ch2 = np.empty(count, np.float64)
        currentCount = self.buffer_count
        index = 0
        while currentCount < count:
            if currentCount > index:
                ch1[index:currentCount] = self.buffer_data(1, index, currentCount)
                ch2[index:currentCount] = self.buffer_data(2, index, currentCount)
                index = currentCount
                time.sleep(delay)
            currentCount = self.buffer_count
            if stopRequest is not None and stopRequest.isSet():
                self.pauseBuffer()
                return (0, 0, 0, 0)
        self.pauseBuffer()
        ch1[index:count] = self.buffer_data(1, index, count)
        ch2[index:count] = self.buffer_data(2, index, count)
        return (ch1.mean(), ch1.std(), ch2.mean(), ch2.std())

    def pause_buffer(self):
        self.write("PAUS")

    def start_buffer(self, fast=False):
        if fast:
            self.write("FAST2;STRD")
        else:
            self.write("FAST0;STRD")

    def wait_for_buffer(self, count, has_aborted=lambda: False,
                        timeout=60, timestep=0.01):
        """ Wait for the buffer to fill a certain count
        """
        i = 0
        while not self.buffer_count >= count and i < (timeout / timestep):
            time.sleep(timestep)
            i += 1
            if has_aborted():
                return False
        self.pauseBuffer()

    def get_buffer(self, channel=1, start=0, end=None):
        """ Aquires the 32 bit floating point data through binary transfer
        """
        if end is None:
            end = self.buffer_count
        return self.binary_values("TRCB?%d,%d,%d" % (
                        channel, start, end-start))

    def reset_buffer(self):
        self.write("REST")

    def trigger(self):
        self.write("TRIG")

    def snap(self, val1="X", val2="Y", *vals):
        """ Method that records and retrieves 2 to 6 parameters at a single
        instant. The parameters can be one of: X, Y, R, Theta, Aux In 1,
        Aux In 2, Aux In 3, Aux In 4, Frequency, CH1, CH2.
        Default is "X" and "Y".

        :param val1: first parameter to retrieve
        :param val2: second parameter to retrieve
        :param vals: other parameters to retrieve (optional)
        """
        if len(vals) > 4:
            raise ValueError("No more that 6 values (in total) can be captured"
                             "simultaneously.")

        # check if additional parameters are given as a list
        if len(vals) == 1 and isinstance(vals[0], (list, tuple)):
            vals = vals[0]

        # make a list of all vals
        vals = [val1, val2] + list(vals)

        vals_idx = [str(self.SNAP_ENUMERATION[val.lower()]) for val in vals]

        command = "SNAP? " + ",".join(vals_idx)
        return self.values(command)



    def get_driver_model(self):
        model = []
        model.append({'name':'Magnitude', 'element':'variable', 'type':float, 'read':self.get_magnitude, 'unit':'V', 'help':'Simple help for magnitude variable'})
        model.append({'name':'Sensitivity', 'element':'variable', 'type':float, 'read':self.get_sensitivity, 'write':self.set_sensitivity, 'unit':'V', 'help':'Simple help for sensitivity variable'})
        model.append({'name':'TimeConstant', 'element':'variable', 'type':float, 'read':self.get_time_constant, 'write':self.set_time_constant, 'unit':'s', 'help':'Simple help for time constant variable'})
        model.append({'name':'Autoset', 'element':'action', 'do':self.quick_range, 'help':'While the magnitude is out of range, increase the sensitivity by one setting'})
        return model



#################################################################################
############################## Connections classes ##############################

class Driver_VISA(Driver):
    def __init__(self, address='GPIB0::9::INSTR'):
        import pyvisa as visa
        rm = visa.ResourceManager()
        self.inst = rm.open_resource(address)
        Driver.__init__(self)
        
    def query(self, command):
        self.inst.write(command)
        ret = self.read()
        return ret
    def write(self, command):
        self.inst.write(command)
    def read(self):
        ret = self.inst.read()
        return ret.strip('\n')
    def close(self):
        print('closing')
        self.inst.close()