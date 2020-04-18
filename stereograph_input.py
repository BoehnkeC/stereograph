import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSignalMapper
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QWidget
from qgis.core import QgsProject, QgsMapLayerType

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'stereograph_input_gui.ui'))


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
        self.format_entries = {
                            'lines':
                                {
                                'TP':
                                    ('Trend', 'Plunge'),
                                'PQ':
                                    ('Plunge', 'Trend Quadrant'),
                                'LL':
                                    ('Longitude', 'Latitude'),
                                'RK':
                                    ('Unspecified', 'Unspecified')
                                },
                            'planes':
                                {
                                'AD':
                                    ('Strike Azimuth', 'Dip Magnitude'),
                                'AZ':
                                    ('Unspecified', 'Unspecified'),
                                'QD':
                                    ('Quadrant', 'Unspecified'),
                                'DD':
                                    ('Dip Magnitude', 'Dip Azimuth')
                                }
        }

        ## clean up layer list
        ## only keep vector layers
        self.layers = self.clean_up_layers()

        ## define empty list to store format comboboxes
        ## dedicated combobox has to be cleared when clicking on the type combobox from the same row
        self.cmbs_format = []
        self.cmbs_type = []

        ## fill input data dialog
        ## func build comboboxes into table
        self.insert_layers()
        self.fill_comboboxes()

        for j in range(len(self.cmbs_type)):
            self.cmbs_type[j].currentIndexChanged.connect(self.cmb_type_slot)

        for k in range(len(self.cmbs_format)):
            self.cmbs_format[k].currentIndexChanged.connect(self.cmb_format_slot)

    def cmb_format_slot(self, index):
        '''Map custom structure type of record to required format.
        Custom structure type is obtained from the combobox cmb_type.
        The desired format is to be picked from the combobox cmb_format.
        Use corresponding format dictionary, e.g. self.format_lines if processing lines.
        The format ictionaries have the same structure, e.g. self.format_lines:
        {'TP':('Trend', 'Plunge'), 'PQ':('Plunge', 'Trend Quadrant')}.
        '''

        ## get format combobox triggering the signal
        cmb_format = self.sender()

        ## get corresponding type combobox
        ## get current dataset type from type combobox, e.g. lines, planes etc.
        cmb_type = cmb_format.property('type')
        dataset_type = cmb_type.currentText()

        ## get current layer
        ## get field names from current layer
        layer = cmb_format.property('layer')
        field_names = [field.name() for field in layer[1].fields()]

        ## proceed to fill lower GUI labels if a valid dataset type has been selected
        ## check if the current text is a key in the format dictionary
        if cmb_type.currentText().lower() in list(self.format_entries.keys()):
            ## text in format combobox is empty for a short time when indices of type combobox change
            ## set text of lower GUI labels to first entry of the selected dataset type, considered as default selection
            ## hand the proper format sub-dictionary, depending on the dataset type
            ## e.g. if dataset type = lines ==> {'TP':('Trend', 'Plunge'),'PQ':('Plunge', 'Trend Quadrant')} etc.
            ## hand a None key, thus the first entry is picked from the format sub-dictionary
            if len(cmb_format.currentText()) == 0:
                self.label_format_fields(field_names, self.format_entries[dataset_type.lower()], key=None)

            ## valid selection on the type combobox has been made
            ## hand the corresponding format sub dictionary
            ## hand the current text of the format combobox, depicting the key in the format sub-dictionary
            else:
                self.label_format_fields(field_names, self.format_entries[dataset_type.lower()], key=cmb_format.currentText())

    def cmb_type_slot(self, index):
        ## get the type combobox triggering the signal
        ## get the corresponding format combobox
        ## clear the format combobox
        cmb_type = self.sender()
        cmb_format = cmb_type.property('format')
        cmb_format.clear()

        ## if a valid selection on the type combobox has been made, fill the format combobox
        ## check if the current text is a key in the format dictionary
        if cmb_type.currentText().lower() in list(self.format_entries.keys()):
            ## get the current dataset type from type combobox, e.g. lines, planes etc.
            ## get the corresponding sub-dictionary
            ## key is dataset type
            dataset_type = cmb_type.currentText()
            format_dict = self.format_entries[dataset_type.lower()]

            ## fill the format combobox with the keys of the sub-dictionary
            cmb_format.addItems(list(format_dict.keys()))

        ## no valid selection on the type combobox
        ## fill the format combobox with a dummy text
        else:
            cmb_format.addItem('Please select dataset type')

    def fill_comboboxes(self):
        for i in range(len(self.cmbs_type)):
            self.cmbs_type[i].addItems(['',
                            'Lines',
                            'Planes',
                            'Lines on Planes (Rake)',
                            'Small Circles',
                            'Arcs'])

            self.cmbs_format[i].addItem('Please select dataset type')

    def clean_up_layers(self):
        layer_dict = {}

        ## loop over layers
        for id, layer in enumerate(self.layers.items()):
            ## only keep vector layers
            if layer[1].type() == QgsMapLayerType.VectorLayer:
                layer_dict[layer[0]] = layer[1]

        return layer_dict

    def insert_layers(self):
        ## set row count of input data table to length of QGIS layer TOC
        self.tbl_layers.setRowCount(len(self.layers.items()))

        ## insert layer into table
        for id, layer in enumerate(self.layers.items()):
            ## get layer name
            ## 1st table column equals layer name
            layer_input = QTableWidgetItem(layer[1].name())
            self.tbl_layers.setItem(id, 0, layer_input)

            ## get type field
            ## add structure type to type combobox
            ## type announces the type of the structural record
            cmb_type = QComboBox()

            ## set the row of the table where the combobox was clicked
            ## add type combobox to table
            cmb_type.setProperty('row', id)
            self.tbl_layers.setCellWidget(id, 1, cmb_type)

            ## add format combobox to table
            cmb_format = QComboBox()
            self.tbl_layers.setCellWidget(id, 2, cmb_format)

            cmb_type.setProperty('format', cmb_format)
            cmb_type.setProperty('layer', layer)
            cmb_format.setProperty('layer', layer)
            cmb_format.setProperty('type', cmb_type)

            ## append the combobox to the combobox table
            self.cmbs_format.append(cmb_format)
            self.cmbs_type.append(cmb_type)

    def label_format_fields(self, field_names, format_dict, key=None):
        '''
        Entry in the format combobox has been clicked.
        Adjust the format field labels to the corresponding format entry.
        E.g. when processing on lines, entry 'LL' clicked, labels are 'Longitude' & 'Latitude'.
        If index in type combobox changed, adjust the labels to default values.
        '''

        if not key:
            ## labels have to be filled with default values from the format dictionary
            ## get a list of keys from the format dictionary
            ## pick the first key, e.g. 'TP' if processing lines
            key = list(format_dict.keys())[0]

        self.lbl_format_0.setText(format_dict[key][0])
        self.lbl_format_1.setText(format_dict[key][1])

        self.cmb_format_0.addItems(field_names)
        self.cmb_format_1.addItems(field_names)
