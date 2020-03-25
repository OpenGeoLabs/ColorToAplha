# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : ColorToAlpha
Description          : ColorToAlpha
Date                 : 23/Mar/2020
copyright            : (C) 2020 by OpenGeoLabs
email                : podpora@opengeolabs.cz
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
from __future__ import print_function
from __future__ import absolute_import
from builtins import object
# Import the PyQt and QGIS libraries
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
try:
    from qgis.PyQt.QtWidgets import *
except:
    pass
from qgis.core import *

import os
import inspect

from .ColorToAlphaDockWidget import ColorToAlphaDockWidget

class ColorToAlpha(object):

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.pluginIsActive = False
        self.dockwidget = None

    def initGui(self):
        current_directory = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        self.action = QAction(QIcon(os.path.join(current_directory, "icons", "colortoalpha_icon.png")),
             "&ColorToAlpha", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("ColorToAlpha", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("ColorToAlpha", self.action)
        self.iface.removeToolBarIcon(self.action)

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING AeroGen"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = ColorToAlphaDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()