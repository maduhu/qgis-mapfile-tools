# -*- coding: utf-8 -*-
"""
/***************************************************************************
MapfileTools
A QGIS plugin
MapServer Mapfile Tools
                             -------------------
begin                : 2009-09-09
copyright            : (C) 2009 by Sourcepole
email                : info at sourcepole dot ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

import resources_rc

from mapfile_layer import MapfileLayer
from mapfile_plugin_layer_type import MapfilePluginLayerType
from dock_editor import DockEditor
from message_window import MessageWindow

class MapfileTools:

  def __init__(self, iface):
    # Save reference to the QGIS interface
    self.iface = iface
    # get paths
    self.user_plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins"
    self.mapfiletools_plugin_dir = self.user_plugin_dir + "/mapfile_tools"
    self.template_dir = self.mapfiletools_plugin_dir + "/templates"

    self.dock_window = None

  def initGui(self):
    # Create action that will start plugin configuration
    self.actionLayer = QAction(QIcon(":/plugins/mapfile_tools/icon.png"), "Toggle dock", self.iface.mainWindow())
    # Action activate plugin dock editor
    QObject.connect(self.actionLayer, SIGNAL("triggered()"), self.toggleEditor)

    # Add toolbar button and menu item
    self.iface.addToolBarIcon(self.actionLayer)
    self.iface.addPluginToMenu("Mapfile Tools", self.actionLayer)

    # Register plugin layer type
    QgsPluginLayerRegistry.instance().addPluginLayerType(MapfilePluginLayerType(self))
    # create dock
    self.dock_editor = DockEditor(self)
    self.iface.mainWindow().addDockWidget(Qt.RightDockWidgetArea, self.dock_editor)
 
  def unload(self):
    # Remove the plugin menu item and icon
    self.iface.removePluginMenu("Mapfile Tools",self.actionLayer)
    self.iface.removeToolBarIcon(self.actionLayer)

    # Unregister plugin layer type
    QgsPluginLayerRegistry.instance().removePluginLayerType(MapfileLayer.LAYER_TYPE)

  def messageTextEdit(self):
    if not self.dock_window:
        self.dock_window = MessageWindow(self)
        self.iface.mainWindow().addDockWidget( Qt.BottomDockWidgetArea,
                                                self.dock_window )
    return self.dock_window.textEdit

  def toggleEditor(self):
    if self.dock_editor.isVisible():
      self.dock_editor.hide()
    else:
      self.dock_editor.show()

  def addLayer(self):
    # add new mapfile layer
    mapfileLayer = MapfileLayer(self.messageTextEdit())
    if mapfileLayer.openMapfile(): #mapfileLayer.showProperties():
      QgsMapLayerRegistry.instance().addMapLayer(mapfileLayer)

      # use mapfile extents for initial view if this is the only layer
      if self.iface.mapCanvas().layerCount() == 1:
        extents = mapfileLayer.maprenderer.getExtents()
        self.iface.mapCanvas().setExtent(QgsRectangle(extents[0], extents[1], extents[2], extents[3]))
        self.iface.mapCanvas().refresh()

# vim: set filetype=python expandtab tabstop=2 shiftwidth=2 autoindent smartindent:
