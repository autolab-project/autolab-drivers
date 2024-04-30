# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 14:27:16 2024

@author: Hamza Dely, wrapped for combo-box by Victor
"""

import math
from typing import Tuple, List

class Driver:

    def __init__(self):
        # Tuple for the available source modes, 1st item is the modes list,
        # second is the index of the selected one 
        self._source_modes = (['VOLT', 'CURR'], 0)
        self._measure_modes = (['VOLT', 'CURR'], 0)  # May need to add RES for
        # resistance measurements later

        self._volt_source_ranges = (['20 mV', '200 mV', '2 V', '20 V', '200 V'],
                                    0)
        self._curr_source_ranges = (['10 nA', '100 nA', '1 \u03bcA', '10 \u03bcA',
                                     '100 \u03bcA', '1 mA', '10 mA', '100 mA',
                                     '1 A'], 0)

        self._volt_meas_ranges = (['20 mV', '200 mV', '2 V', '20 V', '200 V'],
                                  0)
        self._curr_meas_ranges = (['10 nA', '100 nA', '1 \u03bcA', '10 \u03bcA',
                                   '100 \u03bcA', '1 mA', '10 mA', '100 mA',
                                   '1 A'], 0)

        # Default buffer, may be configurable in a future version of the driver
        self._buffer = "defbuffer1"

        self.reset()
        self.get_source_mode()
        self.get_measure_mode()
        self.get_source_range()
        self.get_measurement_range()
        self.get_output_state()

    def _get_str_active_mode(self, mode_tuple: Tuple[List[str], int]) -> str:
        str_active_mode = mode_tuple[0][mode_tuple[1]]
        return str_active_mode

    def _str_range_to_float(self, str_range: str) -> float:
        units_dict = {'n': 1e-9,
                      '\u03bc': 1e-6,
                      'm': 1e-3,
                      '' : 1}
        sep = str_range.split(' ')
        core_value = float(sep[0])
        multiplier = units_dict[sep[1].strip('A').strip('V')]
        return core_value * multiplier    

    @property
    def source_mode(self) -> str:
        return self._get_str_active_mode(self._source_modes)
    
    @property
    def measure_mode(self) -> str:
        return self._get_str_active_mode(self._measure_modes)

    def reset(self):
        self.write('*CLS')
        self.write('*LANG SCPI') # Force SCPI 2450 commands mode
        self.write(':TRACe:CLEar') # Clear all buffers

    def get_source_mode(self) -> Tuple[List[str], int]:
        ret = self.query(":SOURce:FUNCtion?")
        self._source_modes = (self._source_modes[0],
                              self._source_modes[0].index(ret))
        self.get_source_range()
        return self._source_modes

    def set_source_mode(self, value: Tuple[List[str], int]):
        if value[0] != self._source_modes[0]:
            raise ValueError(
                f"Source mode '{value[0][value[1]]}' not supported."
            )

        self.write(f":SOURce:FUNCtion {value[0][value[1]]}")
        self.get_source_mode()

    def get_read_back_state(self) -> bool:
        return bool(int(
            self.query(f":SOURce:{self.source_mode}:READ:BACK?")
        ))

    def set_read_back_state(self, read_back_on: bool):
        new_state = 'ON' if read_back_on else 'OFF'
        self.write(f":SOURce:{self.source_mode}:READ:BACK {new_state}")

    def get_measure_mode(self) -> Tuple[List[str], int]:
        ret = self.query(":SENSe:FUNCtion?").strip('"').split(":")[0]
        self._measure_modes = (self._measure_modes[0],
                               self._measure_modes[0].index(ret))
        return self._measure_modes

    def set_measure_mode(self, value: Tuple[List[str], int]):
        if value[0] != self._measure_modes[0]:
            raise ValueError(
                f"Measurement mode '{value[0][value[1]]}' not supported."
            )

        self.write(f':SENSe:FUNCtion "{value[0][value[1]]}"')
        self.get_measure_mode()
        
    def get_current(self) -> float:
        function = None
        if self.source_mode == 'CURR':
            function = 'SOURce'
        elif self.measure_mode == 'CURR':
            function = 'READing'
            
        if function is None:
            raise RuntimeError("Current cannot be measured if not sourced or read.")

        return float(
            self.query(f':READ? "{self._buffer}", {function}')
        )

    def set_current(self, value: float):
        if not self.source_mode == 'CURR':
            raise RuntimeError("Current cannot be set if not sourced")

        value = float(value)
        self.write(f":SOURce:CURRent:LEVel {value}")
        self.query('*OPC?')

    def get_voltage(self) -> float:
        function = None
        if self.source_mode == 'VOLT':
            function = 'SOURce'
        elif self.measure_mode == 'VOLT':
            function = 'READing'
            
        if function is None:
            raise RuntimeError("Voltage cannot be measured if not sourced or read.")

        return float(
            self.query(f':READ? "{self._buffer}", {function}')
        )

    def set_voltage(self, value: float):
        if not self.source_mode == 'VOLT':
            raise RuntimeError("Voltage cannot be set if not sourced")
            
        value = float(value)
        self.write(f":SOURce:VOLTage:LEVel {value}")
        self.query('*OPC?')

    def get_source_range(self) -> Tuple[List[str], int]:
        # query the source range from the keithley for the selected mode
        source_range = float(self.query(f":SOURce:{self.source_mode}:RANGe?"))

        # Change the unit depending on the source mode
        unit = "V" if self.source_mode == 'VOLT' else "A"
        exponent = int(math.log10(source_range))
        unit_dict = {
            -1  : (1e3, 'm'),
            -2  : (1e6, '\u03bc'),
            -3  : (1e9, 'n'),
            -4  : (1e12, 'p'),
            -5  : (1e15, 'f'),
        }
        multiplier, prefix = unit_dict.get(exponent // 3, (1, ''))
        # Finally get a string compatible with the different range tuples
        str_range = f"{int(source_range * multiplier)} {prefix}{unit}"
        # exception to avoid values starting by zero
        if str_range[0] == '0':
            multiplier, prefix = unit_dict.get((exponent // 3) - 1, (1, ''))
            str_range = f"{int(source_range * multiplier)} {prefix}{unit}"

        if unit == 'V':
            self._volt_source_ranges = (self._volt_source_ranges[0],
                                        self._volt_source_ranges[0]
                                        .index(str_range))
            return self._volt_source_ranges
        else:
            self._curr_source_ranges = (self._curr_source_ranges[0],
                                        self._curr_source_ranges[0]
                                        .index(str_range))
            return self._curr_source_ranges

    def set_source_range(self, value: Tuple[List[str], int]):
        value = self._str_range_to_float(value[0][value[1]])
        self.write(f":SOURce:{self.source_mode}:RANGe {value:.1e}")
        self.get_source_range()

    def get_autorange_state(self) -> bool:
        return bool(int(
            self.query(f":SENSe:{self.source_mode}:RANGe:AUTO?")
        ))

    def set_autorange_state(self, autorange_on: bool):
        new_state = 'ON' if autorange_on else 'OFF'
        self.write(f":SENSe:{self.source_mode}:RANGe:AUTO {new_state}")

    def get_measurement_range(self) -> Tuple[List[str], int]:
        # When voltage source mode, measure limit on current and vice-versa
        unit = 'V' if self.measure_mode == 'VOLT' else 'A'

        # measure_limit = float(self.query(f":SOURce:{source_mode}:{mode}LIMit?"))
        measure_range = float(self.query(f":SENSe:{self.measure_mode}:RANGe:UPPer?"))
        exponent = int(math.log10(measure_range))
        unit_dict = {
            -1  : (1e3, 'm'),
            -2  : (1e6, '\u03bc'),
            -3  : (1e9, 'n'),
            -4  : (1e12, 'p'),
            -5  : (1e15, 'f'),
        }
        multiplier, prefix = unit_dict.get(exponent // 3, (1, ''))

        str_range = f"{int(measure_range * multiplier)} {prefix}{unit}"
        # exception to avoid values starting by zero
        if str_range[0] == '0':
            multiplier, prefix = unit_dict.get((exponent // 3) - 1, (1, ''))
            str_range = f"{int(measure_range * multiplier)} {prefix}{unit}"
        if self.measure_mode == 'VOLT':
            self._volt_meas_ranges = (self._volt_meas_ranges[0],
                                      self._volt_meas_ranges[0]
                                      .index(str_range))
            return self._volt_meas_ranges
        else:
            self._curr_meas_ranges = (self._curr_meas_ranges[0],
                                      self._curr_meas_ranges[0]
                                      .index(str_range))
            return self._curr_meas_ranges

    def set_measurement_range(self, value: Tuple[List[str], int]):
        value = self._str_range_to_float(value[0][value[1]])
        self.write(f':SENSe:{self.measure_mode}:RANGe:UPPer {value}')
        self.get_measurement_range()

    def get_source_limit(self) -> float:
        limit_type = 'V' if self.source_mode == 'CURR' else 'I'
        ret = self.query(f":SOURce:{self.source_mode}:{limit_type}LIMit:LEVel?")
        return float(ret)

    def set_source_limit(self, value: float):
        limit_type = 'V' if self.source_mode == 'CURR' else 'I'
        self.write(f":SOURce:{self.source_mode}:{limit_type}LIMit:LEVel {value:.2f}")
        
    def get_output_state(self) -> bool:
        return bool(int(self.query("OUTPUT?")))

    def set_output_state(self, turn_on: bool):
        new_state = 'ON' if bool(turn_on) else 'OFF'
        self.write(f"OUTPut {new_state}")

    def get_driver_model(self) -> List[dict]:
        model = []

        model.append({'element'     : 'variable',
                      'name'        : 'source_mode',
                      'type'        : tuple,
                      'read_init'   : True,
                      'read'        : self.get_source_mode,
                      'write'       : self.set_source_mode,
                      'help'        : 'Source mode : Voltage or Current.'})

        model.append({'element'     : 'variable',
                      'name'        : 'measurement_mode',
                      'type'        : tuple,
                      'read_init'   : True,
                      'read'        : self.get_measure_mode,
                      'write'       : self.set_measure_mode,
                      'help'        : ('Measurement mode : Voltage, Current'
                                       ' or Resistance.')})

        model.append({'element'     : 'variable',
                      'name'        : 'enable_read_back',
                      'type'        : bool,
                      'read_init'   : True,
                      'read'        : self.get_read_back_state,
                      'write'       : self.set_read_back_state,
                      'help'        : 'Perform readback of the source value.'})

        model.append({'element'     : 'variable',
                      'name'        : 'measurement_autorange',
                      'type'        : bool,
                      'read_init'   : True,
                      'read'        : self.get_autorange_state,
                      'write'       : self.set_autorange_state,
                      'help'        : 'Allow measurement autorange.'})
        
        model.append({
            'element'   : 'variable',
            'name'      : 'Voltage',
            'unit'      : 'V',
            'read'      : self.get_voltage,
            'write'     : self.set_voltage,
            'type'      : float,
            'help'      : 'Voltage at the output (sourced or measured)',
        })
        
        model.append({
            'element'   : 'variable',
            'name'      : 'Current',
            'unit'      : 'A',
            'read'      : self.get_current,
            'write'     : self.set_current,
            'type'      : float,
            'help'      : 'Current at the output (sourced or measured)',
        })

        model.append({'element'     : 'variable',
                      'name'        : 'source_range',
                      'type'        : tuple,
                      'read_init'   : True,
                      'read'        : self.get_source_range,
                      'write'       : self.set_source_range,
                      'help'        : 'Source range.'})

        model.append({'element'     : 'variable',
                      'name'        : 'measurement_range',
                      'type'        : tuple,
                      'read_init'   : True,
                      'read'        : self.get_measurement_range,
                      'write'       : self.set_measurement_range,
                      'help'        : 'Measurement range.'})

        model.append({'element'     : 'variable',
                      'name'        : 'source_limit',
                      'type'        : float,
                      'read_init'   : True,
                      'unit'        : 'V or A',
                      'read'        : self.get_source_limit,
                      'write'       : self.set_source_limit,
                      'help'        : ('Source upper limit, unit depends on'
                                       ' measurement mode')})
        
        model.append({'element'   : 'variable',
                      'name'      : 'Output',
                      'read'      : self.get_output_state,
                      'write'     : self.set_output_state,
                      'type'      : bool,
                      'help'      : 'Turn on/off the device output'})
        
        return model
# =============================================================================
# CONNECTION CLASS
# =============================================================================

class Driver_VISA(Driver):

    def __init__(self, address: str = 'USB0::0x05E6::0x2450::04081087::INSTR',
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