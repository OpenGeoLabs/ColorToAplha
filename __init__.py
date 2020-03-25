# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name			 	 : ColorToAlpha
Description          : ColorToAlpha for Directory of GeoTIFF files
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
 This script initializes the plugin, making it known to QGIS.
"""


def classFactory(iface):
    # load ColorToAlpha class from file ColorToAlpha
    from .ColorToAlpha import ColorToAlpha
    return ColorToAlpha(iface)
