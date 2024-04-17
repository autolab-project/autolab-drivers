# -*- coding: utf-8 -*-
"""
Created on Thu Apr 11 16:34:55 2024

@author: Victor

Note : Using SCPI commands and not API
Tested on Anapico APULN40, may need to change hardcoded values for other models
"""

import numpy as np

category = 'Synthesized signal generators'
# =============================================================================
# INSTRUMENT CLASS
# =============================================================================

class Driver():

    def __init__(self):
        # Hardcoding the frequency limits of the source
        self._lowest_frequency_in_ghz = 1e-4
        self._highest_frequency_in_ghz = 42
        
        # Hardcoding the power limits of the source
        self._lowest_power_in_dbm = -30  # not the actual min, but sys accepts
        self._highest_power_in_dbm = 30  # not the actual max, but sys accepts
        
        # Hardcoding the phase limits
        self._lowest_phase_in_degrees = 0
        self._highest_phase_in_degrees = 360

    def get_id(self) -> str:
        return self.query('*IDN?')

    def _query_to_freq_in_ghz(self, ret: str) -> float:
        return float(ret) * 1e-9

    def _check_within_limits_and_return_acceptable_value(
            self, val: float, lowest: float, highest: float) -> float:
        if np.logical_and(val <= highest, val >= lowest):
            return val
        elif val <= lowest:
            return lowest
        else:
            return highest

    def get_frequency_in_ghz(self) -> float:
        ret = self.query(":SOUR:FREQ:CW?")
        return self._query_to_freq_in_ghz(ret)

    def set_frequency_in_ghz(self, freq_in_ghz: float):
        # First make sure that the value is in actual limits
        freq_in_ghz = self._check_within_limits_and_return_acceptable_value(
            freq_in_ghz, self._lowest_frequency_in_ghz,
            self._highest_frequency_in_ghz)
        # 12 decimals precision to match the precision on the screen
        self.write(f":SOUR:FREQ:CW {freq_in_ghz * 1e9:.12f}")
        self.query("*OPC?")

    def get_power_in_dbm(self) -> float:
        ret = self.query(":SOUR:POW:LEV:IMM:AMPL?")
        return float(ret)

    def set_power_in_dbm(self, power_in_dbm: float):
        power_in_dbm = self._check_within_limits_and_return_acceptable_value(
            power_in_dbm, self._lowest_power_in_dbm,
            self._highest_power_in_dbm)
        # 6 decimals for the precision of the instrument
        self.write(f":SOUR:POW:LEV:IMM:AMPL {power_in_dbm:.6f}")
        self.query("*OPC?")

    def get_output_state(self) -> bool:
        # grabs the output state from the instrument directly
        ret = self.query("OUTP:STAT?")  # ret is either '1';'0' or "ON";"OFF"
        if len(ret) > 1:
            ans = 1 if ret == "ON" else 0
        else:
            ans = ret
        return bool(int(ans))  # convert it to true or false

    def set_output_state(self, state: bool):
        back_to_bit = int(state)
        # Write 0 or 1 to the instrment for the output state
        self.write(f":OUTP:STAT {back_to_bit:d}")
        self.query("*OPC?")

    def get_phase_in_degrees(self) -> float:
        ret = self.query(":SOUR:PHAS?")  # ret is by default in rad, and str
        ret_in_deg = float(ret) * 360 / (2 * np.pi)  # convert in degrees
        return ret_in_deg

    def set_phase_in_degrees(self, phase: float):
        phase = self._check_within_limits_and_return_acceptable_value(
            phase, self._lowest_phase_in_degrees,
            self._highest_phase_in_degrees)
        # 9 decimals precision for the phase
        self.write(f":SOUR:PHAS:ADJ {phase:.9f} deg")
        self.query("*OPC?")

    def get_driver_model(self):
        model = []

        model.append({'element': 'variable', 'name': 'Frequency',
                      'unit': 'GHz', 'type': float,
                      'read': self.get_frequency_in_ghz,
                      'write': self.set_frequency_in_ghz,
                      'help': 'Output frequency of the synthesizer in GHz.'})

        model.append({'element': 'variable', 'name': 'Power',
                      'unit': 'dBm', 'type': float,
                      'read': self.get_power_in_dbm,
                      'write': self.set_power_in_dbm,
                      'help': 'Output power of the synthesizer in dBm.'})

        model.append({'element': 'variable', 'name': 'Phase',
                      'unit': 'deg', 'type': float,
                      'read': self.get_phase_in_degrees,
                      'write': self.set_phase_in_degrees,
                      'help': 'Output phase of the synthesizer in degrees.'})

        model.append({'element': 'variable', 'name': 'Output',
                      'type': bool, 'read': self.get_output_state,
                      'write': self.set_output_state,
                      'help': 'Turn ON/OFF the source using this tickbox.'})
        return model
        
# =============================================================================
# CONNECTION CLASS
# =============================================================================

class Driver_VISA(Driver):

    def __init__(self, address="USB0::0x03EB::0xAFFF::1F1-3C5G00001-2716::INSTR",
                 **kwargs):
        
        import pyvisa as visa
        self.TIMEOUT = 5000  # Default timeout of 5s

        # Instanciation
        rm = visa.ResourceManager()
        self.controller = rm.open_resource(address)
        self.controller.timeout = self.TIMEOUT
        
        Driver.__init__(self)

    def close(self):
        # Avoid returning error when closing, can still go back to local
        try:
            self.controller.close()
        except:
            pass

    # How to query sth with this specific connection
    def query(self, command: str) -> str:
        result = self.controller.query(command)
        result = str(result.strip('\n'))
        return result

    # How to write to the instrument with this connection
    def write(self, command: str):  # SCPI, write strings only
        self.controller.write(command)
