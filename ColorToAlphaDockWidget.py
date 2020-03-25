# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ColorToAlphaDockWidget
                                 A QGIS plugin
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

import os
import numpy

from qgis.PyQt import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal, QSettings, Qt
from qgis.PyQt.QtWidgets import QDockWidget, QFileDialog, QProgressBar

from qgis.core import QgsProject, QgsCoordinateReferenceSystem, QgsVectorFileWriter, QgsWkbTypes, Qgis
from qgis.utils import iface

from osgeo import gdal
from osgeo.gdalnumeric import *
from osgeo.gdalconst import *


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ColorToAlphaDockWidgetBase.ui'))


class ColorToAlphaDockWidget(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(ColorToAlphaDockWidget, self).__init__(parent)

        self.setupUi(self)

        # settings
        self._settings = QSettings()

        # reader
        self._ar = None
        self._rsCrs = None
        self._destCrs = None

        self.browseButton.clicked.connect(self.OnBrowseInput)
        self.generateButton.clicked.connect(self.OnGenerate)
        self.outputButton.clicked.connect(self.OnBrowseOutput)

        # disable some widgets
        self.outputButton.setEnabled(False)
        self.generateButton.setEnabled(False)
        
    def closeEvent(self, event):
        """Closing the plugin."""
        self.closingPlugin.emit()
        event.accept()

    def OnBrowseInput(self):
        """Browse for input directory. Set values and enables the output directory button."""
        sender = 'ColorToAlpha-{}-lastUserFilePath'.format(self.sender().objectName())
        # load lastly used directory path
        lastPath = self._settings.value(sender, '')

        directoryPath = QFileDialog.getExistingDirectory(self, self.tr("Directory with GeoTIFF files"),
                                                     lastPath)

        if not directoryPath:
            # action canceled
            return

        directoryPath = os.path.normpath(directoryPath)
        self.textInput.setText(directoryPath)

        self.outputButton.setEnabled(True)
        
        # remember directory path
        self._settings.setValue(sender, os.path.dirname(directoryPath))

    def OnBrowseOutput(self):
        """Browse for output directory. Set values and enables the Convert button."""
        sender = 'ColorToAlpha-{}-lastUserOutputFilePath'.format(self.sender().objectName())
        # load lastly used directory path
        lastPath = self._settings.value(sender, self.textInput.toPlainText())

        filePath = QFileDialog.getExistingDirectory(self, self.tr('Output Directory'), lastPath)
        if not filePath:
            # action canceled
            return

        filePath = os.path.normpath(filePath)
        self.textOutput.setText(filePath)
        self.generateButton.setEnabled(True)

        # remember directory path
        self._settings.setValue(sender, os.path.dirname(filePath))

    def OnGenerate(self):
        """Reads the directory and other input values. Loops the TIF files and runs the conversion."""

        input_dir = self.textInput.toPlainText()
        output_dir = self.textOutput.toPlainText()
        if input_dir == output_dir:
            iface.messageBar().pushMessage(
                self.tr("Error"),
                self.tr("The input and output directories must differ"),
                level=Qgis.Critical
            )
            return

        directory = os.fsencode(input_dir)

        # Sets the color values
        r_color = self.mColorButton.color().red()
        g_color = self.mColorButton.color().green()
        b_color = self.mColorButton.color().blue()

        # Sets the progress bar item to show progress in the loop
        progressMessageBar = iface.messageBar().createMessage("Converting...")
        progress = QProgressBar()
        progress.setMaximum(len(os.listdir(directory)))
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

        i = 0
        # Loop the directory
        for file in os.listdir(directory):
            progress.setValue(i + 1)
            filename = os.fsdecode(file)
            if filename.endswith(".tif"):
                src_filename = os.path.join(input_dir, filename)
                dst_filename = os.path.join(output_dir, filename)
                try:
                    self.addAlpha(src_filename, dst_filename, r_color, g_color, b_color)
                except:
                    iface.messageBar().pushMessage(
                        self.tr("Error"),
                        self.tr("The conversion did not work. Please check input and out directories."),
                        level=Qgis.Critical
                    )
                    return

        # If succeeded the message appears
        iface.messageBar().clearWidgets()
        iface.messageBar().pushMessage(
                self.tr("Success"),
                self.tr("Output layers saved to {}").format(output_dir),
                level=Qgis.Success
        )

    def addAlpha(self, src_filename, dst_filename, r_color, g_color, b_color):
        """Converts the color to alpha."""

        # Opent the file
        src_ds = gdal.Open(src_filename, gdal.GA_ReadOnly)
        # If can not read we skip it and show the Error message
        if not src_ds:
            iface.messageBar().pushMessage(
                self.tr("Warning"),
                self.tr("The file {} is corrupted").format(src_filename),
                level=Qgis.Critical
            )
            return


        fileformat = "GTiff"
        driver = gdal.GetDriverByName(fileformat)
        # We copy the original file
        tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)

        # If the original does not have Alpha channel we add it
        if src_ds.RasterCount < 4:
            tmp_ds.AddBand()

        # We copy temporary file into the output
        dst_ds = driver.CreateCopy(dst_filename, tmp_ds, strict=0, options=["TILED=YES", "COMPRESS=LZW", 'PHOTOMETRIC=RGBA'])

        # Get the output bands
        output_band_r = dst_ds.GetRasterBand(1)
        output_band_g = dst_ds.GetRasterBand(2)
        output_band_b = dst_ds.GetRasterBand(3)
        output_band_alpha = dst_ds.GetRasterBand(4)
        # Sets the metadata for bands
        output_band_alpha.SetColorInterpretation(gdal.GCI_AlphaBand)
        output_band_r.SetNoDataValue(-1)
        output_band_g.SetNoDataValue(-1)
        output_band_b.SetNoDataValue(-1)

        # Get the input bands
        band_r = src_ds.GetRasterBand(1)
        band_g = src_ds.GetRasterBand(2)
        band_b = src_ds.GetRasterBand(3)

        # We read file row by row
        for row in range(band_r.YSize):

            # Read one row from each band
            r_data = BandReadAsArray(band_r, xoff=0, yoff=row, win_xsize=band_r.XSize, win_ysize=1, buf_type=gdal.GDT_Int32)
            g_data = BandReadAsArray(band_g, xoff=0, yoff=row, win_xsize=band_r.XSize, win_ysize=1, buf_type=gdal.GDT_Int32)
            b_data = BandReadAsArray(band_b, xoff=0, yoff=row, win_xsize=band_r.XSize, win_ysize=1, buf_type=gdal.GDT_Int32)

            # Construct one integer value from all bands
            rgb = (r_data * 1000000) + (g_data * 1000) + b_data

            # Find the value of specified color and create alpha channel
            valtotest = (r_color * 1000000) + (g_color * 1000) + b_color
            alpha = numpy.where(rgb == valtotest, 0, 255)

            # Set -1 -1 -1 for the alpha value as well to have NODATA
            rgb = numpy.where(rgb == valtotest, -1001001, rgb)

            # Decompose integer value of the color into bands
            rgb_r = numpy.around(rgb / 1000000)
            rgb_g = numpy.around((rgb - (numpy.around(rgb / 1000000) * 1000000)) / 1000)
            rgb_b = rgb - (numpy.around(rgb / 1000000) * 1000000) - (
                    (numpy.around((rgb - (numpy.around(rgb / 1000000) * 1000000)) / 1000)) * 1000)

            # Write one row for each band into output
            BandWriteArray(dst_ds.GetRasterBand(1), rgb_r, xoff=0, yoff=row)
            BandWriteArray(dst_ds.GetRasterBand(2), rgb_g, xoff=0, yoff=row)
            BandWriteArray(dst_ds.GetRasterBand(3), rgb_b, xoff=0, yoff=row)
            BandWriteArray(dst_ds.GetRasterBand(4), alpha, xoff=0, yoff=row)