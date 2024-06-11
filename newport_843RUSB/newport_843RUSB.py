"""
Newport 843-R-USB power meter console
Requires separate install of newport PowerMeter Manager software (PMManager)
Requires additional python modules:
    pywin32 (includes win32com and pythoncom below)
"""

import win32com.client
import time
import traceback
import pythoncom
from typing import Tuple, List

category = 'Power meter'


class Driver():
    
    def __init__(self):
        ## Start streaming data by default
        self.start_stream()

    ########### Data stream initialization functions
    def start_stream(self):
        """
        Starts streaming data

        Returns
        -------
        None.

        """
        try:
            self.OphirCOM.StartStream(self.instr, self.channel)		# start measuring
            
        except win32com.client.pythoncom.com_error as e:
            args = e.args
            if args[2][2]=='Channel is in Stream Mode': 
                pass
            else:
                print(f'Start stream returned error message {e}')
                
    def stop_stream(self):
        """
        Stop streaming data. Necessary to execute this before changing any setting

        Returns
        -------
        None.

        """
        try: 
            self.OphirCOM.StopStream(self.instr, self.channel) # stop measuring
        except win32com.client.pythoncom.com_error as e:
            args = e.args
            if args[2][2]=='Stream Mode Not Started': 
                pass
            else:
                print(f'stop stream returned error message {e}')


    ############ Instrument settings
    def set_range(self, meas_range : Tuple [List[str], int]):
        """
        Sets the data range.

        Parameters
        ----------
        meas_range : Tuple [List[str], int]
            Tuple of available options (list) and index of the option in the list.

        Returns
        -------
        None.

        """
        _, idx = meas_range
        self.stop_stream()
        self.OphirCOM.SetRange(self.instr, self.channel, idx)
        self.start_stream()
        
    def get_range(self) -> Tuple[List[str], int]:
        """
        Gets the available data ranges

        Returns
        -------
        (Tuple[List[str], int])
            Tuple of (options, index) with index of the current data range.

        """
        idx, rlist = self.OphirCOM.GetRanges(self.instr, self.channel)
        return tuple([list(rlist), idx])


    def set_wavelength(self, wl : Tuple[List[str], int]):
        """
        Sets the current wavelength

        Parameters
        ----------
        wl : Tuple[List[str], int]
            Tuple of (option, index) of the wavelength.

        Returns
        -------
        None.

        """
        _, idx = wl
        self.stop_stream()
        self.OphirCOM.SetWavelength(self.instr, self.channel, idx)
        self.start_stream()
        
    def get_wavelength(self) -> Tuple[List[str], int]:
        """
        Get the current wavelength in the list of options

        Returns
        -------
        (Tuple[List[str], int])
            Tuple of (options, index) with index of the current value.

        """
        idx, wllist = self.OphirCOM.GetWavelengths(self.instr, self.channel)
        return tuple([list(wllist), idx])
    
    def modify_wavelength(self, wl):
        """
        Change the value of the wavelength at the current memory position

        Parameters
        ----------
        wl : float
            Wavelength to set at the current memory position.

        Returns
        -------
        None.

        """
        self.stop_stream()
        _, idx = self.get_wavelength()
        self.OphirCOM.ModifyWavelength(self.instr, self.channel, idx, wl)
        self.start_stream()
    def get_modified_wavelength(self):
        """
        Gets the wavelength at the memory position - to check it has been modified

        Returns
        -------
        wl : float
            Wavelength.

        """
        wls, idx = self.get_wavelength()
        wl = float(wls[idx])
        return wl
    
    def set_mode(self, mode : Tuple[List[str], int]):
        """
        Set the measurement mode to power or energy

        Parameters
        ----------
        mode : Tuple[List[str], int]
            Measurement mode (options, index).

        Returns
        -------
        None.

        """
        _, idx = mode
        self.stop_stream()
        self.OphirCOM.SetMeasurementMode(self.instr, self.channel, idx)
        self.start_stream()
        
    def get_mode(self) -> Tuple[List[str], int]:
        """
        Get the current measurement mode

        Returns
        -------
        (Tuple[List[str], int])
            (options, index) of the current mode.

        """
        idx, modes = self.OphirCOM.GetMeasurementMode(self.instr, self.channel)
        return tuple([list(modes), idx])
    
    ############ Measurements
    def amplitude(self) -> float:
        """
        Value of the measurement. Power or Energy depending on the mode.

        Returns
        -------
        float
            DESCRIPTION.

        """
        data = self.OphirCOM.GetData(self.instr, self.channel)
        if len(data[0])>0:
            return data[0][0]
        else:
            while len(data[0]) == 0:
                time.sleep(0.05)
                data = self.OphirCOM.GetData(self.instr, self.channel)
            return data[0][0]
            

        
    def get_driver_model(self):
        model = []
        
        
        model.append({'element': 'variable', 'name': 'range', 'type': tuple,
                      'read_init': True, 'read': self.get_range, 'write': self.set_range,
                      'help': 'Measurement range'})
        model.append({'element': 'variable', 'name': 'wavelength', 'type': tuple,
                      'read_init': True, 'read': self.get_wavelength, 'write': self.set_wavelength,
                      'help': 'Laser Wavelength'})
        model.append({'element': 'variable', 'name':'ModifyWavelength', 'type': float, 
                      'read': self.get_modified_wavelength,'write': self.modify_wavelength})
        
        model.append({'element': 'variable', 'name': 'amplitude', 'type': float,
                      'read': self.amplitude, 
                      'help': 'Power or Energy'})
        
        model.append({'element': 'variable', 'name': 'mode', 'type': tuple,
                      'read_init': True, 'read': self.get_mode, 'write': self.set_mode,
                      'help': 'Measurement mode (energy or power)'})
        
        
        model.append({'element':'action','name':'zero','do':self.zero,                       
                       'help':'Sets the zeroing value with the present reading.'})
        
        return model



class Driver_DLL(Driver):
    def __init__(self, SN = '916202'):
        pythoncom.CoInitialize()
        self.Device = SN
        self.channel = 0
        
        self.OphirCOM = win32com.client.Dispatch("OphirLMMeasurement.CoLMMeasurement")
        # Stop & Close all devices ### Maybe dangerous if several pmeter attached..?
        self.OphirCOM.StopAllStreams() 
        self.OphirCOM.CloseAll()
        DeviceList = self.OphirCOM.ScanUSB() # Scan for connected Devices, needed to recognize device below
        
        try:
            self.instr = self.OphirCOM.OpenUSBDevice(self.Device)	# open first device
            exists = self.OphirCOM.IsSensorExists(self.instr, self.channel)
            if exists:
                print(f'Successfully connected to powermeter interface with SN {self.Device}')
            else:
                print('Could not connect to powermeter interface')
        except OSError as err:
            print("OS error: {0}".format(err))
        except win32com.client.pythoncom.com_error as e:
            print(f'Connection returned an error: \n {e}')
        except:
            traceback.print_exc()        
    
        Driver.__init__(self)
    

    
    def close(self):
        self.stop_stream()
        self.OphirCOM.Close(self.instr)
        self.OphirCOM = None
        print('Close newport powermeter')
        