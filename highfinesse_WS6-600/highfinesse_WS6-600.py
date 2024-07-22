#!/usr/bin/env python3

"""
Supported instruments (identified): highfinesse_WS6-600
-
"""
import os
import sys
import ctypes as ct
import time

if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.dirname(__file__))  # needed for wlmConst import
import wlmConst as wc


class Driver():

    def __init__(self):
        self.error = "No error"

    def start_server(self, hide: bool = True):
        if hide:
            out = self.controller.ControlWLM(wc.cCtrlWLMHide, 0, 0)
        else:
            out = self.controller.ControlWLM(wc.cCtrlWLMShow, 0, 0)
        if out == wc.flServerStarted:
            while self.controller.GetWLMCount(0) == 0:
                time.sleep(0.1)
            time.sleep(0.1)

    def start_measurement(self):
        self.controller.Operation(wc.cCtrlStartMeasurement)
        time.sleep(1)

    def stop_measurement(self):
        self.controller.Operation(wc.cCtrlStopAll)

    def set_measurement_state(self, state: bool):
        if state:
            self.start_measurement()
        else:
            self.stop_measurement()

    def get_wavelength(self) -> float:
        try:
            exposure = self.get_exposure()
            assert exposure > 0
            time.sleep(exposure*1e-3)
        except AssertionError:
            pass
        out = self.controller.GetWavelength(0)
        self.error = "No error"
        if out == wc.ErrNoValue: self.error = "No value"
        if out == wc.ErrNoSignal: self.error = "No signal"
        if out == wc.ErrBadSignal: self.error = "Bad signal"
        if out == wc.ErrBigSignal: self.error = "Overexposed"
        if out == wc.ErrLowSignal: self.error = "Underexposed"
        if out == wc.ErrNoPulse: self.error = "No pulse"
        if out == wc.ErrWlmMissing: self.error = "WLM app not active"
        if out == wc.ErrNotAvailable: self.error = "Function not available"
        return out

    def get_frequency(self) -> float:
        out = self.controller.GetFrequency(0)
        self.error = "No error"
        if out == wc.ErrNoValue: self.error = "No value"
        if out == wc.ErrNoSignal: self.error = "No signal"
        if out == wc.ErrBadSignal: self.error = "Bad signal"
        if out == wc.ErrBigSignal: self.error = "Overexposed"
        if out == wc.ErrLowSignal: self.error = "Underexposed"
        if out == wc.ErrNoPulse: self.error = "No pulse"
        if out == wc.ErrWlmMissing: self.error = "WLM app not active"
        if out == wc.ErrNotAvailable: self.error = "Function not available"
        return out

    def get_exposure_range(self) -> None:
        self.expo_min = self.controller.GetExposureRange(wc.cExpoMin)
        self.expo_max = self.controller.GetExposureRange(wc.cExpoMax)
        assert self.expo_min != 0 and self.expo_max != 0


    def get_exposure(self) -> int:
        out = self.controller.GetExposure(0)
        self.error = "No error"
        if out == wc.ErrWlmMissing: self.error = "WLM app not active"
        if out == wc.ErrNotAvailable: self.error = "Function not available"
        return out

    def set_exposure(self, exposure: int):
        try:
            assert exposure <= self.expo_max or exposure >= self.expo_min
            out = self.controller.SetExposure(exposure)
            self.set_functions_error(out)
        except AssertionError:
            print("Exposure out of range.")

    def get_exposure_mode(self) -> bool:
        return self.controller.GetExposureMode(0) == 1

    def set_exposure_mode(self, state: bool):
        state = bool(int(float(state)))
        self.controller.SetExposureMode(state)

    def set_functions_error(self, error: int):
        if error == wc.ResERR_NoErr: self.error = "No Error"
        if error == wc.ResERR_WlmMissing: self.error = "WLM app not active"
        if error == wc.ResERR_CouldNotSet: self.error = "Value could not be set. Please contact Angstrom."
        if error == wc.ResERR_ParmOutOfRange: self.error = "Out of range"
        if error == wc.ResERR_WlmOutOfResources: self.error = "Wavelength meter out of memory or resources. If this happens frequently, please contact Angstrom"
        if error == wc.ResERR_WlmInternalError: self.error = "The wavelength meter raised an internal error, please contact Angstrom."
        if error == wc.ResERR_NotAvailable: self.error = "Not available"
        if error == wc.ResERR_WlmBusy: self.error = "Wavelength meter busy. If this happens frequently, please contact Angstrom."
        if error == wc.ResERR_NotInMeasurementMode: self.error = "Not in measurement mode."
        if error == wc.ResERR_ChannelNotAvailable: self.error = "Channel not available"
        if error == wc.ResERR_ChannelTemporarilyNotAvailable: self.error = "Channel temporarily not available"
        if error == wc.ResERR_CalOptionNotAvailable: self.error = "Calibration option not available"
        if error == wc.ResERR_CalWavelengthOutOfRange: self.error = "Calibration wavelength out of range"
        if error == wc.ResERR_BadCalibrationSignal: self.error = "Bad calibration signal"
        if error == wc.ResERR_UnitNotAvailable: self.error == "Unit not available"

    def get_error(self):
        return self.error

    def get_driver_model(self):
        model = []
        model.append({'element': 'variable', 'name': 'wavelength', 'type': float,
                      'read': self.get_wavelength, "unit": "nm",
                      'help': 'Reads the wavelength.'})
        model.append({'element':'variable', 'name': 'frequency', 'type': float,
                      'read': self.get_frequency, "unit": "THz",
                      'help': 'Reads the frequency.'})
        model.append({"element": "variable", "name": "error", "type": str,
                      "read": self.get_error,
                      "help": "Reads the latest error message."})
        model.append({"element": "variable", "name": "exposure", "type": int,
                      "read": self.get_exposure, "write": self.set_exposure,
                      "unit": "ms", "help": "Reads the latest error message."})
        model.append({"element": "variable", "name": "auto exposure", "type": bool,
                      "read": self.get_exposure_mode, "write": self.set_exposure_mode,
                      "help": "Sets the automatic exposure mode."})
        model.append({"element": "variable", "name": "measuring", "type": bool,
                      "write": self.set_measurement_state,
                      "help": "Starts or stops measurement."})
        return model


###############################################################################
############################ Connections classes ##############################
class Driver_DLL(Driver):

    def __init__(self):

        self.controller = ct.windll.LoadLibrary("wlmData")
        self.controller.GetWavelength.restype = ct.c_double
        self.controller.GetFrequency.restype = ct.c_double

        self.start_server()
        self.get_exposure_range()
        self.set_exposure_mode(True)
        self.start_measurement()
        Driver.__init__(self)

    def close(self):
        self.controller.ControlWLM(wc.cCtrlWLMExit, 0, 0)
############################ Connections classes ##############################
###############################################################################
