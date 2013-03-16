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
from mapfile_renderer import MapfileRenderer

class DockEditor(QDockWidget, Ui_DockEditor):
    def __init__(self, parent, messageTextEdit = None):
        QDockWidget.__init__(self, parent.iface.mainWindow())
        # temporary file for mapfile
        # create a temporary file for current editor content
        fd, self.temp_mapfile = mkstemp(suffix='.map', prefix = 'mapfile_tools_', text = True)
        self.template_dir = str(parent.template_dir)

        # where to log messages
        self.messageTextEdit = messageTextEdit

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
        # initially, nothing loaded, deactivate add and refresh buttons
        self.replaceLayerButton.setEnabled(False)
        self.addLayerButton.setEnabled(False)

        # fill in the combobox
        self.update_ms_layer_list()

        # fill in template comboboxes
        self.update_full_templates()
        self.update_partial_templates()

        # connect signals and slots
        self.connectAll()
        self.update_autorefresh()
        self.display_mapfile_validity()

    def connectAll(self):
        """Do all initial connections of Gui elements."""
        QObject.connect(self.replaceLayerButton, SIGNAL("clicked()"), self.replace_layer_pressed)
        QObject.connect(self.addLayerButton, SIGNAL("clicked()"), self.add_layer_pressed)
        # templates
        QObject.connect(self.loadFullDefault, SIGNAL("clicked()"), self.load_full_default_pressed)
        QObject.connect(self.loadFullButton, SIGNAL("clicked()"), self.load_full_template_pressed)
        QObject.connect(self.loadPartialButton, SIGNAL("clicked()"), self.load_partial_template_pressed)
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

    def update_full_templates(self):
        """Update full template combobox with file list."""
        regexp = re.compile("full_.*\.map")
        for filename in os.listdir(self.template_dir):
            if regexp.match(os.path.basename(filename)) is not None:
                self.fullTemplatesList.addItem(os.path.basename(filename)[5:-4], filename)
        if self.fullTemplatesList.count() == 0:
            self.loadFullButton.setEnabled(False)
        
    def update_partial_templates(self):
        """Update partial templates combobox with file list."""
        regexp = re.compile("partial_.*\.map")
        for filename in os.listdir(self.template_dir):
            if regexp.match(os.path.basename(filename)) is not None:
                self.partialTemplatesList.addItem(os.path.basename(filename)[8:-4], filename)
        if self.partialTemplatesList.count() == 0:
            self.loadPartialButton.setEnabled(False)

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
        self.display_mapfile_validity()

    def export_file(self):
        """Export the current Mapfile to file selected by user."""
        filename = QFileDialog.getSaveFileName(self, "Export Mapfile", "~",
                "Mapserver Mapfile (*.map)")
        self.update_file()
        copyfile(self.temp_mapfile, filename)

    def display_mapfile_validity(self):
        """Display on GUI the validity of current mapfile."""
        if self.editor.getText() <> '' and self.temp_mapfile and os.path.exists(self.temp_mapfile):
            self.update_file()
            renderer = MapfileRenderer(self.temp_mapfile)
            message = renderer.load_mapfile()
            if self.messageTextEdit is not None:
                self.messageTextEdit.append(message)
            mapobj = renderer.getMapObj()
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
                # error with no line number, just ignore
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

    def load_full_default_pressed(self):
        """Create new Mapfile from default template."""
        self.load_template("default.map", replace = True)

    def load_partial_template_pressed(self):
        """Insert currently selected template into editor."""
        idx = self.partialTemplatesList.currentIndex()
        if idx <> -1:
            self.load_template(str(self.partialTemplatesList.itemData(idx).toString()))

    def load_full_template_pressed(self):
        """Load currently selected template into editor."""
        idx = self.partialTemplatesList.currentIndex()
        if idx <> -1:
            self.load_template(str(self.fullTemplatesList.itemData(idx).toString()), replace = True)

    def load_template(self, template_name, replace = False):
        """Insert a template into the editor."""
        if replace:
            self.editor.load(os.path.join(self.template_dir, str(template_name)))
        else:
            self.editor.insertFileAtPosition(os.path.join(self.template_dir, str(template_name)))
        # write mapfile content to the temp file
        self.update_file()
        self.display_mapfile_validity()

    def add_layer_pressed(self):
        """Add current Mapfile to layer."""
        # new layer => new temp file
        # create temporary file
        fd, layer_mapfile = mkstemp(suffix='.map', prefix = 'mapfile_tools_', text = True)
        # write editor text to current file
        self.update_file()
        # write editor text to layer mapfile
        with open(layer_mapfile, "w+") as f:
            f.write(self.editor.getText())
        # add layer
        self.parent.addLayer(layer_mapfile)

    def replace_layer_pressed(self):
        """Replace selected layer with current mapfile."""
        # save current editor to work file
        self.update_file()
        # get layer object for currently selected layer in combobox
        layerid = self.msLayerList.itemData(self.msLayerList.currentIndex()).toString()
        self.msLayerList.setItemText(self.msLayerList.currentIndex(), self.msLayerList.currentText())
        layer = QgsMapLayerRegistry.instance().mapLayer(layerid)
        if layer and layer.mapfile is not None and os.path.exists(layer.mapfile):
            with open(layer.mapfile, "w+") as f:
                f.write(self.editor.getText())
            layer.reload()
        # update name in msLayerList
        self.msLayerList.setItemText(self.msLayerList.currentIndex(), layer.name())

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

    def layer_mapfile_to_temp_mapfile(self, layer_mapfile):
        """Copy layer mapfile content to temp mapfile."""
        with open(layer_mapfile, "r") as f:
            with open(self.temp_mapfile, "w+") as t:
                t.write(f.read())

    def edit_chosen_layer(self, idx):
        """Edit the layer found in combobox."""
        self.edit_layer(self.msLayerList.itemData(idx).toString())

    def edit_layer(self, layerid):
        """Edit mapfile for given layer id"""
        layer = QgsMapLayerRegistry.instance().mapLayer(str(layerid))
        if isinstance(layer, MapfileLayer):
            # FIXME : we should check if file has been modified since last saved  to user file ?
            # make sure the combobox is set to the given layer id
            self.msLayerList.setCurrentIndex(self.msLayerList.findData(layerid))
            # switch editor content to corresponding mapfile
            if layer.mapfile is not None and os.path.exists(layer.mapfile):
                self.layer_mapfile_to_temp_mapfile(layer.mapfile)
                self.editor.load(self.temp_mapfile)
            else:
                self.editor.setText("Mapfile not found.")



