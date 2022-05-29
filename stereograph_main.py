# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StereographDockWidget
                                 A QGIS plugin
 This plugin plots structural geological data.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-04-12
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Christian Böhnke
        email                : christian@home-boehnke.de
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
import sys
from pathlib import Path

from qgis.PyQt import uic
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsMapLayerType, QgsFeatureRequest
from .options import Types, TypesIndices, FormatsShort, FormatsLong

# import matplotlibs backend for plotting in PyQT5
# see https://www.geeksforgeeks.org/how-to-embed-matplotlib-graph-in-pyqt5/
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from copy import deepcopy

from .stereograph_input import StereoGraphInputWidget

# from stereograph_plot_settings import StereoGraphPltSettingsWidget

# APSG library by Ondro Lexa: https://github.com/ondrolexa/apsg
try:
    from apsg import *

except ImportError:
    mod_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "mod", "apsg-0.7.0-py2.py3-none-any.whl")
    sys.path.append(mod_path)
    from apsg import *

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "stereograph_gui.ui")
)


class StereographDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(StereographDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        #self.stereonet = StereoNet()
        self.layers = Layers()
        self.removable_layer = None

        # this is the Canvas Widget that
        # displays the 'figure'it takes the
        # 'figure' instance as a parameter to __init__
        #self.canvas = FigureCanvas(self.stereonet.fig)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        #self.toolbar = NavigationToolbar(self.canvas, self)

        # adding tool bar to the layout
        #self.plot_layout.addWidget(self.toolbar)

        # adding canvas to the layout
        #self.plot_layout.addWidget(self.canvas)

        self.survey_layers()  # get layers loaded in QGIS
        self.fill_dataset_combobox()  # insert layers in dataset combobox
        self.fill_types_and_formats()

        self.cmb_set.currentIndexChanged.connect(self.fill_data_table)
        self.cmb_type.currentIndexChanged.connect(self.fill_data_table)
        self.cmb_format.currentIndexChanged.connect(self.fill_data_table)

    def survey_layers(self):
        for layer in QgsProject.instance().mapLayers().items():
            # layer is a tuple, e.g. ('lines_dfb84f76_7835_4663_8da0_d43d8c1620f7', <QgsMapLayer: 'lines' (ogr)>)
            if layer[1].type() == QgsMapLayerType.VectorLayer:
                self.layers.add_layer(Layer(layer[1]))

    def fill_dataset_combobox(self):
        self.cmb_set.clear()

        if len(self.layers.layer_list) > 0:
            self.cmb_set.addItem("Deselect")
            self.cmb_set.addItems([layer.name for layer in self.layers.layer_list])

    def fill_types_and_formats(self):
        self.cmb_type.clear()
        self.cmb_type.addItems([_type.value for _type in Types])

        self.fill_types_combobox()  # nothing selected yet, fill formats with dummy entry

        self.cmb_type.currentIndexChanged.connect(self.type_index_changed)

    def type_index_changed(self):
        self.fill_types_combobox()  # fill formats based on type selection

    def fill_types_combobox(self):
        self.cmb_format.clear()

        if self.cmb_type.currentIndex() == TypesIndices.dummy:
            self.cmb_format.addItem("Please select dataset type.")

        elif self.cmb_type.currentIndex() == TypesIndices.lines:
            self.cmb_format.addItems([_line.value for _line in FormatsShort.Lines])

        elif self.cmb_type.currentIndex() == TypesIndices.planes:
            self.cmb_format.addItems([_plane.value for _plane in FormatsShort.Planes])

        else:
            raise AttributeError("The selected type and format and not implemented.")

    def fill_data_table(self):
        if self.cmb_set.currentIndex() > 0 and self.cmb_type.currentIndex() > 0:
            # header
            # self.layer_list[index].id() gives the QGIS-internal layer ID
            #field_0 = self.layers.layer_list[index].field_0
            #field_1 = self.layers.layer_list[index].field_1

            # set header of input table
            self.tbl_input.setHorizontalHeaderLabels(["ID", "H1", "H2"])

            self.tbl_input.setRowCount(
                self.layers.layer_list[self.cmb_set.currentIndex()].layer.featureCount()
            )

            for row in range(self.tbl_input.rowCount()):
                feature = self.layers.layer_list[self.cmb_set.currentIndex()].layer.getFeature(row)

                # set id
                if feature.attributes()[0]:
                    fid = feature.attributes()[0]

                else:
                    fid = feature.id()

                col_0 = QtWidgets.QTableWidgetItem()
                col_1 = QtWidgets.QTableWidgetItem()
                col_2 = QtWidgets.QTableWidgetItem()

                col_0.setData(Qt.EditRole, fid)
                #col_1.setData(Qt.EditRole, feature.attributes()[self.layers.layer_list[index].index_field_0])
                #col_2.setData(Qt.EditRole, feature.attributes()[self.layers.layer_list[index].index_field_1])

                self.tbl_input.setItem(row, 0, col_0)
                #self.tbl_input.setItem(row, 1, col_1)
                #self.tbl_input.setItem(row, 2, col_2)

        else:
            self.cmb_type.setCurrentIndex(0)
            self.cmb_format.setCurrentIndex(0)

            self.tbl_input.setRowCount(0)
            self.tbl_input.setHorizontalHeaderLabels(["", "", ""])



class Layers:
    def __init__(self):
        self.layer_list = []

    def add_layer(self, layer):
        self.layer_list.append(layer)

    def remove_layer(self, layer):
        self.layer_list.remove(layer)


class Layer:
    def __init__(self, layer=None):
        #self.layer = QgsProject.instance().mapLayers()[layer.layer_id]
        self.layer_id = layer.id()
        self.layer = layer  # QGIS vlayer
        self.name = layer.name()
        self.row = None
        self.cmb_type = None
        self.cmb_format = None
        self.index_type = 0
        self.index_format = 0
        self.field_0 = None
        self.field_1 = None
        self.index_field_0 = 0
        self.index_field_1 = 0
