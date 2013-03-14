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
        # get position of "widget" widget to replace it
        # so as not to change the code on every qt designer modification
        row, col, rowspan, colspan = self.gridLayout.getItemPosition(
                self.gridLayout.indexOf(self.widget))
        # add the scintilla editor on top of "widget" widget
        self.gridLayout.addWidget(self.editor, row, col, rowspan, colspan)
    
    def closeEvent(self, event):
        self.parent.dock_window = None

