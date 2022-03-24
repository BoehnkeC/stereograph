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

        self.stereonet = StereoNet()
        self.layers = Layers()
        self.removable_layer = None

        # this is the Canvas Widget that
        # displays the 'figure'it takes the
        # 'figure' instance as a parameter to __init__
        self.canvas = FigureCanvas(self.stereonet.fig)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # adding tool bar to the layout
        self.plot_layout.addWidget(self.toolbar)

        # adding canvas to the layout
        self.plot_layout.addWidget(self.canvas)

        #self.survey_layers()

        # add datasets
        self.btn_add_set.clicked.connect(self.open_dataset_dialog)
        self.btn_test.clicked.connect(self.test_case)
        self.tbl_sets.cellClicked.connect(self.tbl_sets_slot)
        self.btn_rm_set.clicked.connect(self.btn_remove_layer)

        QgsProject.instance().layersRemoved.connect(self.qgs_layer_removed)

        # StereographDockWidget.event.connect()

    def qgs_layer_removed(self, id_list):
        print(id_list[0])
        #print([layer.layer_id for layer in self.layers.layer_list])
        print("#######")

    def btn_remove_layer(self):
        self.layers.remove_layer(self.removable_layer)
        self.btn_rm_set.setEnabled(False)

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

            self.survey_layers()

    """
    def unload_test(self):
        QgsProject.instance().removeMapLayers([self.lines_layer.id(), self.planes_layer.id()])
    """

    def test_case(self):
        self._load_test()

        self.layers.layer_list[0].row = 0
        self.layers.layer_list[0].index_type = 1
        self.layers.layer_list[0].type = "Lines"
        self.layers.layer_list[0].index_format = 0
        self.layers.layer_list[0].format = "TP"
        self.layers.layer_list[0].field_0 = "Trend"
        self.layers.layer_list[0].field_1 = "Plunge"
        self.layers.layer_list[0].index_field_0 = 2
        self.layers.layer_list[0].index_field_1 = 3

        self.layers.layer_list[1].row = 1
        self.layers.layer_list[1].index_type = 2
        self.layers.layer_list[1].type = "Planes"
        self.layers.layer_list[1].index_format = 0
        self.layers.layer_list[1].format = "AD"
        self.layers.layer_list[1].field_0 = "Strike Azimuth"
        self.layers.layer_list[1].field_1 = "Dip Magnitude"
        self.layers.layer_list[1].index_field_0 = 2
        self.layers.layer_list[1].index_field_1 = 3

        self._fill_dataset_combobox()

        self.tbl_sets.setRowCount(len(self.layers.layer_list))

        for row in range(len(self.layers.layer_list)):
            dlg_layer = QtWidgets.QTableWidgetItem(self.layers.layer_list[row].name)
            dlg_type = QtWidgets.QTableWidgetItem(self.layers.layer_list[row].index_type)
            dlg_format = QtWidgets.QTableWidgetItem(self.layers.layer_list[row].index_format)

            self.tbl_sets.setItem(row, 0, dlg_layer)
            self.tbl_sets.setItem(row, 1, dlg_type)
            self.tbl_sets.setItem(row, 2, dlg_format)

        # initially fill input data table with first dataset (default)
        self.insert_input_data(index=0)

        self.cmb_set.currentIndexChanged.connect(self.insert_input_data)

    def tbl_sets_slot(self, row, column):
        self.btn_rm_set.setEnabled(True)
        self.removable_layer = self.layers.layer_list[row]

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
            self.layers.add_layer(Layer(vlayer))

        #QgsProject.instance().layersRemoved.connect(self.qgs_layer_removed)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def open_dataset_dialog(self, close=False):
        """Open a separate window to load data from disk or to create new dataset from scratch.
        """

        self.dlg_input = StereoGraphInputWidget(self.layers)

        if close:
            self.dlg_input.close()

        else:
            self.dlg_input.show()
            self.dlg_input.exec_()

        self.layers = self.dlg_input.layers
        self._fill_dataset_combobox()

        self.insert_datasets(self.dlg_input.tbl_layers)

        self.cmb_set.currentIndexChanged.connect(self.insert_input_data)

    def insert_datasets(self, input_table):
        """Fill dataset table in Datasets tab"""

        self.tbl_sets.setRowCount(input_table.rowCount())

        for row in range(input_table.rowCount()):
            dlg_layer = QtWidgets.QTableWidgetItem(input_table.item(row, 0).text())
            dlg_type = QtWidgets.QTableWidgetItem(input_table.cellWidget(row, 1).currentText())
            dlg_format = QtWidgets.QTableWidgetItem(input_table.cellWidget(row, 2).currentText())

            self.tbl_sets.setItem(row, 0, dlg_layer)
            self.tbl_sets.setItem(row, 1, dlg_type)
            self.tbl_sets.setItem(row, 2, dlg_format)

        # initially fill input data table with first dataset (default)
        self.insert_input_data(index=0)

    def _fill_dataset_combobox(self):
        # write layer names to dataset combobox in Input Data tab
        self.cmb_set.clear()
        self.cmb_set.addItems([layer.name for layer in self.layers.layer_list])

    def _build_dataset_table_header(self, index):
        # self.layer_list[index].id() gives the QGIS-internal layer ID
        field_0 = self.layers.layer_list[index].field_0
        field_1 = self.layers.layer_list[index].field_1

        # set header of input table
        self.tbl_input.setHorizontalHeaderLabels(["ID", field_0, field_1])

    def _insert_data(self, index):
        # set row count of input data table to length of selected layer
        # first, get the layer list from the Layers class
        # second, access the current index in that list, giving the vector layer
        # finally, get the feature count (QGIS function) from that vector layer
        self.tbl_input.setRowCount(self.layers.layer_list[index].layer.featureCount())
        self.cmb_set.setProperty("layer", self.layers.layer_list[index])  # set layer class as property of dataset combobox

        for row in range(self.tbl_input.rowCount()):
            feature = self.layers.layer_list[index].layer.getFeature(row)

            # set id
            if feature.attributes()[0]:
                fid = feature.attributes()[0]

            else:
                fid = feature.id()

            col_0 = QtWidgets.QTableWidgetItem()
            col_1 = QtWidgets.QTableWidgetItem()
            col_2 = QtWidgets.QTableWidgetItem()

            col_0.setData(Qt.EditRole, fid)
            col_1.setData(Qt.EditRole, feature.attributes()[self.layers.layer_list[index].index_field_0])
            col_2.setData(Qt.EditRole, feature.attributes()[self.layers.layer_list[index].index_field_1])

            self.tbl_input.setItem(row, 0, col_0)
            self.tbl_input.setItem(row, 1, col_1)
            self.tbl_input.setItem(row, 2, col_2)

    def insert_input_data(self, index=None):
        # index is None for any other activity, i.e. apart from initializing
        if index is None:
            # get layer from the combobox
            index = self.cmb_set.currentIndex()

        self._build_dataset_table_header(index)
        self._insert_data(index)
        self.clear_plots()
        # self.create_plot()

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

    def clear_plots(self):
        for i in reversed(range(self.plot_layout.count())):
            self.plot_layout.itemAt(i).widget().setParent(None)

        self.stereonet.cla()

        # adding tool bar to the layout
        self.plot_layout.addWidget(self.toolbar)

        # adding canvas to the layout
        self.plot_layout.addWidget(self.canvas)

    def create_plot(self):
        layer = self.cmb_set.property("layer")  # combobox cmb_set holds the selected layer as property

        if layer.type.lower() == "lines":
            for x, y in self._get_plot_values():
                self.stereonet.line(Lin(x, y))

        elif layer.type.lower() == "planes":
            for x, y in self._get_plot_values():
                self.stereonet.plane(Fol(x, y))

        #self.stereonet.ax.picker = line_picker

        # canvas = FigureCanvas(self.stereonet.fig)
        # self.plot_layout.addWidget(canvas)
        #self.plot_layout.setGeometry()
        print(self.plot_layout.minimumSize())
        print(self.stereonet.fig.get_size_inches())

    def _get_plot_values(self):
        for row in range(self.tbl_input.rowCount()):
            x = self.tbl_input.item(row, 1).data(Qt.EditRole)
            y = self.tbl_input.item(row, 2).data(Qt.EditRole)

            yield x, y


class Layers:
    def __init__(self):
        self.layer_list = []

    def add_layer(self, layer):
        self.layer_list.append(layer)

    def remove_layer(self, layer):
        print(f"BEFORE {self.layer_list}")
        self.layer_list.remove(layer)
        print(f"After {self.layer_list}")


class Layer:
    def __init__(self, layer=None):
        #self.layer = QgsProject.instance().mapLayers()[layer.layer_id]
        self.layer_id = layer.id()
        self.layer = layer
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
