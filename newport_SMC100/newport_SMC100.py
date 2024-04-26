#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified):
- Newport smc100
"""
import time

category = 'Motion controller'


class Driver():

    slot_naming = 'slot<NUM> = <MODULE_NAME>'

    def __init__(self, **kwargs):

        # Submodules loading
        self.slot_names = {}
        prefix = 'slot'
        for key in kwargs.keys():
            if key.startswith(prefix) and not '_name' in key:
                slot_num = key[len(prefix): ]
                module_name = kwargs[key].strip()
                module_class = globals()[f'Module_{module_name}']
                if f'{key}_name' in kwargs.keys(): name = kwargs[f'{key}_name']
                else: name = f'{key}_{module_name}'
                setattr(self, name, module_class(self, slot_num))
                self.slot_names[slot_num] = name

    def get_driver_model(self):

        model = []
        for name in self.slot_names.values():
            model.append({'element': 'module', 'name': name, 'object': getattr(self, name)})
        return model

###############################################################################
############################ Connections classes ##############################
class Driver_VISA(Driver):
    def __init__(self, address='GPIB0::2::INSTR', **kwargs):
        import pyvisa as visa

        rm = visa.ResourceManager()
        self.controller = rm.open_resource(address)
        self.controller.baud_rate = 57600
        self.controller.flow_control = visa.constants.VI_ASRL_FLOW_XON_XOFF
        self.controller.read_termination = '\r\n'

        Driver.__init__(self, **kwargs)

    def query(self, command):
        return self.controller.query(command)

    def write(self, command):
        self.controller.write(command)

    def close(self):
        try: self.controller.close()
        except: pass
############################ Connections classes ##############################
###############################################################################


class Module_ILS100CC():

    def __init__(self, dev: Driver, slot: int):

        self.dev = dev
        self.SLOT = str(slot)

    def query(self, command, unwrap: bool = True):
        result = self.dev.query(self.SLOT+command)
        if unwrap:
            try:
                prefix = self.SLOT + command[0: 2]
                result = result.replace(prefix, '')
                result = result.strip()
                result = float(result)
            except:
                pass

        return result

    def write(self, command):
        self.dev.write(self.SLOT+command)

    def get_id(self) -> str:
        return self.query('ID?')

    def get_state(self) -> str:
        ans = self.query('TS?', unwrap=False)[-2: ]

        if ans[0] == '0':
            return 'NOTREF'
        elif ans == '14':
            return 'CONF'
        elif ans in ('1E','1F'):
            return 'HOMING'
        elif ans == '28':
            return 'MOVING'
        elif ans[0] == '3' and not ans[1].isalpha():
            return 'READY'
        elif ans[0] == '3' and ans[1].isalpha():
            return 'DISABLED'

        elif ans in ('0A', '0B', '0C', '0D', '0E', '0F', '10', '11'):
            return 'NOT REF'
        elif ans in ('32', '33', '34', '35'):
            return 'READY'
        elif ans in ('3C', '3D', '3E'):
            return 'DISABLED'

        elif ans in ('46', '47'):
            return 'JOGGING'
        else:
            return 'UNKNOWN'

    def set_ready_state(self):

        # On vérifie que l'on est pas dans le mode REF
        state = self.get_state()  # It may also be necessary to consider all the other possible prior states

        if state == 'CONF':
            self.write('1PW0')  # to not referenced
            time.sleep(0.5)
            print('going to Not ref')
            time.sleep(0.5)
            self.get_state()

        if state in ('NOTREF', 'NOT REF'):
            self.write('OR')  # Perfom Home search
            self.get_state()
            while self.get_state() == 'HOMING':
                time.sleep(0.5)
                print('Homing')
            self.get_state()

        state = self.get_state()  # check if I am in NOT REF
        if state== 'READY':
            print('Ready')

        if state == 'JOGGING':
            self.write('JD')  # Sortie du mode Jogging
            print('Sortie du mode Jogging')
        elif state == 'DISABLED':
            self.write('MM1')  # Sortie du mode disabled
            print('Sortie du mode DISABLED')
        self.wait_ready_state()
        self.get_state()

    def wait_ready_state(self):  # To be used only when it is going to ready state
        while self.get_state() != 'READY':
            time.sleep(0.1)


    def get_position(self) -> float:
        return self.query('PA?')

    def set_position(self, value: float):  # I need first to go to ready state
        self.set_ready_state()
        self.write('PA'+str(value))  # if no errors it returns back to ready state after, otherwise it will go to DISABLE state
        self.wait_ready_state()


    def get_acceleration(self) -> float:
        return self.query('AC?')

    def set_acceleration(self, value: float):
        self.set_ready_state()
        self.write('AC'+str(value))


    def get_driver_model(self):
        model = []
        model.append({'element': 'variable', 'name': 'position', 'type': float,
                      'read': self.get_position, 'write': self.set_position,
                      'help': 'Initiates an absolute move.'})
        model.append({'element': 'variable', 'name': 'acceleration', 'type': float,
                      'read': self.get_acceleration, 'write': self.set_acceleration,
                      'help': 'Changes the acceleration.'})
        return model
