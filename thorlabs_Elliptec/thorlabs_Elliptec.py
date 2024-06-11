"""
Driver for the Elliptec motors and stages from Thorlabs https://www.thorlabs.com/navigation.cfm?guide_id=2486
Communication through the ELLO dll (C#)
Requires pythonnet (pip install pythonnet) which gives the clr and System modules

All elliptec devices are handled as separate modules
"""

if not 'clr' in dir():
    import clr
from System import Decimal ## has to be imported after clr
import time

### might get outdated w/ new stages coming out. Keep an eye on
ELL = {'06' : {'long':'Dual-Position Slider','short':'TwoPosSlider'},
		'07' : {'long':'Linear Stage : 26mm Travel', 'short':'LinStage26'},
		'08' : {'long':'Rotation Stage : Ø50mm','short':'RotStage'},
		'09' : {'long':'Four-Position Slider','short':'FourPosSlider'},
		'0E' : {'long':'Rotation Mount: SM1 Threaded', 'short':'RotMount'},
		'11' : {'long':'Linear Stage: 28 mm Travel', 'short':'LinStage28'},
		'12' : {'long':'Rotation Stage: Ø50.0 mm Platform', 'short':'RotPlatform'},
		'14' : {'long':'Linear Stage: 60 mm Travel', 'short':'LinStage620'}}
#### all possible addresses to scan
addresslist = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F']

category = 'Motion controller'


class Driver():
    """ 
    This class mostly corresponds to the ELLDevices class
    """
    def __init__(self, dll_lib, scanlimits):
        
        self.dll_lib = dll_lib
        self.ELLDevObject = self.dll_lib.ELLDevices() ## Elliptec Devices Object
        self.deviceslist = [] ## the device list, empty before scanning
        
        if len(scanlimits) == 0 :
            start, stop = '0' 'F'
        else:
            if type(scanlimits)==str:
                scanlimits = eval(scanlimits)
            ids = sorted([addresslist.index(ii) for ii in scanlimits])
            start = addresslist[ids[0]]
            stop = addresslist[ids[1]]
        self.ScanAddresses(start, stop) ## scan ports
        self.slot_names = {}
        for i, Dev_i in enumerate(self.deviceslist):
            self.ELLDevObject.Configure(Dev_i)
            address = Dev_i[0] ## the address is the first character of the string from 0 to F
            devtype = ELL[Dev_i[3:5]]['short']
            print(Dev_i[3:5])
            if Dev_i[3:5] == '06': ### two position slider stage
                module_class = TwoPosSlider
            elif Dev_i[3:5] == '08': ### Rotation mount
                module_class = RotationMount
            elif Dev_i[3:5] in ['11','14']: ### Linear stage
                module_class = LinearStage
            else: ### all others. Change here if you want to differentiate
                module_class = RotationMount
                
            slot_name = f'{address}_{devtype}'
            self.slot_names[f'{address}'] = slot_name
            ADev_i = self.AddressedDevice(address)
            setattr(self, slot_name, module_class(ADev_i))
            print(slot_name)
            
    def ScanAddresses(self, start='0', stop='F'):
        print(f'Elliptec: Scanning for addresses from {start} to {stop}')
        self.deviceslist = self.ELLDevObject.ScanAddresses(start, stop)
        return self.deviceslist
    
    def Connect(self):
        return self.ELLDevObject.Connect()
    
    def Disconnect(self):
        return self.ELLDevObject.Disconnect
    
    
    def Configure(self, deviceID):
        return(self.ELLDevObject.Configure(deviceID))
    
    def AddressedDevice(self, address):
        ELLDev = self.ELLDevObject.AddressedDevice(address)
        return(ELLDev)
    


    def get_driver_model(self):
        model = [{'element':'module','name':name,'object':getattr(self,name)}
                 for name in self.slot_names.values() ]
        return model
    
#################################################################################
############################## Connections classes ##############################

class Driver_DLL(Driver):
    """
    This class embbeds mostly the ELLDevicePort class 
    """
    def __init__(self, dll_path=r'C:\Program Files\Thorlabs\Elliptec\Thorlabs.Elliptec.ELLO_DLL.dll',
                 port=7, scanlimits=['0','2'] ):
        ### import the C# dll
        clr.AddReference(str(dll_path))
        import Thorlabs.Elliptec.ELLO_DLL as dll_lib 
        
        self.dll_lib = dll_lib
        self.port = f'COM{port}'
        self.baudrate = 9600
        self.bytesize = 8
        self.parity = 'N'
        self.timeout = 0.2
        self.connect()
        self.scanlimits = scanlimits
        Driver.__init__(self, self.dll_lib, self.scanlimits)
            
    
    def connect(self):
        success = self.dll_lib.ELLDevicePort.Connect(self.port)
        return success
        
    def close(self):
        success = self.dll_lib.ELLDevicePort.Disconnect()
        return success
        
    @property
    def isConnected(self):
        return self.dll_lib.ELLDevicePort.IsConnected
    
        
        
############################## Connections classes ##############################
#################################################################################

#################################################################################
################################# Module classes ################################
#### 
#### Classes below should implement methods from the ELLBaseDevice and ELLDevice classes
####
class TwoPosSlider():
    """ 
    Two-position slider. 
    """
    def __init__(self, ELLDev):
        self.Device = ELLDev
    
    def GetPosition(self):
        if self.Device.GetPosition():
            pos = Decimal.ToDouble(self.Device.Position)
        return(pos)
    
    def JogForward(self):
        return(self.Device.JogForward())
    def JogBackward(self):
        return(self.Device.JogBackward())
    
    def get_driver_model(self):
        model = []
        model.append({'name':'Position', 'element':'variable', 'type':float, 'read':self.GetPosition, 'help':'Get position'})
        model.append({'name':'Jog Forward', 'element':'action', 'do':self.JogForward, 'help':'Jog Forward'})
        model.append({'name':'Jog Backward', 'element':'action', 'do':self.JogBackward, 'help':'Jog Backward'})
        return model


class RotationMount():
    """ 
    SM1-threaded rotation mount
    """
    def __init__(self, ELLDev):
        self.Device = ELLDev
        self.JogStep = 0
        self.HomeOffset = 0
    
    
    def JogForward(self): 
        """
        Jog forward by self.JogStep

        """
        return(self.Device.JogForward())
    def JogBackward(self):
        """
        Jog backward by self.JogStep

        """
        return(self.Device.JogBackward())
    def SetJogStep(self, step):
        """
        Sets the jog step
        """
        self.JogStep = step
    def GetJogStep(self):
        """
        Get the Jog step
        """
        return self.JogStep


    def MoveAbsolute(self, pos):
        """
        Move to an absolute position with respect to the home position

        """
        target = pos + self.HomeOffset
        return(self.Device.MoveAbsolute(Decimal(target)))
    
    def MoveRelative(self, step=None):
        """
        Move relative to the given position. If step is none, use internal JogStep 
        """
        if step is None:
            step = self.JogStep
        return(self.Device.MoveRelative(Decimal(step)))
    
    # def MoveToPosition(self, pos):
    #     """ 
    #     Move to a position -- use MoveAbsolute instead?
    #     """
    #     return(self.Device.MoveToPosition(Int64(pos)))
    
    def GetPosition(self):
        """
        Get the current position (corrected by the home offset)
        """
        if self.Device.GetPosition():
            pos = Decimal.ToDouble(self.Device.Position)
        correctedpos = pos - self.HomeOffset
        return(correctedpos)
    
    def SetHomeOffset(self):
        pos = self.GetPosition()
        self.HomeOffset = pos
        
    def GoHome(self):
        return(self.Device.Home())

    def get_driver_model(self):
        model = []
        model.append({'name':'Position', 'element':'variable', 'type':float, 'read':self.GetPosition, 'write':self.MoveAbsolute, 'help':'Get position'})
        model.append({'name':'JogStep', 'element':'variable', 'type':float, 'read':self.GetJogStep, 'write':self.SetJogStep, 'help':'Jog Step'})
        model.append({'name':'SetHome', 'element':'action', 'do':self.SetHomeOffset, 'help':'Set home offset to align rotation axis'})
        model.append({'name':'Jog', 'element':'action', 'do':self.MoveRelative, 'help':'Set home offset to align rotation axis'})
        return model


class LinearStage():
    """ Linear translation stage
    """
    def __init__(self, ELLDev):
        self.Device = ELLDev
        self.JogStep = 0
        self.HomeOffset = 0
        self.pos1 = 0
        self.pos2 = 0
        self.Device.GoHome()
        
    def GoHome(self):
        ret = self.Device.Home()
        if not ret:
            print('Homing resulted in an error')
        
    
    def GetPosition(self):
        while not self.Device.GetPosition():
            print(self.Device.IsDeviceBusy())
            time.sleep(0.01)
        pos = Decimal.ToDouble(self.Device.Position)
        
        return(pos)        
    
    def JogForward(self): 
        """
        Jog forward by self.JogStep

        """
        return(self.Device.JogForward())
    def JogBackward(self):
        """
        Jog backward by self.JogStep

        """
        return(self.Device.JogBackward())
    def SetJogStep(self, step):
        """
        Sets the jog step
        """
        self.JogStep = step
    def GetJogStep(self):
        """
        Get the Jog step
        """
        return self.JogStep


    def MoveAbsolute(self, pos):
        """
        Move to an absolute position with respect to the home position

        """
        target = pos + self.HomeOffset
        ret = self.Device.MoveAbsolute(Decimal(target))
        if not ret:
            print('MoveAbsolute resulted in an error')
            
    def MoveRelative(self, step=None):
        """
        Move relative to the given position. If step is none, use internal JogStep 
        """
        if step is None:
            step = self.JogStep
        ret = self.Device.MoveRelative(Decimal(step))
        if not ret:
            print('MoveRelative resulted in an error')

    
    def SetPos1(self, pos1):
        """To teach a position to the stage
        """
        self.pos1 = pos1
    def SetPos2(self,pos2):
        """To teach a position to the stage
        """
        self.pos2 = pos2
    def GetPos1(self):
        return self.pos1
    def GetPos2(self):
        return self.pos2
    def GoTo1(self):
        self.Device.MoveAbsolute(Decimal(self.pos1))
    def GoTo2(self):
        self.Device.MoveAbsolute(Decimal(self.pos2))
    
    def get_driver_model(self):
        model = []
        model.append({'name':'Home', 'element':'action', 'do':self.GoHome, 'help':'Go to home position'})
        model.append({'name':'Position', 'element':'variable', 'type':float, 'read':self.GetPosition, 'write':self.MoveAbsolute, 'help':'Get position'})
        model.append({'name':'JogStep', 'element':'variable', 'type':float, 'read':self.GetJogStep, 'write':self.SetJogStep, 'help':'Jog Step'})
        model.append({'name':'Jog', 'element':'action', 'do':self.MoveRelative, 'help':'Set home offset to align rotation axis'})
        model.append({'name':'Pos1', 'element':'variable', 'type':float, 'write':self.SetPos1, 'read':self.GetPos1, 'help':'Set position 1'})
        model.append({'name':'Pos2', 'element':'variable', 'type':float, 'write':self.SetPos2, 'read':self.GetPos2, 'help':'Set position 1'})
        model.append({'name':'GoTo1', 'element':'action', 'do':self.GoTo1, 'help':'Go to position 1'})
        model.append({'name':'GoTo2', 'element':'action', 'do':self.GoTo2, 'help':'Go to position 2'})
        return model    
    
################################# Module classes ################################
#################################################################################


#%% Testing
if __name__== '__main__' :
    elldev = Driver_DLL(port='3')
    # print('homing')
    # elldev.Channel0.Home()
    # print('home')

    # print(elldev.Channel0.GetPosition())
    # angleoffset = 165.5
    # elldev.Channel0.MoveAbsolute(0+angleoffset)
    elldev.close()
