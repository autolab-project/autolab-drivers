# -*- coding: utf-8 -*-
"""
Created on Fri May 17 15:04:04 2019

@author: quentin.chateiller
"""

# Initializing
#from . import core
#core.checkConfig()

__version__ = '1.0'


from . import core
core.checkConfig()

from .core._drivers import DriverManager
drivers = DriverManager()
del DriverManager

core.devices.index = core.devices.loadIndex()

devices = core.devices.DeviceManager()

from .core.gui import gui
from .core._report import report
from .core.recorder_old.recorder import Recorder, Recorder_V2




    