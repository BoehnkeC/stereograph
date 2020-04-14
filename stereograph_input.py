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

    def clean_up_layers(self):
        layer_dict = {}

        for id, layer in enumerate(self.layers.items()):
            if layer[1].type() == QgsMapLayerType.VectorLayer:
                layer_dict[layer[0]] = layer[1]

        return layer_dict

    def insert_layers(self):
        ## set row count of input data table to length of QGIS layer TOC
        self.tbl_layers.setRowCount(len(self.layers.items()))

        ## define empty list to store format comboboxes
        ## dedicated combobox has to be cleared when clicking on the type combobox from the same row
        cmbs_format = []

        ## insert layer into table
        for id, layer in enumerate(self.layers.items()):
            #field_names = [field.name() for field in layer[1].fields()]

            ## get layer name
            layer_input = QTableWidgetItem(layer[1].name())
            self.tbl_layers.setItem(id, 0, layer_input)

            ## name, type & format required

            ## get type field
            ## type announces the type of the structural record
            cmb_type = QComboBox()
            cmb_type.addItems(['',
                            'Lines',
                            'Planes',
                            'Lines on Planes (Rake)',
                            'Small Circles',
                            'Arcs'])
            cmb_type.setProperty('row', id)
            self.tbl_layers.setCellWidget(id, 1, cmb_type)

            ## map user cutsom type to required format
            cmb_format = QComboBox()
            cmb_format.addItem('Please select dataset type')
            self.tbl_layers.setCellWidget(id, 2, cmb_format)

            ## append the combobox to the combobox table
            cmbs_format.append(cmb_format)

            ## entry in the combobox clicked
            ## map to the structure type
            ## hand the list of comboboxes to work on the combobox from the current row
            cmb_type.currentIndexChanged.connect(lambda: self.slot_type(cmbs_format))

    def slot_type(self, cmbs_format):
        '''Process a click on the structure type combobox.
        '''
        ## get combobox triggering the signal
        ## get the row of the table where the combobox was clicked
        cmb_type = self.sender()
        row = cmb_type.property('row')

        ## get clicked index from combobox
        index = cmb_type.currentIndex()

        ## clear format combobox and overwrite
        cmbs_format[row].clear()

        ## map custom structure type of record to required format
        self.get_format(cmb_type, cmbs_format[row])

    def get_format(self, cmb_type, cmb_format):
        '''Map custom structure type of record to required format.
        '''
        format_lines = ['TP', 'PT', 'PQ', 'LL', 'RK']
        format_planes = ['AD', 'AZ', 'QD', 'DD']

        ## get current structure type
        dataset_type = cmb_type.currentText()

        if dataset_type == 'Lines':
            cmb_format.addItems(format_lines)
        elif dataset_type == 'Planes':
            cmb_format.addItems(format_planes)
        else:
            cmb_format.addItem('Please select dataset type')
