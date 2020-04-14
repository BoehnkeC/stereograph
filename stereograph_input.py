import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox
from qgis.core import QgsProject, QgsMapLayerType

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'stereograph_input_test.ui'))


class StereoGraphInputWidget(QtWidgets.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(StereoGraphInputWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        ## ---------------------------------------------------------
        ## define crucial instances
        ## ---------------------------------------------------------
        self.layers = QgsProject.instance().mapLayers()

        ## clean up layer list
        ## only keep vector layers
        self.layers = self.clean_up_layers()

        ## fill input data dialog
        self.insert_layers()

        ## ---------------------------------------------------------
        ## signals & slots
        ## ---------------------------------------------------------
        #for cmb_type, cmb_format in zip(self.cmbs_type, self.cmbs_format):
        #    cmb_type.currentIndexChanged.connect(lambda: self.get_type(cmb_type, cmb_format))

    def clean_up_layers(self):
        layer_dict = {}

        for id, layer in enumerate(self.layers.items()):
            if layer[1].type() == QgsMapLayerType.VectorLayer:
                layer_dict[layer[0]] = layer[1]

        return layer_dict

    def insert_layers(self):
        ## set row count of input data table to length of QGIS layer TOC
        self.tbl_layers.setRowCount(len(self.layers.items()))

        ## insert layer into table
        for id, layer in enumerate(self.layers.items()):
            #field_names = [field.name() for field in layer[1].fields()]

            ## get layer name
            layer_input = QTableWidgetItem(layer[1].name())
            self.tbl_layers.setItem(id, 0, layer_input)

            ## name, type & format required

            ## get type field
            ## type announces the type of the structural record


            #self.cmb_type.addItems(field_names)
            self.cmbs_type = []
            cmb_type = QComboBox()
            cmb_type.addItems(['',
                                    'Lines',
                                    'Planes',
                                    'Lines on Planes (Rake)',
                                    'Small Circles',
                                    'Arcs'])

            self.tbl_layers.setCellWidget(id, 1, cmb_type)
            self.cmbs_type.append(cmb_type)

            ## map user cutsom type to required format
            self.cmbs_format = []
            cmb_format = QComboBox()
            cmb_format.addItem('Please select dataset type')
            self.tbl_layers.setCellWidget(id, 2, cmb_format)
            self.cmbs_format.append(cmb_format)

            cmb_type.currentIndexChanged.connect(lambda: self.get_type(cmb_type, cmb_format))

    def get_type(self, cmb_type, cmb_format):
        '''Map custom structure type of record to required format.
        '''
        ## get current structure type
        ## clear format combobox and overwrite
        dataset_type = cmb_type.currentText()
        print(dataset_type)
        cmb_format.clear()

        format_lines = ['TP', 'PT', 'PQ', 'LL', 'RK']
        format_planes = ['AD', 'AZ', 'QD', 'DD']
