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

from copy import deepcopy

from .stereograph_input import StereoGraphInputWidget

# from stereograph_plot_settings import StereoGraphPltSettingsWidget

# APSG library by Ondro Lexa: https://github.com/ondrolexa/apsg
try:
    from apsg import *
except ImportError:
    mod_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mod', 'apsg-0.6.4-py2.py3-none-any.whl')
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

        self.build_collapsible()

        self.layer_dict = {}
        self.layers = None

        self.survey_layers()

        self.btn_add_set.clicked.connect(self.open_dataset_dialog)
        self.btn_test.clicked.connect(self.test_case)

    def _load_test(self):
        from qgis.core import QgsVectorLayer

        lines_path = os.path.join(os.path.dirname(__file__), "test", "data", "structures", "lines.shp")
        planes_path = os.path.join(os.path.dirname(__file__), "test", "data", "structures", "planes.shp")

        self.lines_layer = QgsVectorLayer(lines_path, "Lines", "ogr")
        self.planes_layer = QgsVectorLayer(planes_path, "Planes", "ogr")

        if not self.lines_layer.isValid() and not self.planes_layer.isValid():
            print("Layer failed to load!")

        else:
            QgsProject.instance().addMapLayer(self.lines_layer)
            QgsProject.instance().addMapLayer(self.planes_layer)

            self.btn_add_set.setCheckable(True)
            self.btn_add_set.toggle()

    """
    def unload_test(self):
        QgsProject.instance().removeMapLayers([self.lines_layer.id(), self.planes_layer.id()])
    """

    def test_case(self):
        self._load_test()

        self.layer_dict[self.lines_layer.id()] = {
            "layer": self.lines_layer,
            "properties": {
                "row": 0,
                "index_type": 1,
                "type": None,
                "index_format": 0,
                "format": None,
                "field_0": None,
                "field_1": None,
                "index_field_0": 2,
                "index_field_1": 3,
            },
        }

        self.layer_dict[self.planes_layer.id()] = {
            "layer": self.planes_layer,
            "properties": {
                "row": 1,
                "index_type": 2,
                "type": None,
                "index_format": 0,
                "format": None,
                "field_0": None,
                "field_1": None,
                "index_field_0": 2,
                "index_field_1": 3,
            },
        }

        self.open_dataset_dialog(close=True)

    def layers_added(self, layers):
        """
        Process the signal of added layers.

        :param layers: List of added layers.
        """

        for layer in layers:
            self.process_layer_dict(layer)

    def layer_removed(self, layer_id):
        """Process the signal of removed layers.

        :param layer_id: A removed layer ID.
        """

        def remove_key(layer_dict, key):
            copy = dict(layer_dict)
            del copy[key]

            return copy

        self.layer_dict = remove_key(self.layer_dict, layer_id)

    @staticmethod
    def check_layer_type(layer):
        """
        Check the layer type. Only accept vector layers.

        :param layer: QGIS layer to be checked, as tuple.

        :returns layer: QGIS layer if vector layer.
        """

        # layer is a tuple, e.g. ('lines_dfb84f76_7835_4663_8da0_d43d8c1620f7', <QgsMapLayer: 'lines' (ogr)>)
        if layer[1].type() == QgsMapLayerType.VectorLayer:
            return layer[1]

    def survey_layers(self):
        for layer in QgsProject.instance().mapLayers().items():
            vlayer = self.check_layer_type(layer)
            self.process_layer_dict(vlayer)

        QgsProject.instance().layersAdded.connect(self.layers_added)
        QgsProject.instance().layerRemoved.connect(self.layer_removed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def process_layer_dict(self, layer):
        """
        Build a dictionary with information of all valid vector layers in use.

        :param layer: QGIS vector layer.
        """

        # layer ID is used as key
        # layer ID is unique for the current QGIS session
        # NOTE: If computing on reloaded layers in the plugin,
        # exchange layer IDs in that dictionary with the renewed QGIS layer ID from the TOC
        # incorporate layer itslef in the dictionary to get a pointer to the field names in later stages

        #self.layers.append(layer)

        self.layer_dict[layer.id()] = {
            "layer": layer,
            "properties": {
                "row": None,
                "index_type": 0,
                "type": None,
                "index_format": 0,
                "format": None,
                "field_0": None,
                "field_1": None,
                "index_field_0": 0,
                "index_field_1": 0,
            },
        }

    def open_dataset_dialog(self, close=False):
        """Open a separate window to load data from disk or to create new dataset from scratch.
        """

        self.dlg_input = StereoGraphInputWidget(self.layer_dict)

        if close:
            self.dlg_input.close()

        else:
            self.dlg_input.show()
            self.dlg_input.exec_()

        self.layer_dict = self.dlg_input.layers
        #self.tbl_layers = dlg_input.tbl_layers

        # get layers from layer dictionary
        self.layers = [self.layer_dict[key]["layer"] for key in self.layer_dict.keys()]

        self.insert_datasets(self.dlg_input.tbl_layers)

        self.cmb_set.currentIndexChanged.connect(self.insert_input_data)

    def insert_datasets(self, input_table):
        """Fill dataset table"""

        self.tbl_sets.setRowCount(input_table.rowCount())

        for row in range(input_table.rowCount()):
            dlg_layer = QtWidgets.QTableWidgetItem(input_table.item(row, 0).text())
            dlg_type = QtWidgets.QTableWidgetItem(input_table.cellWidget(row, 1).currentText())
            dlg_format = QtWidgets.QTableWidgetItem(input_table.cellWidget(row, 2).currentText())

            self.tbl_sets.setItem(row, 0, dlg_layer)
            self.tbl_sets.setItem(row, 1, dlg_type)
            self.tbl_sets.setItem(row, 2, dlg_format)

        self._fill_dataset_combobox()

    def _fill_dataset_combobox(self):
        # write layer names to dataset combobox
        self.cmb_set.clear()
        self.cmb_set.addItems([layer.name() for layer in self.layers])

    def _build_dataset_table_header(self):
        # get layer from the combobox
        index = self.cmb_set.currentIndex()

        # self.layers[index].id() gives the QGIS-internal layer ID
        field_0 = self.layers[index].fields().names()[self.layer_dict[self.layers[index].id()]["properties"]["index_field_0"]]
        field_1 = self.layers[index].fields().names()[self.layer_dict[self.layers[index].id()]["properties"]["index_field_1"]]

        # set header of input table
        self.tbl_input.setHorizontalHeaderLabels(["ID", field_0, field_1])

    def _insert_data(self):
        # get layer from the combobox
        index = self.cmb_set.currentIndex()
        # set row count of input data table to length of selected layer
        self.tbl_input.setRowCount(len(self.layers[index]))

        for row in range(self.tbl_input.rowCount()):
            feature = self.layers[index].getFeature(row)

            # set id
            if feature.attributes()[0]:
                id = feature.attributes()[0]

            else:
                id = feature.id()

            col_0 = QtWidgets.QTableWidgetItem()
            col_1 = QtWidgets.QTableWidgetItem()
            col_2 = QtWidgets.QTableWidgetItem()

            # self.layer_dict[self.layers[index].id()]["properties"]["index_field_0"] refers to the field index of the vector file
            # e.g. the field header of the feature has the index 2
            col_0.setData(Qt.EditRole, id)
            col_1.setData(Qt.EditRole, feature.attributes()[self.layer_dict[self.layers[index].id()]["properties"]["index_field_0"]])
            col_2.setData(Qt.EditRole, feature.attributes()[self.layer_dict[self.layers[index].id()]["properties"]["index_field_1"]])

            self.tbl_input.setItem(row, 0, col_0)
            self.tbl_input.setItem(row, 1, col_1)
            self.tbl_input.setItem(row, 2, col_2)

    def insert_input_data(self):
        self._build_dataset_table_header()
        self._insert_data()
        self.create_plot()

    """
    def pick_from_plot(self, event):
        this_item = event.artist
        xdata = this_item.get_xdata()
        ydata = this_item.get_ydata()
        ind = event.ind

        points = tuple(zip(xdata[ind], ydata[ind]))

        #print('Points: ', points)
        #print('X = ' + str(np.take(xdata, ind)[0]))
        #print('Y = ' + str(np.take(ydata, ind)[0]))
        print(self.stereonet.draw().contains(event))
    """

    def create_plot(self):
        # add stereographic chart
        self.stereonet = StereoNet()
        self.plot_layout.addWidget(self.stereonet.fig.canvas)

        #print(self.tbl_input.item(0, 1).data(Qt.EditRole))

        index = self.cmb_set.currentIndex()

        # get the dictionary of stereographic types
        # get the index of the stereographic type
        # get the current type
        types = list(self.dlg_input.type_entries.values())
        index_type = self.layer_dict[self.layers[index].id()]["properties"]["index_type"]
        current_type = types[index_type]

        if current_type == "Planes":
            for row in range(self.tbl_input.rowCount()):
                x = self.tbl_input.item(row, 1).data(Qt.EditRole)
                y = self.tbl_input.item(row, 2).data(Qt.EditRole)

                self.stereonet.plane(Fol(x, y))
            #self.stereonet.plane(aFol(1, 2))
            #self.stereonet.plane(aFol(value_1, value_2), color=plt_color, linestyle=style, picker=5)
        #self.stereonet.fig.canvas.mpl_connect('pick_event', self.pick_from_plot)

        self.stereonet.draw()

    def build_collapsible(self):
        table = CollapsibleTable("lalalala")
        self.scrollArea.setWidget(table)


class CollapsibleTable(QtWidgets.QTableWidget):
    def __init__(self, title="lala", parent=None):
        super(CollapsibleTable, self).__init__(parent)

        self.toggle_button = QtWidgets.QToolButton()#text=title, checkable=True, checked=False)
        self.toggle_button.setStyleSheet("QToolButton { border: none; }")
        self.toggle_button.setToolButtonStyle(
            QtCore.Qt.ToolButtonTextBesideIcon
        )
        self.toggle_button.setArrowType(QtCore.Qt.RightArrow)

        self.toggle_button.pressed.connect(self.on_pressed)

        self.toggle_animation = QtCore.QParallelAnimationGroup(self)

        self.content_area = QtWidgets.QScrollArea(
            maximumHeight=0, minimumHeight=0
        )
        self.content_area.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.content_area.setFrameShape(QtWidgets.QFrame.NoFrame)

    @QtCore.pyqtSlot()
    def on_pressed(self):
        pass