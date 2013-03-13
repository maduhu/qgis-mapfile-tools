# -*- coding: utf-8 -*-

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_dock_editor import Ui_DockEditor

class DockEditor(QDockWidget, Ui_DockEditor):
    def __init__(self, parent):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        # Set up the user interface from Designer. 
        self.parent = parent
        self.setupUi(self)
    
    def closeEvent(self, event):
        self.parent.dock_window = None

