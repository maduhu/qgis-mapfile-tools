# -*- coding: utf-8 -*-

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_dock_editor import Ui_DockEditor
from simple_map_editor import SimpleMapEditor

class DockEditor(QDockWidget, Ui_DockEditor):
    def __init__(self, parent):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        # Set up the user interface from Designer. 
        self.parent = parent
        self.setupUi(self)
        self.editor = SimpleMapEditor(self)
        self.gridLayout.addWidget(self.editor, 0, 0, 7, 1)
    
    def closeEvent(self, event):
        self.parent.dock_window = None

