# Makefile for a PyQGIS plugin 

PLUGINNAME = mapfile_tools

PY_FILES =

EXTRAS =

UI_FILES = ui_mapfile_layer.py ui_message_window.py ui_dock_editor.py

RESOURCE_FILES = resources_rc.py

default: compile

compile: $(UI_FILES) $(RESOURCE_FILES)

%_rc.py : %.qrc
	pyrcc4 -o $@  $<

%.py : %.ui
	pyuic4 -o $@ $<

# The deploy  target only works on unix like operating system where
# the Python plugin directory is located at:
# $HOME/.qgis/python/plugins
deploy-local: compile
	mkdir -p $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(PY_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(UI_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(RESOURCE_FILES) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)
	cp -vf $(EXTRAS) $(HOME)/.qgis/python/plugins/$(PLUGINNAME)

deploy: compile
	echo "Deploy remote repo (don't forget to push first!)"
	ssh -t root@vilan.sourcepole.ch "vserver builder exec su - builder sh -c ./qgis-plugins-update"
