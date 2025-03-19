#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Supported instruments (identified): EXFO CT440.
-

This driver is a copy of the ct400 driver using the ct440 option and serves as
a proxy for the ct440 driver.
"""
import os
import sys

# needed for yenista_CT400 import (only needed if used outside of autolab)
if os.path.dirname(os.path.dirname(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# needed for ct440_lib import located in yenista_CT400
if os.path.dirname(__file__) not in sys.path:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'yenista_CT400'))


from yenista_CT400.yenista_CT400 import Driver_DLL as Driver_DLL_ct400
from yenista_CT400.yenista_CT400 import Driver  # just for config_help("exfo_CT440")

#################################################################################
############################## Connections classes ##############################
class Driver_DLL(Driver_DLL_ct400):
    def __init__(self,
        libpath=r"C:\Program Files\EXFO\CT440\Library\Win64\CT440_lib.dll",
        configpath=r'C:\Users\Public\Documents\EXFO\CT440\Config\CT440.config',
        **kwargs):

        self.model = "CT440"
        Driver_DLL_ct400.__init__(self, libpath, configpath, model=self.model, **kwargs)
