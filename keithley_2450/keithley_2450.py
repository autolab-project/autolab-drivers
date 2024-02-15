#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified):
- Keithley 2450

Uses TSP commands
"""
from typing import Tuple, List


category = 'Source measure unit (SMU)'


class Driver():

    def __init__(self):
        self.write('*CLS')

        self.allowed_overvoltage_protection_limit = [
            2, 5, 10, 20, 40, 60, 80, 100, 120, 140, 180]
        self._tuple_measurement_sense = (["2-wire", "4-wire"], 0)
        self._tuple_measurement_func = (["voltage", "current", "resistance"], 0)
        self._tuple_source_func = (["voltage", "current"], 0)

    def _set_closest(self, allowed_list, value):
        a = allowed_list
        index = min(range(len(a)), key=lambda i: abs(a[i]-value))
        return a[index]

    def get_output_state(self) -> bool:
        return 'ON' in self.query("print(smu.source.output)")

    def set_output_state(self, state: bool):
        state = bool(int(float(state)))
        if state:
            self.write("smu.source.output = smu.ON")
        else:
            self.write("smu.source.output = smu.OFF")
        self.query('*OPC?')


    def get_wire(self) -> str:
        return self.query('print(smu.measure.sense)')

    def set_2wire_mode(self):
        self.write('smu.measure.sense = smu.SENSE_2WIRE')
        self.query('*OPC?')

    def set_4wire_mode(self):
        self.write('smu.measure.sense = smu.SENSE_4WIRE')
        self.query('*OPC?')

    def get_measurement_sense(self) -> Tuple[List[str], int]:
        ans = self.get_wire()
        list_sense = self._tuple_measurement_sense[0]
        if 'SENSE_2WIRE' in ans: return (list_sense, 0)
        elif 'SENSE_4WIRE' in ans: return (list_sense, 1)

    def set_measurement_sense(self, value: Tuple[List[str], int]):
        value = tuple(value)
        element = value[0][value[1]]
        if element == "2-wire": self.set_2wire_mode()
        elif element == "4-wire": self.set_4wire_mode()
        self._tuple_measurement_sense = value


    def get_measurement(self) -> str:
        return self.query('print(smu.measure.func)')

    def set_voltage_measurement(self):
        self.write('smu.measure.func = smu.FUNC_DC_VOLTAGE')

    def set_current_measurement(self):
        self.write('smu.measure.func = smu.FUNC_DC_CURRENT')

    def set_resistance_measurement(self):
        self.write('smu.measure.func = smu.FUNC_RESISTANCE')

    def get_measurement_func(self) -> Tuple[List[str], int]:
        ans = self.get_measurement()
        list_func = self._tuple_measurement_func[0]
        if 'FUNC_DC_VOLTAGE' in ans: return (list_func, 0)
        elif 'FUNC_DC_CURRENT' in ans: return (list_func, 1)
        elif 'FUNC_RESISTANCE' in ans: return (list_func, 2)

    def set_measurement_func(self, value: Tuple[List[str], int]):
        value = tuple(value)
        element = value[0][value[1]]
        if element == 'voltage': self.set_voltage_measurement()
        elif element == 'current': self.set_current_measurement()
        elif element == 'resistance': self.set_resistance_measurement()
        self._tuple_measurement_func = value


    def set_overvoltage_protection_limit(self, value: int):
        value = int(value)
        value = self._set_closest(
            self.allowed_overvoltage_protection_limit, value)
        self.write(f"smu.source.protect.level = smu.PROTECT_{value}V")
        self.query('*OPC?')

    def get_overvoltage_protection_limit(self) -> int:
        ans = self.query(
            "print(smu.source.protect.level)").lstrip('smu.PROTECT_').rstrip('V')
        return int(ans)


    def get_source(self):
        return self.query('print(smu.source.func)')

    def set_voltage_source(self):
        self.write('smu.source.func = smu.FUNC_DC_VOLTAGE')

    def set_current_source(self):
        self.write('smu.source.func = smu.FUNC_DC_CURRENT')

    def get_source_func(self) -> Tuple[List[str], int]:
        ans = self.get_source()
        list_func = self._tuple_source_func[0]
        if 'FUNC_DC_VOLTAGE' in ans: return (list_func, 0)
        elif 'FUNC_DC_CURRENT' in ans: return (list_func, 1)

    def set_source_func(self, value: Tuple[List[str], int]):
        value = tuple(value)
        element = value[0][value[1]]
        if element == 'voltage': self.set_voltage_source()
        elif element == 'current': self.set_current_source()
        self._tuple_source_func = value


    def get_source_limit(self) -> float:
        source = self.get_source()
        if source == 'smu.FUNC_DC_CURRENT':
            ans = float(self.query('print(smu.source.vlimit.level)'))
        elif source == 'smu.FUNC_DC_VOLTAGE':
            ans = float(self.query('print(smu.source.ilimit.level)'))
        else:
            ans = -1  # error
        return ans

    def set_source_limit(self, value: float):
        value = float(value)
        source = self.get_source()
        if source == 'smu.FUNC_DC_CURRENT':
            self.write(f"smu.source.vlimit.level = {value}")
        elif source == 'smu.FUNC_DC_VOLTAGE':
            self.write(f"smu.source.ilimit.level = {value}")

    def get_source_level(self) -> float:
        if self.get_output_state():
            ans = float(self.query('print(smu.source.level)'))
        else:
            ans = 0.
        return ans

    def set_source_level(self, value: float):
        value = float(value)
        self.write(f"smu.source.level = {value}")

    def get_measurement_level(self) -> float:
        if self.get_output_state():
            ans = float(self.query('print(smu.measure.read())'))
        else:
            ans = 0.
        return ans

    def get_id(self) -> str:
        return self.query('*IDN?')

    def get_driver_model(self):
        model = []

        model.append({'element': 'variable', 'name': 'output_state',
                      'type': bool,
                      'read': self.get_output_state, 'write': self.set_output_state,
                      'help': 'Output state'})

        model.append({'element': 'variable', 'name': 'wire_mode',
                      'type': tuple,
                      'read': self.get_measurement_sense, 'write': self.set_measurement_sense,
                      'help': 'Set wire mode between 2-wire (local) and 4-wire (remote)'})
        # model.append({'element':'variable','name':'wire_state','read':self.get_wire,'type':str,'help':'Wire mode'})
        # model.append({'element':'action','name':'2_wire_mode','do':self.set_2wire_mode,'type':bool,'help':'Two wire mode'})
        # model.append({'element':'action','name':'4_wire_mode','do':self.set_4wire_mode,'type':bool,'help':'Four wire mode'})

        model.append({'element': 'variable', 'name': 'measurement_type',
                      'type': tuple,
                      'read': self.get_measurement_func, 'write': self.set_measurement_func,
                      'help': 'Set measurement type between voltage, current and resistance'})
        # model.append({'element':'variable','name':'measurement','read':self.get_measurement,'type':str,'help':'Measurement type'})
        # model.append({'element':'action','name':'resistance_measurement','do':self.set_resistance_measurement,'type':bool,'help':'Resistance measurement'})
        # model.append({'element':'action','name':'voltage_measurement','do':self.set_voltage_measurement,'type':bool,'help':'Voltage measurement'})
        # model.append({'element':'action','name':'current_measurement','do':self.set_current_measurement,'type':bool,'help':'Current measurement'})

        model.append({'element': 'variable', 'name': 'source_type',
                      'type': tuple,
                      'read': self.get_source_func, 'write': self.set_source_func,
                      'help': 'Set source type between voltage and current'})
        # model.append({'element':'variable','name':'source','read':self.get_source,'type':str,'help':'Source type'})
        # model.append({'element':'action','name':'current_source','do':self.set_current_source,'help':'Source type: current'})
        # model.append({'element':'action','name':'voltage_source','do':self.set_voltage_source,'help':'Source type: voltage'})

        model.append({'element': 'variable', 'name': 'source_limit',
                      'type': float, 'unit': 'Volts or Amps',
                      'read': self.get_source_limit, 'write': self.set_source_limit,
                      'help': 'Source limit depend on the type of source in use (current or voltage).'})

        model.append({'element': 'variable', 'name': 'source_level',
                      'type': float, 'unit': 'Volts or Amps',
                      'read': self.get_source_level, 'write': self.set_source_level,
                      'help':'Source value to be used; unit depend on the type of source in use (current or voltage).'})

        model.append({'element': 'variable', 'name': 'measurement_level',
                      'type': float,'unit':' Volts or Amps or Ohms',
                      'read': self.get_measurement_level,
                      'help':'Measured value; unit depend on the type of measurement ("current", "voltage" or "resistance").'})

        model.append({'element': 'variable', 'name': 'overvoltage_protection_limit',
                      'type': int, 'unit': 'V',
                      'read': self.get_overvoltage_protection_limit, 'write': self.set_overvoltage_protection_limit,
                      'help': 'Overvoltage protection limit. Values accepted: 2, 5, 10, 20, 40, 60, 80, 100, 120, 140, 180'})

        return model


#################################################################################
############################## Connections classes ##############################
class Driver_VISA(Driver):
    def __init__(self, address='USB0::1510::9296::04062471::0::INSTR', **kwargs):
        import pyvisa as visa

        self.TIMEOUT = 5000  # ms
        # Instantiation
        rm = visa.ResourceManager()
        self.controller = rm.get_instrument(address)
        self.controller.timeout = self.TIMEOUT

        Driver.__init__(self)

    def close(self):
        try: self.controller.close()
        except: pass

    def query(self, command):
        result = self.controller.query(command)
        result = result.strip('\n')
        return result

    def write(self, command):
        self.controller.write(command)

    def read(self):
        result = self.controller.read()
        return result.strip('\n')
############################## Connections classes ##############################
#################################################################################
