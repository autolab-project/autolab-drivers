"""
Driver for MIRCat Lasers from Daylight Solutions
Based on C++ dlls from the MIRCat SDK obtained from Daylight Solutions
Constants are defined and imported from the MIRcatSDKConstants.py file

Warnings: 
    Safety limits are hard-coded in the python driver. 
    You should check that they match your system
    
    The laser needs to be tuned once at startup. 
    It is up to the user to do it and check that it is done.
"""
import MIRcatSDKConstants as MIRCatCst
from ctypes import (
    c_uint8,
    c_uint16,
    c_uint32,
    c_float,
    c_bool,
    CDLL,
    byref
    )
import time


class Driver():
    
    def __init__(self, dll_lib):
        self.dll_lib = dll_lib
        self.IOsleeptime = 0.25 ## from docs: I/O p olling at 4Hz so sleep 250ms before querying
        self.AllowedModes = [MIRCatCst.MIRcatSDK_MODE_PULSED.value, MIRCatCst.MIRcatSDK_MODE_CW.value]
        
        self.Connect() 
        self.ArmAndWaitForTemp() ## optional, but it makes sense to arm the laser when starting
        
    def Connect(self):
        """
        Connect to the MIRCat and check interlock, key switches etc.
        Obtained from the exampe file in MIRCat SDK documentation
        """
        # Initialize MIRcatSDK & Connect to MIRcat laser
        print("Initializing MIRcatSDK")
        ret = self.dll_lib.MIRcatSDK_Initialize()
        if ret == MIRCatCst.MIRcatSDK_RET_SUCCESS.value:
            print(" Successfully Connected to MIRcat")
        else:
            print(f" Failure to Initialize API. Error Code: {ret}")
        isInterlockSet = c_bool(False)
        isKeySwitchSet = c_bool(False)
        # Step 1: Get the number of installed QCLs
        print("Test: Detect installed QCLs")
        QCLNumber = self.GetQCLNumber() ### defined below
        print(f" Found {QCLNumber} QCLs")
        # Step 2: Check for Interlock Status
        print("Test: Is Interlock Set?")
        ret = self.dll_lib.MIRcatSDK_IsInterlockedStatusSet(byref(isInterlockSet))
        if isInterlockSet.value:
            print(f" Interlock Set: {isInterlockSet.value}")
        else:
            print(f" Interlock Set: {isInterlockSet.value} \t error code: {ret}")
            exit(0)
        # Step 3: Check for Key Switch Status
        print("Test: Is Key Switch Set?")
        ret = self.dll_lib.MIRcatSDK_IsKeySwitchStatusSet(byref(isKeySwitchSet))
        if isKeySwitchSet.value:
            print(f" KeySwitch Set: {isKeySwitchSet.value}")
        else:
            print(f" KeySwitch Set: {isKeySwitchSet.value} \t error code {ret}")
            exit(0)
    
    
    def ArmAndWaitForTemp(self):
        """
        Arm the laser and wait for all TECs to be at temperature for all QCL chips
        Obtained from the exampe file in MIRCat SDK documentation
        """
        atTemp = c_bool(False)
        isArmed = c_bool(False)
        ret = self.dll_lib.MIRcatSDK_IsLaserArmed(byref(isArmed))
        if not isArmed.value:
            ret = self.dll_lib.MIRcatSDK_ArmDisarmLaser()
            print(" Test Result: \tret:{0}".format(ret))
            print("#****************************************************************#")
            print("Test: Is Laser Armed?")

        while not isArmed.value:
            ret = self.dll_lib.MIRcatSDK_IsLaserArmed(byref(isArmed))
            print(" Test Result: \tret:{0} \tIsArmed: {1}".format(ret, isArmed.value))
            time.sleep(4*self.IOsleeptime)

        # Wait until TECs are at temperature before doing any tuning/scanning
        # Note: This can take a while depending on how the laser is cooled.
        print("#****************************************************************#")
        print("Test : TEC Temperature Status")
        ret = self.dll_lib.MIRcatSDK_AreTECsAtSetTemperature(byref(atTemp))
        print(f" Test Result: {ret} \t atTemp = {atTemp.value}")
        tecCur = c_uint16(0)
        qclTemp = c_float(0)
        numQCLs = self.GetQCLNumber()
        while not atTemp.value:
            for i in range(1, numQCLs + 1):
                ret = self.dll_lib.MIRcatSDK_GetQCLTemperature(c_uint8(i), byref(qclTemp))
                print(f" Test Result: ret:{ret} \t QCL:{i} \t Temp: {qclTemp.value:.5} C")
                ret = self.dll_lib.MIRcatSDK_GetTecCurrent(c_uint8(i), byref(tecCur))
                print(f" Test Result: ret:{ret} \t TEC:{i} \tCurrent: {tecCur.value} mA")

            ret = self.dll_lib.MIRcatSDK_AreTECsAtSetTemperature(byref(atTemp))
            print(f"TECs at Temperature: ret:{ret} \t atTemp = {atTemp.value}")
            time.sleep(self.IOsleeptime)
        return atTemp
        
    def DisarmLaser(self):
        """
        Simply disarm the laser. Can be armed again using ArmAndWaitForTemp
        """
        ret = self.dll_lib.MIRcatSDK_DisarmLaser()
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value:
            print(f"Disarm laser returned error code {ret}")

    def DisarmAndClose(self):
        """
        Disarm the laser and close the connection. 
        This should be called only for closing the laser.
        """
        print('Shutting down the laser.')
        if self.isEmitting():
            print('Turning emission off')
            self.TurnEmissionOff()
            time.sleep(2*self.IOsleeptime)
        ## Cancel Manual Scan Mode
        ret = self.dll_lib.MIRcatSDK_CancelManualTuneMode()
        # Disarm Laser
        if self.isArmed():
            print('Disarming laser')
            self.DisarmLaser()
            time.sleep(2*self.IOsleeptime)
        isArmed = c_bool()
        ret = self.dll_lib.MIRcatSDK_IsLaserArmed(byref(isArmed))
        print(f"Test Result: {ret} \t Is Armed: {isArmed.value}")
        # Disconnect from MIRcat
        print("Attempting to De-Initialize MIRcatSDK...")
        ret = self.dll_lib.MIRcatSDK_DeInitialize()
        print(f"Test Result: {ret}")

    def setArmAndTemp(self, status):
        """
        Toggle function for the GUI boolean variable 'Arm Laser' 
        """
        if status is True:
            if self.isArmed() is False:
                self.ArmAndWaitForTemp()
        else:
            if self.isArmed():
                self.DisarmLaser()

    def isTuned(self):
        """
        Check that the QCL is tuned to the correct wavelength. 
        Requires at least one execution prior to emission when arming the laser.
        """
        units = c_uint8()
        isTuned = c_bool(False)
        actualWn = c_float()
        lightValid = c_bool()
        while not isTuned.value:
            """"Check Tuning Status"""
            ret = self.dll_lib.MIRcatSDK_IsTuned(byref(isTuned))
            print(f" Test Result: ret:{ret} isTuned: {isTuned.value}")
            """Check Actual Wavenumber"""
            ret = self.dll_lib.MIRcatSDK_GetActualWW(byref(actualWn), byref(units), byref(lightValid))
            if units == MIRCatCst.MIRcatSDK_UNITS_CM1:
                unit_str = 'cm-1'
            else:
                unit_str = 'micron'
            print(f"Test Result: ret:{ret} Actual Wn: {actualWn.value:.5}{unit_str} Light Valid: {lightValid.value}")
            time.sleep(2*self.IOsleeptime)
        return isTuned.value

    def isArmed(self):
        isArmed = c_bool()
        ret = self.dll_lib.MIRcatSDK_IsLaserArmed(byref(isArmed))
        if not isArmed.value:
            ret = self.dll_lib.MIRcatSDK_ArmDisarmLaser()
            print(" Test Result: \tret:{0}".format(ret))
            print("#****************************************************************#")
            print("Test: Is Laser Armed?")

        while not isArmed.value:
            ret = self.dll_lib.MIRcatSDK_IsLaserArmed(byref(isArmed))
            print(" Test Result: \tret:{0} \tIsArmed: {1}".format(ret, isArmed.value))
            time.sleep(4*self.IOsleeptime)
        return isArmed.value
    
    def isEmitting(self):
        isEmitting = c_bool()
        ret = self.dll_lib.MIRcatSDK_IsEmissionOn(byref(isEmitting))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value:
            print(f'isEmitting returned with error code {ret}. isEmitting: {isEmitting.value}')
        time.sleep(self.IOsleeptime)
        return isEmitting.value
    
        
    def TurnEmissionOn(self):
        isEmitting = c_bool()
        ret = self.dll_lib.MIRcatSDK_IsEmissionOn(byref(isEmitting))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value or isEmitting.value is True:
            print(f" Error turning emission on, returned with error code{ret}. IsEmitting returned {isEmitting.value}")
        ret = self.dll_lib.MIRcatSDK_TurnEmissionOn()
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value:
            print(f" Error turning emission on, returned with error code{ret}.")            
    def TurnEmissionOff(self):
        isEmitting = c_bool()
        ret = self.dll_lib.MIRcatSDK_TurnEmissionOff()
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value:
            print(f"Trying to turn off emission returned with error code {ret}")
        ret = self.dll_lib.MIRcatSDK_IsEmissionOn(byref(isEmitting))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value or isEmitting.value is True:
            print(f"Error turning emission off, returned with error code {ret}. IsEmitting returned {isEmitting.value}")
    def setOutput(self, state):
        """
        Toggle function for the emission state, for the GUI boolean variable 'Shoot'
        """
        if state is True:
            self.TurnEmissionOn()
            time.sleep(self.IOsleeptime)
        else:
            self.TurnEmissionOff()
            time.sleep(self.IOsleeptime)

        
    def SetAllQCLParams(self, QCLchip, PulseRate,
                        PulseWidth, Current, Temp, Mode):
        """
        Main function that sets all the QCL parameters.
        Safety checks are hard-coded here. You should make sure they match your system.
        """
        ChipNumber = c_uint8(QCLchip)
        PulseRateInHz = c_float(PulseRate)
        PulseWidthInNanoSec = c_float(PulseWidth)
        if Mode not in self.AllowedModes:
            print('Trying to set an unsupported mode. Defaulting to pulsed')
            Mode = MIRCatCst.MIRcatSDK_MODE_PULSED
        else:
            Mode = c_uint8(Mode)
        if Mode.value == MIRCatCst.MIRcatSDK_MODE_CW.value:
            if QCLchip == 1 and Current > 800: ## refer to calibration
                print(f'Warning, current {Current}mA is too high for QCL chip {QCLchip} in CW mode. Defaulting to max value 800mA')
                CurrentInMiliAmps = c_float(800)
            elif QCLchip == 2 and Current > 900: ## refer to calibration
                print(f'Warning, current {Current}mA is too high for QCL chip {QCLchip} in CW mode. Defaulting to max value 900mA')
                CurrentInMiliAmps = c_float(900)
            else:
                CurrentInMiliAmps = c_float(Current)
                
        elif Mode.value == MIRCatCst.MIRcatSDK_MODE_PULSED.value:
            if QCLchip == 1 and Current > 880: ## refer to calibration
                print(f'Warning, current {Current}mA is too high for QCL chip {QCLchip} in pulsed mode. Defaulting to max value 880mA')
                CurrentInMiliAmps = c_float(880)
            elif QCLchip == 2 and Current > 1000: ## refer to calibration
                print(f'Warning, current {Current}mA is too high for QCL chip {QCLchip} in pulsed mode. Defaulting to max value 1000mA')
                CurrentInMiliAmps = c_float(1000)
            else:
                CurrentInMiliAmps = c_float(Current)
            
        if Temp <= 18 or Temp >= 20 :
            print('Warning! Temperature set different from 19°C. ')
            QCLTemp = c_float(19) ## hard coded temperature for the chips 19°C
        else:
            QCLTemp = c_float(19)
        
        print("Setting parameters to QCL...")
        ret = self.dll_lib.MIRcatSDK_SetAllQclParams(ChipNumber, PulseRateInHz, 
                                                     PulseWidthInNanoSec, CurrentInMiliAmps, 
                                                     QCLTemp, Mode)  
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while setting QCL params on chip {QCLchip}, returned with error code {ret}')
            
    def GetActiveQCL(self):
        """
        Get the currently active QCL chip
        """
        ChipNumber = c_uint8()
        ret = self.dll_lib.MIRcatSDK_GetActiveQcl(byref(ChipNumber))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error in getting Active QCL number. Returned with error code {ret}. QCL number {ChipNumber.value}')
        return ChipNumber.value
        
    def GetQCLNumber(self):        
        """
        Get the number of installed QCLs
        """
        QCLNumber = c_uint8(0)
        ret = self.dll_lib.MIRcatSDK_GetNumInstalledQcls(byref(QCLNumber))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while getting QCL number, returned with error code {ret}')
        return QCLNumber.value
        
    def GetQCLOperatingMode(self, QCLchip = None):
        if QCLchip is None:
            ChipNumber = c_uint8(self.GetActiveQCL())
        else:
            ChipNumber = c_uint8(QCLchip)
        mode = c_uint32()
        ret = self.dll_lib.MIRcatSDK_GetQCLOperatingMode(ChipNumber, byref(mode))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while getting QCL operating mode on chip {QCLchip}, returned with error code {ret}')
        return mode.value
    
    def GetQCLCurrent(self, QCLchip = None):
        if QCLchip is None:
            ChipNumber = c_uint8(self.GetActiveQCL())
        else:
            ChipNumber = c_uint8(QCLchip)
        QCLcurrent = c_float()
        ret = self.dll_lib.MIRcatSDK_GetQCLCurrent(ChipNumber, byref(QCLcurrent))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while getting QCL current on chip {QCLchip}, returned with error code {ret}')
        return QCLcurrent.value

    def GetQCLPulseRate(self, QCLchip = None):
        if QCLchip is None:
            ChipNumber = c_uint8(self.GetActiveQCL())
        else:
            ChipNumber = c_uint8(QCLchip)
        pfPulseRateInHz = c_float()
        ret = self.dll_lib.MIRcatSDK_GetQCLPulseRate(ChipNumber, byref(pfPulseRateInHz))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while getting QCL pulse rate on chip {QCLchip}, returned with error code {ret}')
        return pfPulseRateInHz.value

    def GetQCLPulseWidth(self, QCLchip = None):
        if QCLchip is None:
            ChipNumber = c_uint8(self.GetActiveQCL())
        else:
            ChipNumber = c_uint8(QCLchip)
        pfPulseWidthInNanoSec = c_float()
        ret = self.dll_lib.MIRcatSDK_GetQCLPulseWidth(ChipNumber, byref(pfPulseWidthInNanoSec))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while getting QCL pulse width on chip {QCLchip}, returned with error code {ret}')
        return pfPulseWidthInNanoSec.value
        
    def GetQCLTemperature(self, QCLchip = None):
        if QCLchip is None:
            ChipNumber = c_uint8(self.GetActiveQCL())
        else:
            ChipNumber = c_uint8(QCLchip)
        QCLTemp = c_float()
        ret = self.dll_lib.MIRcatSDK_GetQCLTemperature(ChipNumber, byref(QCLTemp))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Error while getting QCL temperature on chip {QCLchip}, returned with error code {ret}')
        return round(QCLTemp.value,2)
        
    def GetAllQCLParams(self, QCLchip):
        """
        Wrapper function that allows retrieving all QCL parameters at once, 
        to be used again with SetAllQCLParams to selectively set one parameter
        """
        PulseRate = self.GetQCLPulseRate(QCLchip)
        PulseWidth = self.GetQCLPulseWidth(QCLchip)
        Current = self.GetQCLCurrent(QCLchip)
        Temp = self.GetQCLTemperature(QCLchip)
        mode = self.GetQCLOperatingMode(QCLchip)
        return PulseRate, PulseWidth, Current, Temp, mode
    
    ####
    ## All functions below wrap around SetAllQCLParams
    def SetQCLCurrent(self, Current, QCLchip = None):
        if QCLchip is None:
            QCLchip = self.GetActiveQCL()
        PulseRate, PulseWidth, _, Temp, Mode = self.GetAllQCLParams(QCLchip)
        _ = self.SetAllQCLParams(QCLchip, PulseRate, PulseWidth, Current, Temp, Mode)
    
    def SetQCLPulseRate(self, PulseRate, QCLchip = None):
        if QCLchip is None:
            QCLchip = self.GetActiveQCL()
        _, PulseWidth, Current, Temp, Mode = self.GetAllQCLParams(QCLchip)
        _ = self.SetAllQCLParams(QCLchip, PulseRate, PulseWidth, Current, Temp, Mode)
    
    def SetQCLPulseWidth(self, PulseWidth, QCLchip = None):
        if QCLchip is None:
            QCLchip = self.GetActiveQCL()
        PulseRate, _, Current, Temp, Mode = self.GetAllQCLParams(QCLchip)
        _ = self.SetAllQCLParams(QCLchip, PulseRate, PulseWidth, Current, Temp, Mode)

    def SetQCLMode(self, intMode, QCLchip = None):
        if QCLchip is None:
            QCLchip = self.GetActiveQCL()
        if intMode not in self.AllowedModes:
            print('Trying to set an unsupported mode. Defaulting to pulsed')
            Mode = MIRCatCst.MIRcatSDK_MODE_PULSED
        else:
            Mode = c_uint8(intMode)
        PulseRate, PulseWidth, Current, Temp, _ = self.GetAllQCLParams(QCLchip)
        _ = self.SetAllQCLParams(QCLchip, PulseRate, PulseWidth, Current, Temp, Mode)
    
    def GetTuneWn(self):
        """
        Get the target Wavenumber to tune to. Probably useless
        """
        pfTuneWW = c_float()
        pbUnits = c_uint8()
        pbPreferredQcl = c_uint8()
        ret = self.dll_lib.MIRcatSDK_GetTuneWW(byref(pfTuneWW), byref(pbUnits), byref(pbPreferredQcl))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'GetTuneWn returned error code {ret}')
        return pfTuneWW.value
    
    def GetActualWn(self):
        """
        Get the actual wavenumber. Used in 'tuned' to check the tuning operation and read 
        the current wavenumber.
        """
        ActualWn = c_float()
        pfActualWW = c_float()
        pbUnits = c_uint8()
        pbLightValid = c_bool()
        ret = self.dll_lib.MIRcatSDK_GetActualWW(byref(pfActualWW), byref(pbUnits), byref(pbLightValid))
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'GetActualWn returned error code {ret}')
        if pbUnits.value == MIRCatCst.MIRcatSDK_UNITS_MICRONS.value:
            ret = self.dll_lib.MIRcatSDK_ConvertWW(pfActualWW, 
                                                   MIRCatCst.MIRcatSDK_UNITS_MICRONS,
                                                   MIRCatCst.MIRcatSDK_UNITS_CM1,
                                                   byref(ActualWn))
        else:
            ActualWn = pfActualWW
        return ActualWn.value
            
    def TuneToWavenumber(self, wn, QCLchip=None):
        """
        Tune to the given wavenumber
        """
        fTuneWW = c_float(wn)
        units = MIRCatCst.MIRcatSDK_UNITS_CM1
        if QCLchip is not None:
            ChipNumber = c_uint8(QCLchip)
        else:
            if 1140 < wn <= 1350:
                ChipNumber = c_uint8(1)
            elif 1000 <= wn <= 1140:
                ChipNumber = c_uint8(2)
        PulseRate, PulseWidth, Current, Temp, Mode = self.GetAllQCLParams(ChipNumber.value)
        self.SetAllQCLParams(ChipNumber.value, PulseRate, PulseWidth, Current, Temp, Mode)
        ret = self.dll_lib.MIRcatSDK_TuneToWW(fTuneWW, units, ChipNumber)
        if ret != MIRCatCst.MIRcatSDK_RET_SUCCESS.value :
            print(f'Tuning to wavenumber returned error code {ret}')
        self.isTuned()
        
    def get_driver_model(self):
        model = []
        model.append({'name':'Arm Laser', 'element':'variable', 'type':bool, 'read':self.isArmed, 'write':self.setArmAndTemp, 'help':'Arm the laser and wait for TEC stabilization'})
        model.append({'name':'Shoot', 'element':'variable', 'type':bool, 'read':self.isEmitting, 'write':self.setOutput, 'help':'Turn emission On/Off'})
        model.append({'name':'Wavenumber', 'element':'variable', 'type':float, 'read':self.GetActualWn, 'write':self.TuneToWavenumber, 'unit':'cm-1', 'help':'Change the wavenumber'})
        model.append({'name':'Current', 'element':'variable', 'type':float, 'read':self.GetQCLCurrent, 'write':self.SetQCLCurrent, 'unit':'mA', 'help':'Change the QCL current in mA'})
        model.append({'name':'Pulse Rate', 'element':'variable', 'type':float, 'read':self.GetQCLPulseRate, 'write':self.SetQCLPulseRate, 'unit':'Hz', 'help':'Change the QCL pulse rate in Hz'})
        model.append({'name':'Pulse Width', 'element':'variable', 'type':float, 'read':self.GetQCLPulseWidth, 'write':self.SetQCLPulseWidth, 'unit':'ns', 'help':'Change the QCL pulse width in ns'})
        model.append({'name':'QCL Mode', 'element':'variable', 'type':float, 'read':self.GetQCLOperatingMode, 'write':self.SetQCLMode, 'help':'Modes: pulsed=1 cw=2'})
        model.append({'name':'Active QCL chip', 'element':'variable', 'type':float, 'read':self.GetActiveQCL, 'help':'Currently active QCL'})
        model.append({'name':'Temperature', 'element':'variable', 'type':float, 'read':self.GetQCLTemperature, 'unit':'C', 'help':'Active QCL Temperature'})
        model.append({'name':'QCLs present', 'element':'variable', 'type':float, 'read':self.GetQCLNumber, 'help':'Number of detected QCLs'})
        model.append({'name':'Clean close', 'element':'action', 'do':self.DisarmAndClose, 'help':'Close the MIRCat'})
        return model
        
        
#################################################################################
############################## Connections classes ##############################

class Driver_DLL(Driver):
    
    def __init__(self, dll_path=r'C:\Program Files (x86)\Daylight Solutions\MIRcat\MIRcatSDK_1.4.5\x64'):
        import os
        from sys import version
        
        ####
        ## Differentiating along python versions since import of the dll has been 
        ## unstable depending on Py3.7 or Py3.8
        version_num = version.split(' ')[0].split('.')
        
        if int(version_num[0]) == 3 and int(version_num[1]) == 7: ##v3.7
            cwd = os.path.dirname(os.path.abspath(__file__))    
            os.chdir(dll_path)
            dll_lib = CDLL("MIRcatSDK")
            os.chdir(cwd)

        elif int(version_num[0]) == 3 and int(version_num[1]) == 8: ##v3.8
            os.add_dll_directory(dll_path)
            dll_lib = CDLL(os.path.join(dll_path,"MIRcatSDK"))
        
        elif int(version_num[0]) < 3:
            print('You should upgrade to python 3.7 or higher')
        
        else:
            print('Using python > 3.8, dll not tested yet. Resorting to py3.8 case')
            os.add_dll_directory(dll_path)
            dll_lib = CDLL(os.path.join(dll_path,"MIRcatSDK"))
        
        Driver.__init__(self, dll_lib)
    
    def close(self):
        
        self.DisarmAndClose()
        