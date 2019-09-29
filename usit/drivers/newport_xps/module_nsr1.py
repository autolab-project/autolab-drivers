# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 16:29:09 2019

@author: qchat
"""

import time
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d

class NSR1():
    
    
    def __init__(self,dev,slot,calibPath):
        
        self.dev = dev
        self.NAME = slot
        self.SLOT = slot
        
        self.calibPath = calibPath
        assert os.path.exists(calibPath)
        self.calibrationFunction = None
        
        self.calib = None
        self.loadCalib()
        
    #--------------------------------------------------------------------------
    # Calibration functions
    #--------------------------------------------------------------------------
    
    def loadCalib(self):
        try: self.calib = pd.read_csv(os.path.join(self.calibPath,'calib.csv'))
        except: pass
    
    def setCalibrationGetPowerFunction(self,calibrationFunction):
        self.calibrationFunction = calibrationFunction
        
    def calibrate(self):
        
        assert self.calibrationFunction is not None
        
        def scan(listAngle):
            
            df = pd.DataFrame()

            for angle_setpoint in listAngle :
                self.setAngle(angle_setpoint)
                angle=self.getAngle()
                power=self.calibrationFunction()
                df=df.append({'angle':angle,'power':power})
                   
            df.sort_values(by=['angle'],inplace=True)
            return df
        
        plt.ioff()
        fig = plt.figure()
        ax=fig.add_subplot(111)
        
        # Homing
        self.goHome()
        
        # Fabrication de la liste des angles à explorer
        listAngle = np.concatenate((np.arange(0,360,8),np.arange(4,360,8)))
        listAngle = np.flipud(listAngle)
        
        # Lancement du scan de mesure de puissance
        df=scan(listAngle)
        
        # Find transition
        derivative = np.diff(df.power)
        imax=np.argmax(derivative)
        
        # Recoupage
        df_shifted = pd.DataFrame()
        df_shifted['power'] = np.concatenate((df.power[imax:],df.power[0:imax]))
        df_shifted['angle'] = np.concatenate((df.angle[imax:]-360,df.angle[0:imax]))
        df = df_shifted
        
        # Suppression transition sur 10deg
        df = pd.DataFrame()
        df = df[df.angle>(df.angle.min()+10)]
        df = df[df.angle<(df.angle.max()-10)]
        
        # Normalisation
        df['transmission']=df.power/df.power.max()
        ax.plot(df.angle,df.transmission,'x',label='raw')
        
        # Lissage
        df['transmission']=savgol_filter(df.transmission, 7, 3)
        
        # Interpolation
        interpolFunc=interp1d(df.angle, df.transmission, kind='cubic')
        df['angle']=np.linspace(df.angle.min(),df.angle.max(),1000)
        df['transmission']=interpolFunc(df.angle)
        
        # EXTRACT On ne garde que entre 0% et 95% car trop bruité au dessus
        df = df[df.transmission<0.95]
        
        # Sauvegarde plot
        date=time.strftime("%Y%m%d_%H%M%S")
        ax.plot(df.angle,df.transmission,'r-',label='Final')
        ax.set_title(f'{self.NAME} filter {date}')
        ax.grid()
        ax.set_xlabel('Angle [deg]')
        ax.set_ylabel('Power [a.u.]')
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles, labels, loc=0)
        filepath=os.path.join(self.calibPath,f'{date}_{self.NAME}_calib.jpg')
        fig.savefig(filepath,bbox_inches='tight',dpi=300)
        fig.close()
           
        # Enregistrement des données 
        df.to_csv(os.path.join(self.calibPath,'calib.csv'))
        
        # Raffraichissement des donnees
        self.loadCalib()
        

        
        
        
        
    #--------------------------------------------------------------------------
    # Optional functions
    #--------------------------------------------------------------------------
        
    def setSafeState(self):
        self.setMin()
        if self.getTransmission() < 0.2 :
            return True
            

        

        
    #--------------------------------------------------------------------------
    # Technical functions
    #--------------------------------------------------------------------------
    
    def getFilterState(self):
        state=self.dev.query(['GroupStatusGet',self.SLOT])
        
        if 0 <= state <= 9 :
            return 'NOTINIT'
        elif state == 42 :
            return 'NOTREF'
        elif state == 43 :
            return 'HOMING'
        elif state == 44 :
            return 'MOVING'
        elif 10 <= state <= 19 :
            return 'ENABLED'
        elif 20 <= state <= 39 :
            return 'DISABLED'
        else :
            return None
    
    def checkReady(self):
    
        if self.getFilterState() in ['ENABLED','DISABLED'] :
            return True 
        else :
            if self.getFilterState() == 'NOTINIT' :
                self.dev.query(['GroupInitialize',self.SLOT])
                if self.getFilterState() != 'NOTREF' :
                    return False
            if self.getFilterState() == 'NOTREF':
                self.dev.query(['GroupHomeSearch',self.SLOT])
                while self.getFilterState() == 'HOMING' :
                    time.sleep(0.5)
                if self.getFilterState() in ['ENABLED','DISABLED'] :
                    self.setEnabled(False)
                    return True
                else :
                    return False
                
    
    def waitMoveEnding(self):
        while self.getFilterState() == 'MOVING' :
            time.sleep(0.1)
        time.sleep(0.4) # Trop rapide sinon
        
        
        
        
        
        
    def setEnabled(self,state):
        assert isinstance(state,bool)
        if state is True :
            self.dev.query(['GroupMotionEnable',self.SLOT])
        else :
            self.dev.query(['GroupMotionDisable',self.SLOT])       

    def isEnabled(self):
        state=self.getFilterState()
        if state in ['ENABLED','MOVING'] :
            return True
        else :
            return False
        
        
        
        

    def setPositionerName(self,value):
        assert isinstance(value,str)
        self.setData('positionerName',value)
        
    def getPositionerName(self):
        if 'positionerName' not in self.getDataList() :
            self.setPositionerName('Pos')
        return self.getData('positionerName')
    
    
    
        
    #--------------------------------------------------------------------------
    # Instrument variables
    #--------------------------------------------------------------------------
    
    
    
    def getParameters(self):
        if self.checkReady() is True :
            params={}
            temp=self.dev.query(['PositionerSGammaParametersGet',self.SLOT+'.'+self.getPositionerName()])       
            params['velocity']=temp[0]
            params['acceleration']=temp[1]
            params['minJerkTime']=temp[2]
            params['maxJerkTime']=temp[3]
            return params
        else :
            raise ValueError('Not ready')
            
    def setParameters(self,params):
        if self.checkReady() is True :
            self.dev.query(['PositionerSGammaParametersSet',self.SLOT+'.'+self.getPositionerName(),
                                                             params['velocity'],
                                                             params['acceleration'],
                                                             params['minJerkTime'],
                                                             params['maxJerkTime']]) 
        else :
            raise ValueError('Not ready')






    def setVelocity(self,value):
        assert isinstance(float(value),float)
        value=float(value)
        params=self.getParameters()
        params['velocity']=value
        self.setParameters(params)
    
    def getVelocity(self):
        return float(self.getParameters()['velocity'])


        
    


    def setAcceleration(self,value):
        assert isinstance(float(value),float)
        value=float(value)
        params=self.getParameters()
        params['acceleration']=value
        self.setParameters(params)
    
    def getAcceleration(self):
        return float(self.getParameters()['acceleration'])
    



    
    
    def setAngle(self,value,forced=False):
        assert isinstance(float(value),float)
        value=float(value)
        
        if forced is False :
            currAngle = self.getAngle()
            if value > currAngle - 1.9 :
                self.setAngle(value+20,forced=True)
            
        if self.checkReady() is True :
            self.setEnabled(True)
            self.dev.query(['GroupMoveAbsolute',self.SLOT,[value]])
            self.waitMoveEnding()
            self.setEnabled(False)
        else :
            raise ValueError('Not ready')
        
    def getAngle(self):
        if self.checkReady() is True :
            value = float(self.dev.query(['GroupPositionCurrentGet',self.SLOT,1]))
            return value
        else :
            raise ValueError('Not ready')
    
    
    
    
    

    def setTransmission(self,value):
        assert isinstance(float(value),float)
        value = float(value)
        angle = self.getAngleFromTransmission(value)
        self.setAngle(angle)
    
    def getTransmission(self):
        angle = self.getAngle()
        return self.getTransmissionFromAngle(angle)

        
    def getTransmissionMax(self):
        return self.calib.transmission.max()



    def getAngleFromTransmission(self,value):
        ind = abs(self.calib.transmission-value).idxmin()
        return float(self.calib.loc[ind,'angle'])   
    
    def getTransmissionFromAngle(self,value):
        ind = abs(self.calib.angle-value).idxmin()
        return float(self.calib.loc[ind,'transmission'])   





        



    
      
    
    def setMin(self):
        self.setTransmission(0)
        
    def setMax(self):
        self.setTransmission(1)



            
    
    def goHome(self):
        
        self.setAngle(self.getAngle()+5) # In case we are at home - blocking
        
        # Go to not init
        self.dev.query(['GroupKill',self.SLOT])
        while self.getFilterState() != 'NOTINIT':
            time.sleep(0.1)
                            
        # Go from not init to ref mode
        self.dev.query(['GroupInitialize',self.SLOT])
        while self.getFilterState() != 'NOTREF':
            time.sleep(0.1)
        
        # Homing to get back to ready state
        self.dev.query(['GroupHomeSearch',self.SLOT])
        while self.getFilterState() != 'ENABLED':
            time.sleep(0.1)

        # On le désactive
        self.setEnabled(False)
        while self.getFilterState() != 'DISABLED':
            time.sleep(0.1)
            