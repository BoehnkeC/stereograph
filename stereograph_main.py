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

from qgis.PyQt import QtWidgets, uic
from PyQt5.QtWidgets import QTableWidgetItem
from qgis.PyQt.QtCore import pyqtSignal
from PyQt5.QtCore import Qt
from qgis.core import QgsProject, QgsMapLayerType,QgsFeatureRequest

from copy import deepcopy

from .stereograph_input import StereoGraphInputWidget

# from stereograph_plot_settings import StereoGraphPltSettingsWidget

# APSG library by Ondro Lexa: https://github.com/ondrolexa/apsg
try:
    import apsg
except ImportError:
    mod_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mod', 'apsg-0.6.4-py2.py3-none-any.whl')
    sys.path.append(mod_path)
    import apsg

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

        self.layer_dict = {}
        self.layers = None

        self.btn_add_set.clicked.connect(self.open_dataset_dialog)

        self.survey_layers()

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

    def open_dataset_dialog(self):
        """Open a separate window to load data from disk or to create new dataset from scratch.
        """

        dlg_input = StereoGraphInputWidget(self.layer_dict)
        dlg_input.show()
        dlg_input.exec_()

        self.layer_dict = dlg_input.layers
        #self.tbl_layers = dlg_input.tbl_layers

        # get layers from layer dictionary
        self.layers = [self.layer_dict[key]["layer"] for key in self.layer_dict.keys()]

        self.cmb_set.currentIndexChanged.connect(self.insert_input_data)

        self.insert_datasets(dlg_input.tbl_layers)
        self.fill_dataset_combobox()

    def insert_datasets(self, input_table):
        self.tbl_sets.setRowCount(input_table.rowCount())

        for row in range(input_table.rowCount()):
            dlg_layer = QTableWidgetItem(input_table.item(row, 0).text())
            dlg_type = QTableWidgetItem(input_table.cellWidget(row, 1).currentText())
            dlg_format = QTableWidgetItem(input_table.cellWidget(row, 2).currentText())

            self.tbl_sets.setItem(row, 0, dlg_layer)
            self.tbl_sets.setItem(row, 1, dlg_type)
            self.tbl_sets.setItem(row, 2, dlg_format)

    def fill_dataset_combobox(self):
        # write layer names to dataset combobox
        self.cmb_set.clear()
        self.cmb_set.addItems([layer.name() for layer in self.layers])

    def _build_dataset_table_header(self):
        # get layer from the combobox
        index = self.cmb_set.currentIndex()
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

            col_0 = QTableWidgetItem()
            col_1 = QTableWidgetItem()
            col_2 = QTableWidgetItem()

            col_0.setData(Qt.EditRole, id)
            col_1.setData(Qt.EditRole, feature.attributes()[1])
            col_2.setData(Qt.EditRole, feature.attributes()[2])

            self.tbl_input.setItem(row, 0, col_0)
            self.tbl_input.setItem(row, 1, col_1)
            self.tbl_input.setItem(row, 2, col_2)

    def insert_input_data(self):
        self._build_dataset_table_header()
        self._insert_data()
