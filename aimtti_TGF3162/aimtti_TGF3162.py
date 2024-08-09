#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified):
-
"""

from typing import List
import socket # library to communicate with instrument

import numpy as np


class Driver():
    """ Class that is inhirited by Driver_SOCKET or Driver_VISA, depending on
    which connection is needed.
    It has useful methods to communicate with instrument. """

    def __init__(self, nb_channels: int = 2):
        """ nb_channels: Number of channels ready for TTI """
        self.nb_channels = int(nb_channels)

        for i in range(1, self.nb_channels+1):
            setattr(self, f'channel{i}', Channel(self, i))

    def set_channel(self, value: int):
        value = int(value)
        self.write(f'CHN {value}')

    def get_channel(self) -> int:
        return int(self.query('CHN?'))

    def write_to_channel(self, channel: int, command: str):
        """ Function that write simple command to channel (used by class Channel) """
        self.set_channel(channel)
        self.write(command)

    def idn(self) -> str:
        """ Asks for status of device """
        return self.query('*IDN?')

    def reset(self):
        """ Resets the instrument parameters to their default values. """
        self.write("*RST")

    def get_driver_model(self) -> List[dict]:
        """ Used by autolab to create a device representation of the driver """
        model = []

        model.append({'element': 'variable', 'name': 'channel', 'type': int,
                      'read': self.get_channel, 'write': self.set_channel,
                      'help': 'Set active channel'})
        model.append({'element': 'action', 'name': 'reset',
                      'do': self.reset,
                      'help': 'Reset instrument state'})
        for num in range(1, self.nb_channels+1):
            model.append({'element': 'module', 'name': f'channel{num}',
                          'object': getattr(self, f'channel{num}'),
                          'help': f'Commands for channel{num}'})
        return model


#################################################################################
############################## Connections classes ##############################
class Driver_SOCKET(Driver):
    """ Class to initiate communication with instrument using socket.
    It inhirites atributs of Driver. """

    def __init__(self, address: str = '192.168.1.23', port: int = 9221,
                 **kwargs):
        """ adress and port ready for TTI """

        # create object for communicating with instrument
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # define timeout to 5 seconds
        self.s.settimeout(5)

        # connect
        self.s.connect((address, int(port)))

        # initiate Driver
        Driver.__init__(self, **kwargs)

    def write(self, command: str):
        """ Convert string command to bytes and send bytes """
        # Convert str to bytes and send bytes
        self.s.send((command+'\n').encode())

    def write_raw(self, command: bytes):
        """ Send command in bytes """
        self.s.send(command)

    def read(self, memory: int = 1000) -> str:
        """ Read from instrument, convert bytes to string and return string """
        rep = self.s.recv(memory).decode()
        return rep

    def read_raw(self, memory: int) -> bytes:
        """ Read from instrument, return bytes """
        rep = self.s.recv(memory)
        return rep

    def query(self, qry: str) -> str:
        """ Write and read string from instrument """
        self.write(qry)
        return self.read()

    def close(self):
        """ Close instrument connection """
        self.s.close()


# WARNING: didn't test pyvisa for this instrument
class Driver_VISA(Driver):
    """Class to initiate communication with instrument using VISA.
    It inherits attributes of Driver."""

    def __init__(self, address: str = 'TCPIP::192.168.1.23::9221::SOCKET',
                 **kwargs):
        """ adress ready for TTI """
        import pyvisa as visa
        # Initialize VISA resource manager
        self.rm = visa.ResourceManager()

        # Open connection to the instrument
        self.inst = self.rm.open_resource(address)

        # Set a timeout of 5000 milliseconds (5 seconds)
        self.inst.timeout = 5000

        # Initialize Driver
        Driver.__init__(self, **kwargs)

    def write(self, command: str):
        """ Send string command """
        self.inst.write(command)

    def write_raw(self, command: bytes):
        """ Send bytes command """
        self.inst.write_raw(command)

    def read(self) -> str:
        """ Read string from instrument """
        return self.inst.read()

    def read_raw(self, memory: int) -> bytes:
        """ Read bytes from instrument """
        return self.inst.read_raw(memory)

    # query instrument
    def query(self, qry: str) -> str:
        """ Write and read string from instrument """
        return self.inst.query(qry)

    def close(self):
        """ Close instrument connection """
        self.inst.close()
############################## Connections classes ##############################
#################################################################################


class Channel():
    """ Channel class with usful methods to communicate more easily with instrument.
    Take instrument object and channel number as arguments. """

    def __init__(self, dev, channel: int):
        """ dev: Driver instance, channel: channel number """
        self.dev = dev  # Driver_SOCKET or Driver_VISA
        self.CHANNEL = int(channel)

        self.arbitrary_waveform = ArbitraryWaveform(self)
        self.burst = Burst(self)
        self.modulation = Modulation(self)
        self.sweep = Sweep(self)

    def amplitude(self, amplitude: float):
        """ Define amplitude of signal """
        self.dev.write_to_channel(self.CHANNEL, f'AMPL {amplitude}')

    def frequency(self, frequency: float):
        """ Define frequency of signal """
        self.dev.write_to_channel(self.CHANNEL, f'FREQ {frequency}')

    def offset(self, offset: float):
        """ Define offset of signal """
        self.dev.write_to_channel(self.CHANNEL, f'DCOFFS {offset}')

    def set_output(self, state: str):
        """ Set output ON, OFF, NORMAL or INVERT """
        state = str(state).upper()
        self.dev.write_to_channel(self.CHANNEL, f'OUTPUT {state}')

    def set_mode(self, mode_name: str):
        """ Set waveform output. Accepted arguments are: SINE, SQUARE, RAMP,
        TRIANG PULSE, NOISE, PRBSPN7, PRBSPN9, PRBSPN11, PRBSPN15, PRBSPN20,
        PRBSPN23, PRBSPN29, PRBSPN31 and ARB """
        mode_name = str(mode_name).upper()
        self.dev.write_to_channel(self.CHANNEL, f'WAVE {mode_name}')

    def trigger(self):
        """ This command is the same as pressing the TRIGGER key. Its effect will
        depend on the context in which it is asserted. If the trigger source is
        manual and the generator is set to perform triggered burst or triggered
        sweep operation, this command sends a trigger pulse to the generator.
        If the trigger source is manual and the generator is set to perform
        gated burst operation, this command simply inverts the level of the
        manual trigger to high or low. """
        self.dev.write_to_channel(self.CHANNEL, '*TRG')

    def get_driver_model(self):
        model = []
        model.append({'element': 'variable', 'name': 'amplitude', 'type': float,
                      'write': self.amplitude, 'unit': 'Vpp',
                      'help': 'set the amplitude'})
        model.append({'element': 'variable', 'name': 'offset', 'type': float,
                      'write': self.offset, 'unit': 'V',
                      'help': 'Set the offset'})
        model.append({'element': 'variable', 'name': 'frequency', 'type': float,
                      'write': self.frequency, 'unit': 'Hz',
                      'help': 'Set the frequency'})
        model.append({'element': 'variable', 'name': 'output', 'type': str,
                      'write': self.set_output, 'help': 'Enable/disable the output. Accepted arguments are: ON, OFF'})
        model.append({'element': 'variable', 'name': 'mode', 'type': str,
                      'write': self.set_mode, 'help': 'Set the output mode. Accepted arguments are: SINE, SQUARE, RAMP, TRIANG, PULSE, NOISE, PRBSPN7, PRBSPN9, PRBSPN11, PRBSPN15, PRBSPN20, PRBSPN23, PRBSPN29, PRBSPN31, ARB'})
        model.append({'element': 'module', 'name': 'arbitrary_waveform',
                      'object': self.arbitrary_waveform,
                      'help': f'Manage arbitrary waveform for channel{self.CHANNEL}'})
        model.append({'element': 'module', 'name': 'burst',
                      'object': self.burst,
                      'help': f'Manage burst for channel{self.CHANNEL}'})
        model.append({'element': 'module', 'name': 'modulation',
                      'object': self.modulation,
                      'help': f'Manage modulation for channel{self.CHANNEL}'})
        model.append({'element': 'module', 'name': 'sweep',
                      'object': self.sweep,
                      'help': f'Manage sweep for channel{self.CHANNEL}'})
        model.append({'element': 'action', 'name': 'trigger',
                      'do': self.trigger,
                      'help': 'Send a trigger request'})

        return model


class ArbitraryWaveform:
    # OPTIMIZE: missing lots of functions
    def __init__(self, dev2):
        self.dev2 = dev2  # Channel

    def define_waveform(self, arb_chan: int, user_name: str, interpolation: str):
        """ Define an arbitrary waveform with user specified waveform name and
        waveform point interpolation state.
        Arguments:  arbitrary channel = 1, 2, 3, 4
                    user_name is the name you want for the function
                    interpolation = "ON", "OFF" depending if you want the TTI
                    to interpolate the wavefunction or not"""
        self.dev2.dev.write(f'ARBDEF ARB{arb_chan},{user_name},{interpolation}')

    def load_waveform(self, value: str):
        """ Set the output waveform type to <DC>, <SINC>, <HAVERSINE>, <CARDIAC>,
        <EXPRISE>, <LOGRISE>, <EXPFALL>, <LOGFALL>, <GAUSSIAN>, <LORENTZ>,
        <DLORENTZ>, <TRIANG>, <ARB1>, <ARB2>, <ARB3> or <ARB4>.
        The user specified name of the arbs stored in ARB1, ARB2, ARB3 or ARB4
        are also accepted as valid entries to change the waveform to ARB1, ARB2,
        ARB3 or ARB4 respectively. """
        if isinstance(value, int):  # Legacy behavior
            value = f'ARB{value}'
        value = str(value)  # not upper because can have custom name
        self.dev2.set_mode('ARB')
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'ARBLOAD {value}')

    def _write_array_to_byte(self, l: np.ndarray, arb_chan: int):
        """ Upload arbitrary waveform to device.
        Arguments: array, arbitrary waveform number to address the array to

        Note: ARB1 < BIN > Load data to an existing arbitrary waveform memory location ARB1.
        The data consists of two bytes per point with no characters between bytes or points.
        The point data is sent high byte first. The data block has a header which
        consists of the # character followed by several ascii coded numeric characters.
        The first of these defines the number of ascii characters to follow and
        these following characters define the length of the binary data in bytes.
        The instrument will wait for data indefinitely if less data is sent.
        If more data is sent the extra is processed by the command parser which
        results in a command error."""
        self.dev2.set_mode('ARB')

        # transform waveform to 2 bit unicode string with big endian convention (high byte first) and then encode to bytes
        a = l.astype('>u2').tobytes()

        # header components
        temp = str(2 * len(l))
        ARB = str(arb_chan)

        # build command to send
        qry = bytes(f'ARB{ARB} #{len(temp)}{temp}', 'ascii') + a + b' \n'
        # send command
        self.dev2.dev.write_raw(qry)
        self.dev2.dev.query('*OPC?') # useless according to the documentation as all commands are sequential (the instrument always waits for the command to be completed before continuing in the command queue).

    def send_waveform(self, waveform: np.ndarray, arb_chan: int):
        """ Format, encode and send waveform to channel number 'arb_chan' of instrument. """
        # Raise error if waveform is too big
        assert len(waveform) <= 2**(13), 'Waveform array too big. Maximum length is 2**(13)=8192'

        # Normalize wavefunction to range ]-1,1[
        waveform = scale_waveform(waveform)

        # We encode the range ]1,-1[ to a 16 bit resolution, that is the new range is ]-2**(16)/2 ,2**(16)/2[ = ]-32768,32768[
        waveform = waveform * 2**(16-1)

        # Upload waveform to device
        self._write_array_to_byte(waveform, arb_chan)

    def send_waveform_1(self, waveform: np.ndarray):
        self.send_waveform(waveform, 1)

    def send_waveform_2(self, waveform: np.ndarray):
        self.send_waveform(waveform, 2)

    def send_waveform_3(self, waveform: np.ndarray):
        self.send_waveform(waveform, 3)

    def send_waveform_4(self, waveform: np.ndarray):
        self.send_waveform(waveform, 4)

    def read_waveform(self, arb_chan: int) -> np.ndarray:
        """ Read waveform data in channel number 'arb_chan' memory and convert to float array """
        # Read definition of waveform to get number of points in memory
        definition = self.dev2.dev.query(f'ARB{arb_chan}DEF?')
        nbpts = int(definition.split(',')[2])

        # Calculate memory that is going to be sent ( header included )
        memory = nbpts*2 + 2*len(str(nbpts * 2)) + 4

        # Download data
        self.dev2.dev.write(f'ARB{arb_chan}?')
        data = self.dev2.dev.read_raw(memory)

        # get length of header
        H = int(chr(data[1]))
        index = H + 2

        # decode data. The datatype must be >i2 not >u2 so that np.frombuffer considers negatives integers as well
        waveform = np.array(
            np.frombuffer(data[index:], dtype='>i2', count=nbpts),
            dtype=float, copy=False)

        # transform data back to ]-1,1[ range
        waveform = waveform / (2**(16-1))

        return waveform

    def read_waveform_1(self) -> np.ndarray:
        return self.read_waveform(1)

    def read_waveform_2(self) -> np.ndarray:
        return self.read_waveform(2)

    def read_waveform_3(self) -> np.ndarray:
        return self.read_waveform(3)

    def read_waveform_4(self) -> np.ndarray:
        return self.read_waveform(4)

    def get_driver_model(self):
        model = []

        model.append({'element': 'action', 'name': 'load', 'param_type': str,
                      'do': self.load_waveform,
                      'help': 'Set the output waveform type to <DC>, <SINC>, <HAVERSINE>, <CARDIAC>, <EXPRISE>, <LOGRISE>, <EXPFALL>, <LOGFALL>, <GAUSSIAN>, <LORENTZ>, <DLORENTZ>, <TRIANG>, <ARB1>, <ARB2>, <ARB3> or <ARB4>.'})
        model.append({'element': 'variable', 'name': 'waveform_1', 'type': np.ndarray,
                      'read': self.read_waveform_1, 'write': self.send_waveform_1,
                      'help': 'Set/Read arbitrary waveform in location ARB1'})
        model.append({'element': 'variable', 'name': 'waveform_2', 'type': np.ndarray,
                      'read': self.read_waveform_2, 'write': self.send_waveform_2,
                      'help': 'Set/Read arbitrary waveform in location ARB2'})
        model.append({'element': 'variable', 'name': 'waveform_3', 'type': np.ndarray,
                      'read': self.read_waveform_3, 'write': self.send_waveform_3,
                      'help': 'Set/Read arbitrary waveform in location ARB3'})
        model.append({'element': 'variable', 'name': 'waveform_4', 'type': np.ndarray,
                      'read': self.read_waveform_4, 'write': self.send_waveform_4,
                      'help': 'Set/Read arbitrary waveform in location ARB4'})
        return model


class Burst:
    """ All available burst functions """
    def __init__(self, dev2):
        self.dev2 = dev2  # Channel

    def set_trigger_source(self, value: str):
        """ Set the burst trigger source to <INT>, <EXT> or <MAN> """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'BSTTRGSRC {value}')

    def set_trigger_period(self, value: float):
        """ Set the burst trigger period in sec. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'BSTPER {value}')

    def set_trigger_slope(self, value: str):
        """ Set the burst trigger slope to <POS> or <NEG>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'BSTTRGPOL {value}')

    def set_count(self, value: int):
        """ Set the burst count to n cycles. """
        value = int(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'BSTCOUNT {value}')

    def set_phase(self, value: float):
        """ Set the burst phase in degree. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'BSTPHASE {value}')

    def set_type(self, value: str):
        """ Set the burst to <OFF>, <NCYC>, <GATED> or <INFINITE>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'BST {value}')

    def get_driver_model(self):
        model = []

        model.append({'element': 'variable', 'name': 'trigger_source', 'type': str,
                      'write': self.set_trigger_source,
                      'help': 'Set the burst trigger source to <INT>, <EXT> or <MAN>'})
        model.append({'element': 'variable', 'name': 'trigger_period', 'type': float,
                      'write': self.set_trigger_period, 'unit': 's',
                      'help': 'Set the burst trigger period in sec.'})
        model.append({'element': 'variable', 'name': 'trigger_slope', 'type': str,
                      'write': self.set_trigger_slope,
                      'help': 'Set the burst trigger slope to <POS> or <NEG>.'})
        model.append({'element': 'variable', 'name': 'count', 'type': int,
                      'write': self.set_count,
                      'help': 'Set the burst count to n cycles.'})
        model.append({'element': 'variable', 'name': 'phase', 'type': float,
                      'write': self.set_phase, 'unit': '°',
                      'help': 'Set the burst phase in degree.'})
        model.append({'element': 'variable', 'name': 'type', 'type': str,
                      'write': self.set_type,
                      'help': 'Set the burst to <OFF>, <NCYC>, <GATED> or <INFINITE>.'})
        return model


class Modulation:
    # OPTIMIZE: missing lots of functions
    def __init__(self, dev2):
        self.dev2 = dev2  # Channel

    def set_type(self, value: str):
        """ Set modulation to <OFF>, <AM>, <AMSC>, <FM>, <PM>, <ASK>, <FSK>,
        <SUM>, <BPSK> or <PWM> """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'MOD {value}')

    def set_fm_shape(self, value: str):
        """ Set FM waveform shape to <SINE>, <SQUARE>, <RAMPUP>, <RAMPDN>,
        <TRIANG>, <NOISE>, <DC>, <SINC>, <EXPRISE>, <LOGRISE>, <EXPFALL>,
        <LOGFALL>, <HAVERSINE>, <CARDIAC>, <GAUSSIAN>, <LORENTZ>, <DLORENTZ>,
        <ARB1>, <ARB2>, <ARB3>, <ARB4>, <PRBSPN7>, <PRBSPN9>, <PRBSPN11>,
        <PRBSPN15>, <PRBSPN20>, <PRBSPN23>, <PRBSPN29> or < PRBSPN31> """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'MODFMSHAPE {value}')

    def set_fm_source(self, value: str):
        """ Set FM waveform source to <INT> or <EXT> """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'MODFMSRC {value}')

    def set_fm_deviation(self, value: float):
        """ Set FM waveform deviation in Hz """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'MODFMDEV {value}')

    def set_fm_frequency(self, value: float):
        """ Set FM waveform frequency in Hz """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'MODFMFREQ {value}')

    def get_driver_model(self):
        model = []

        model.append({'element': 'variable', 'name': 'type', 'type': str,
                      'write': self.set_type,
                      'help': 'Set modulation to <OFF>, <AM>, <AMSC>, <FM>, <PM>, <ASK>, <FSK>, <SUM>, <BPSK> or <PWM>'})
        model.append({'element': 'variable', 'name': 'fm_shape', 'type': str,
                      'write': self.set_fm_shape,
                      'help': 'Set FM waveform shape to <SINE>, <SQUARE>, <RAMPUP>, <RAMPDN>, <TRIANG>, <NOISE>, <DC>, <SINC>, <EXPRISE>, <LOGRISE>, <EXPFALL>, <LOGFALL>, <HAVERSINE>, <CARDIAC>, <GAUSSIAN>, <LORENTZ>, <DLORENTZ>, <ARB1>, <ARB2>, <ARB3>, <ARB4>, <PRBSPN7>, <PRBSPN9>, <PRBSPN11>, <PRBSPN15>, <PRBSPN20>, <PRBSPN23>, <PRBSPN29> or < PRBSPN31>'})
        model.append({'element': 'variable', 'name': 'fm_source', 'type': str,
                      'write': self.set_fm_source,
                      'help': 'Set FM waveform source to <INT> or <EXT>'})
        model.append({'element': 'variable', 'name': 'fm_deviation', 'type': float,
                      'write': self.set_fm_deviation, 'unit': 'Hz',
                      'help': 'Set FM waveform deviation in Hz'})
        model.append({'element': 'variable', 'name': 'fm_frequency', 'type': float,
                      'write': self.set_fm_frequency, 'unit': 'Hz',
                      'help': 'Set FM waveform frequency in Hz'})
        return model


class Sweep:
    """ All available sweep functions """
    def __init__(self, dev2):
        self.dev2 = dev2  # Channel

    def set_state(self, value: str):
        """ Set the sweep to <ON> or <OFF>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWP {value}')

    def set_type(self, value: str):
        """ Set the sweep type to <LINUP>, <LINDN>, <LOGUP> or <LOGDN>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPTYPE {value}')

    def set_mode(self, value: str):
        """ Set the sweep mode to <CONT> or <TRIG>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPMODE {value}')

    def set_trigger_source(self, value: str):
        """ Set the sweep trigger source to <INT>, <EXT> or <MAN>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPTRGSRC {value}')

    def set_trigger_period(self, value: float):
        """ Set the sweep trigger period in sec. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPTRGPER {value}')

    def set_trigger_slope(self, value: str):
        """ Set the sweep trigger slope to <POS> or <NEG>. """
        value = str(value).upper()
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPTRGPOL {value}')

    def set_start(self, value: float):
        """ Set the sweep start frequency in Hz. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPBEGFREQ {value}')

    def set_stop(self, value: float):
        """ Set the sweep stop frequency in Hz. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPENDFREQ {value}')

    def set_center(self, value: float):
        """ Set the sweep center frequency in Hz. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPCNTFREQ {value}')

    def set_span(self, value: float):
        """ Set the sweep span frequency in Hz. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPSPNFREQ {value}')

    def set_time(self, value: float):
        """ Set the sweep time in sec. """
        value = float(value)
        self.dev2.dev.write_to_channel(self.dev2.CHANNEL, f'SWPTIME {value}')

    def get_driver_model(self):
        model = []

        model.append({'element': 'variable', 'name': 'state', 'type': str,
                      'write': self.set_state,
                      'help': 'Set the sweep to <ON> or <OFF>.'})
        model.append({'element': 'variable', 'name': 'type', 'type': str,
                      'write': self.set_type,
                      'help': 'Set the sweep type to <LINUP>, <LINDN>, <LOGUP> or <LOGDN>.'})
        model.append({'element': 'variable', 'name': 'mode', 'type': str,
                      'write': self.set_mode,
                      'help': 'Set the sweep mode to <CONT> or <TRIG>.'})
        model.append({'element': 'variable', 'name': 'trigger_source', 'type': str,
                      'write': self.set_trigger_source,
                      'help': 'Set the sweep trigger source to <INT>, <EXT> or <MAN>.'})
        model.append({'element': 'variable', 'name': 'trigger_period', 'type': float,
                      'write': self.set_trigger_period, 'unit': 's',
                      'help': 'Set the sweep trigger period in sec.'})
        model.append({'element': 'variable', 'name': 'trigger_slope', 'type': str,
                      'write': self.set_trigger_slope,
                      'help': 'Set the sweep trigger slope to <POS> or <NEG>.'})
        model.append({'element': 'variable', 'name': 'start', 'type': float,
                      'write': self.set_start, 'unit': 'Hz',
                      'help': 'Set the sweep start frequency in Hz.'})
        model.append({'element': 'variable', 'name': 'stop', 'type': float,
                      'write': self.set_stop, 'unit': 'Hz',
                      'help': 'Set the sweep stop frequency in Hz.'})
        model.append({'element': 'variable', 'name': 'center', 'type': float,
                      'write': self.set_center, 'unit': 'Hz',
                      'help': 'Set the sweep center frequency in Hz.'})
        model.append({'element': 'variable', 'name': 'span', 'type': float,
                      'write': self.set_span, 'unit': 'Hz',
                      'help': 'Set the sweep span frequency in Hz.'})
        model.append({'element': 'variable', 'name': 'time', 'type': float,
                      'write': self.set_time, 'unit': 's',
                      'help': 'Set the sweep time in sec.'})

        return model


def scale_waveform(waveform: np.ndarray) -> np.ndarray:
    """ Scale waveform to required ]-1,1[ range """
    # Ensure the waveform is a NumPy array
    waveform = np.array(waveform, dtype=float, copy=False)

    # Find the minimum and maximum values
    min_val = np.min(waveform)
    max_val = np.max(waveform)

    # Scale to the range [0, 1]
    waveform_normalized = (waveform - min_val) / (max_val - min_val)

    # Scale to the range ]-1, 1[
    waveform_scaled = 2 * waveform_normalized - 1

    # Exclude exact -1 and 1
    # epsilon = np.finfo(float).eps  # Machine epsilon for float type
    epsilon = 1e-5
    waveform_scaled = np.clip(waveform_scaled, -1+epsilon, 1-epsilon)

    return waveform_scaled
