# -*- coding: utf-8 -*-

import os
import sys
from tempfile import mkstemp
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ui_dock_editor import Ui_DockEditor
from simple_map_editor import SimpleMapEditor

class DockEditor(QDockWidget, Ui_DockEditor):
    def __init__(self, parent):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        # temporary file for mapfile
        # FIXME : should deal with multiple mapfiles
        self.temp_file = None
        self.temp_mapfile = None

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
        self.connectAll()

    def connectAll(self):
        """Do all initial connections of Gui elements."""
        QObject.connect(self.createNewButton, SIGNAL("clicked()"), self.create_new_pressed)
        QObject.connect(self.replaceLayerButton, SIGNAL("clicked()"), self.replace_layer_pressed)
        QObject.connect(self.addLayerButton, SIGNAL("clicked()"), self.add_layer_pressed)

    def create_new_pressed(self):
        """Create new Mapfile from default template."""
        self.editor.load(self.parent.template_dir + "/default.map")
        # create temporary file
        fd, self.temp_mapfile = mkstemp(suffix='.map', prefix = 'mapfile_tools_', text = True)
        self.temp_file = open(self.temp_mapfile, 'w+')
        # write mapfile content to it
        self.update_file()

    def add_layer_pressed(self):
        """Add current Mapfile to layer."""
        self.parent.addLayer(self.temp_mapfile)

    def replace_layer_pressed(self):
        """Replace selected layer with current mapfile."""
        pass

    def get_new_layer_name(self):
        """Get current text in combobox for new layer name."""
        template = 'New Layer %s'
        layer_name = self.msLayerList.currentText()
        if not layer_name:
            i = 1
            layer_name = template % i
            while self.msLayerList.find(layer_name) == -1 :
                i = i + 1
                layer_name = template % i
        return layer_name

    def closeEvent(self, event):
        self.parent.dock_window = None

    def update_file(self):
        """Update file on disk with editor's content."""
        self.temp_file.write(self.editor.getText())
        self.temp_file.flush()


