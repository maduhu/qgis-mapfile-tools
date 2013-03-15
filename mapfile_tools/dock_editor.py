# -*- coding: utf-8 -*-

import os
import sys
import re
from shutil import copyfile
from tempfile import mkstemp
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import QgsMapLayerRegistry
from mapfile_layer import MapfileLayer
from ui_dock_editor import Ui_DockEditor
from simple_map_editor import SimpleMapEditor

class DockEditor(QDockWidget, Ui_DockEditor):
    def __init__(self, parent):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        # temporary file for mapfile
        # FIXME : should deal with multiple mapfiles
        self.temp_mapfile = None

        # Set up the user interface from Designer. 
        self.parent = parent
        # save qgis interface
        self.iface = self.parent.iface
        self.setupUi(self)
        self.editor = SimpleMapEditor(self)
        # get position of "widget" widget to replace it
        # so as not to change the code on every qt designer modification
        row, col, rowspan, colspan = self.gridLayout.getItemPosition(
                self.gridLayout.indexOf(self.widget))
        # add the scintilla editor on top of "widget" widget
        self.gridLayout.addWidget(self.editor, row, col, rowspan, colspan)

        # fill in the combobox
        self.update_ms_layer_list()

        # connect signals and slots
        self.connectAll()
        self.update_autorefresh()
        self.display_mapfile_validity()

    def connectAll(self):
        """Do all initial connections of Gui elements."""
        QObject.connect(self.createNewButton, SIGNAL("clicked()"), self.create_new_pressed)
        QObject.connect(self.replaceLayerButton, SIGNAL("clicked()"), self.replace_layer_pressed)
        QObject.connect(self.addLayerButton, SIGNAL("clicked()"), self.add_layer_pressed)
        # when a layer is added or removed in the layer tree, update combo box
        QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layersAdded(QList<QgsMapLayer *>)"), self.update_ms_layer_list)
        QObject.connect(QgsMapLayerRegistry.instance(), SIGNAL("layersWillBeRemoved(QStringList)"), self.ms_layer_list_remove)
        # when the combobox is changed, then switch editor
        QObject.connect(self.msLayerList, SIGNAL("currentIndexChanged(int)"), self.edit_chosen_layer)
        QObject.connect(self.autorefresh, SIGNAL("toggled(bool)"), self.update_autorefresh)
        QObject.connect(self.editor, SIGNAL("textChanged()"), self.display_mapfile_validity)
        # connect the open and save buttons
        QObject.connect(self.openButton, SIGNAL("clicked()"), self.open_file)
        QObject.connect(self.exportButton, SIGNAL("clicked()"), self.export_file)

    def open_file(self):
        """Open a new Mapfile selected by user."""
        self.msLayerList.clearEditText()
        filename = QFileDialog.getOpenFileName(self,
                "Open Mapfile", "~", "Mapserver Mapfile (*.map)")
        self.editor.load(filename)
        # create temporary file
        fd, self.temp_mapfile = mkstemp(suffix='.map', prefix = 'mapfile_tools_', text = True)
        # write mapfile content to the temp file
        self.update_file()

    def export_file(self):
        """Export the current Mapfile to file selected by user."""
        filename = QFileDialog.getSaveFileName(self, "Export Mapfile", "~",
                "Mapserver Mapfile (*.map)")
        self.update_file()
        copyfile(self.temp_mapfile, filename)

    def display_mapfile_validity(self):
        """Display on GUI the validity of current mapfile."""
        layerid = self.msLayerList.itemData(self.msLayerList.currentIndex()).toString()
        layer = QgsMapLayerRegistry.instance().mapLayer(layerid)
        if layer is not None:
            self.update_file()
            message = layer.maprenderer.load_mapfile(self.temp_mapfile)
            layer.messageTextEdit.append(message)
            mapobj = layer.maprenderer.getMapObj()
            if mapobj is None:
                self.addLayerButton.setEnabled(False)
                self.replaceLayerButton.setEnabled(False)
            else:
                self.addLayerButton.setEnabled(True)
                self.replaceLayerButton.setEnabled(True)
                self.editor.markerDeleteAll()
            # display error line
            regexp = re.compile('.*\(line ([0-9]*)\)')
            try:
                # get error line number
                linenb = int(regexp.findall(message.split("\n")[-1])[-1])
                # add a marker on error line in editor
                # FIXME : move this code into editor's mark_error()
                self.editor.markerAdd(linenb - 1, self.editor.ARROW_MARKER_NUM)
            except ValueError:
                # error not understood, just ignore
                pass
            except IndexError:
                pass

    def update_autorefresh(self):
        """Connect or disconnect autorefresh according to combobox state."""
        if self.autorefresh.isChecked():
            QObject.disconnect(self.editor, SIGNAL("textChanged()"), self.display_mapfile_validity)
            QObject.connect(self.editor, SIGNAL("textChanged()"), self.refresh_layer)
        else:
            QObject.disconnect(self.editor, SIGNAL("textChanged()"), self.refresh_layer)
            QObject.connect(self.editor, SIGNAL("textChanged()"), self.display_mapfile_validity)

    def refresh_layer(self):
        """Refresh layer for auto-refresh, if mapfile is valid."""
        # indicate that mapfile is valid
        self.display_mapfile_validity()
        # same as if we pressed refresh layer button
        if self.replaceLayerButton.isEnabled():
            self.replace_layer_pressed()

    def create_new_pressed(self):
        """Create new Mapfile from default template."""
        self.msLayerList.clearEditText()
        self.editor.load(self.parent.template_dir + "/default.map")
        # create temporary file
        fd, self.temp_mapfile = mkstemp(suffix='.map', prefix = 'mapfile_tools_', text = True)
        # write mapfile content to the temp file
        self.update_file()

    def add_layer_pressed(self):
        """Add current Mapfile to layer."""
        self.update_file()
        name = ""
        if self.msLayerList.currentText == '':
            name = self.get_new_layer_name()
        else:
            name = self.msLayerList.currentText()
        self.parent.addLayer(self.temp_mapfile, name = name)

    def replace_layer_pressed(self):
        """Replace selected layer with current mapfile."""
        self.update_file()
        # get layer object for currently selected layer in combobox
        layerid = self.msLayerList.itemData(self.msLayerList.currentIndex()).toString()
        self.msLayerList.setItemText(self.msLayerList.currentIndex(), self.msLayerList.currentText())
        layer = QgsMapLayerRegistry.instance().mapLayer(layerid)
        layer.loadMapfile(self.temp_mapfile, name = self.msLayerList.currentText())

    def get_new_layer_name(self):
        """Get current text in combobox for new layer name."""
        template = 'New Layer %s'
        layer_name = self.msLayerList.currentText()
        if not layer_name:
            i = 1
            layer_name = template % i
            while self.msLayerList.findText(layer_name) <> -1 :
                i = i + 1
                layer_name = template % i
        return layer_name

    def closeEvent(self, event):
        self.parent.dock_window = None

    def update_file(self):
        """Update file on disk with editor's content."""
        with open(self.temp_mapfile, "w+") as f:
            f.write(self.editor.getText())

    def update_ms_layer_list(self):
        """Update combo box with every ms layer available."""
        # the combobox should be updated on every layer list modification
        self.msLayerList.clear()
        for layer in self.iface.mapCanvas().layers():
            if isinstance(layer, MapfileLayer):
                self.msLayerList.addItem(layer.name(), layer.id())

    def ms_layer_list_remove(self, layer_list):
        """Remove layers to be deleted from combobox."""
        # if current mapfile is in deleted layer list, clear the editor
        if self.msLayerList.itemData(self.msLayerList.currentIndex()).toString() in layer_list:
            self.editor.setText('')
        for layer_id in layer_list:
            self.msLayerList.removeItem(self.msLayerList.findData(layer_id))

    def edit_chosen_layer(self, idx):
        """Edit the layer found in combobox."""
        self.edit_layer(self.msLayerList.itemData(idx).toString())

    def edit_layer(self, layerid):
        """Edit mapfile for given layer id"""
        layer = QgsMapLayerRegistry.instance().mapLayer(str(layerid))
        if isinstance(layer, MapfileLayer):
            # save current file
            self.update_file()
            # make sure the combobox is set to the given layer id
            self.msLayerList.setCurrentIndex(self.msLayerList.findData(layerid))
            # FIXME : we should check if file has been modified since last saved  to user file ?
            # switch editor content to corresponding mapfile
            if layer.mapfile:
                self.editor.load(layer.mapfile)
            else:
                self.editor.setText("Mapfile not found.")
            self.temp_mapfile = layer.mapfile


