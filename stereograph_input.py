import os

from qgis.PyQt import QtGui, QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QSignalMapper
from PyQt5.QtWidgets import QTableWidgetItem, QComboBox
from PyQt5.QtGui import QIcon
from qgis.core import QgsProject, QgsMapLayerType

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "stereograph_input_gui.ui")
)


class StereoGraphInputWidget(QtWidgets.QDialog, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, layers, parent=None):
        """Constructor."""
        super(StereoGraphInputWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.type_entries = {
            'dummy': "",
            'lines': "Lines",
            'planes': "Planes",
            'rake': "Lines on Planes (Rake)",  # abweichung vom einfallen der fläche gemessen am linear
            'circles': "Small Circles",
            'arcs': "Arcs",
        }

        self.format_entries = {
            "lines": {
                "TP": ("Trend", "Plunge"),
                "PQ": ("Plunge", "Trend Quadrant"),
                "LL": ("Longitude", "Latitude"),
                "RK": ("Unspecified", "Unspecified"),
            },
            "planes": {
                "AD": ("Strike Azimuth", "Dip Magnitude"),
                "AZ": ("Unspecified", "Unspecified"),
                "QD": ("Quadrant", "Unspecified"),
                "DD": ("Dip Magnitude", "Dip Azimuth"),
            },
        }

        self.layers = layers
        self.default_labels = {
            "key": (self.lbl_format_0.text(), self.lbl_format_1.text())
        }

        # fill input data dialog
        self.insert_layers()
        self.fill_comboboxes()

        # set width of format field selection to width of 1st table column
        self.txt_layers.setFixedWidth(self.tbl_layers.columnWidth(0))

        for layer in self.layers.layer_list:  # loop over type combobox
            layer.cmb_type.combobox.activated.connect(self.cmb_type_slot)  # check if item in combobox was clicked
            layer.cmb_format.combobox.activated.connect(self.cmb_format_slot)  # check if item in combobox was clicked

        self.cmb_field_0.currentIndexChanged.connect(self.cmb_field_0_slot)
        self.cmb_field_1.currentIndexChanged.connect(self.cmb_field_1_slot)

        # get the table coordinates of the clicked cell
        self.tbl_layers.cellClicked.connect(self.txt_layer_slot)

    def cmb_field_0_slot(self):
        """
        Index of the first field combobox changed. Process on signal.
        """

        # loop over layers
        # find layer matching the current row
        for layer in self.layers.layer_list:
            if self.tbl_layers.currentRow() == layer.row:
                layer.index_field_0 = self.cmb_field_0.currentIndex()

    def cmb_field_1_slot(self):
        """
        Index of the first field combobox changed. Process on signal.
        """

        # loop over layers
        # find layer matching the current row
        for layer in self.layers.layer_list:
            if self.tbl_layers.currentRow() == layer.row:
                layer.index_field_1 = self.cmb_field_1.currentIndex()

    def txt_layer_slot(self, row, column):
        """
        Cell in table has been clicked. Process on signal.

        :param row: The row of the clicked cell.
        :param column: The column of the clicked cell.
        """
        print(f"COLUMN {column}")
        if column == 0:
            # get the item at the clicked table coordinates
            item = self.tbl_layers.item(row, column)

            # write layer name to format field selection
            self.txt_layers.setText(item.text())

            # fill format fields with information from dictionary
            # loop over layer dictionary keys
            for layer in self.layers.layer_list:
                # check if row of layer equals clicked table row
                if layer.row == row:
                    # get the current layer and its field names
                    vlayer = QgsProject.instance().mapLayers()[layer.layer_id]
                    field_names = [field.name() for field in vlayer.fields()]

                    # label the format fields according to the dictionary entries
                    # supply the field comboboxes with the field names of the current layer
                    self.label_format_fields(
                        self.format_entries[layer.cmb_type.dataset.lower()], 
                        key=layer.cmb_format.dataset
                    )
                    self.fill_field_comboboxes(field_names)

                    # set the index in the field comboboxes to the desired indices from the dictionary
                    # this step must be performed at the end
                    # otherwise the index would be set to 0 by default
                    self.cmb_field_0.setCurrentIndex(layer.index_field_0)
                    self.cmb_field_1.setCurrentIndex(layer.index_field_1)

    def cmb_format_slot(self, index):
        """Map custom structure type of record to required format.
        Custom structure type is obtained from the combobox cmb_type.
        The desired format is to be picked from the combobox cmb_format.
        Use corresponding format dictionary at the proper key, e.g. Lines when processing on lines.
        E.g. 'Lines':{'TP':('Trend', 'Plunge'), 'PQ':('Plunge', 'Trend Quadrant')}.

        :param index: Current index of the format combobox.
        """

        # get format combobox triggering the signal
        layer = self.layers.layer_list[index-1]

        # get current layer
        # get field names from current layer
        layer.cmb_format.dataset = layer.cmb_format.combobox.currentText()
        vlayer = QgsProject.instance().mapLayers()[layer.layer_id]
        field_names = [field.name() for field in vlayer.fields()]

        # proceed to fill lower GUI labels if a valid dataset type has been selected
        # check if the current text is a key in the format dictionary
        if layer.cmb_format.dataset.lower() in list(self.format_entries.keys()):
            # text in format combobox is empty for a short time when indices of type combobox change
            # set text of lower GUI labels to first entry of the selected dataset type, considered as default selection
            # hand the proper format sub-dictionary, depending on the dataset type
            # e.g. if dataset type = lines ==> {'TP':('Trend', 'Plunge'),'PQ':('Plunge', 'Trend Quadrant')} etc.
            # hand a None key, thus the first entry is picked from the format sub-dictionary
            if len(layer.cmb_format.dataset.currentText()) == 0:
                # set the labels of the format fields to the selected format
                self.label_format_fields(
                    self.format_entries[layer.cmb_type.dataset.lower()], key=None
                )
                self.fill_field_comboboxes(field_names)

                # no selection, no label
                # write index = 0 to the layer dictionary
                layer.cmb_format.index = 0

            # valid selection on the type combobox has been made
            # hand the corresponding format sub dictionary
            # hand the current text of the format combobox, depicting the key in the format sub-dictionary
            else:
                format_dict = self.format_entries[layer.cmb_type.dataset.lower()]

                # write the index from the format combobox to the layer dictionary
                self.label_format_fields(
                    self.format_entries[layer.cmb_type.dataset.lower()],
                    key=layer.cmb_format.combobox.currentText(),
                )
                self.fill_field_comboboxes(field_names)

                # write the index from the format combobox to the layer dictionary
                layer.cmb_format.index = index

                # write format entry to layer dictionary
                # convert the keys of the format dictionary keys into a list
                # get the proper key at the specified index
                layer.field_0 = format_dict[
                    list(format_dict.keys())[index]
                ][0]
                layer.field_1 = format_dict[
                    list(format_dict.keys())[index]
                ][1]

    def cmb_type_slot(self, index):
        """
        Set the custom structure type for the current layer, e.g. lines, planes etc.

        :param index: Current index of the type combobox.
        """

        # get the type combobox triggering the signal
        # get the corresponding format combobox
        # clear the format combobox

        layer = self.layers.layer_list[index-1]
        layer.cmb_format.combobox.clear()

        layer.cmb_type.dataset = layer.cmb_type.combobox.currentText()

        # if a valid selection on the type combobox has been made, fill the format combobox
        # check if the current text is a key in the format dictionary
        if layer.cmb_type.dataset.lower() in list(self.format_entries.keys()):
            # get the current dataset type from type combobox, e.g. lines, planes etc.
            # key is dataset type
            format_dict = self.format_entries[layer.cmb_type.dataset.lower()]

            # fill the format object
            layer.cmb_format.combobox.addItems(list(format_dict.keys()))
            layer.cmb_format.index = 0
            layer.cmb_format.combobox.setCurrentIndex(layer.cmb_format.index)
            layer.cmb_format.combobox.setCurrentText(list(format_dict.keys())[layer.cmb_format.index])
            layer.cmb_format.dataset = layer.cmb_format.combobox.currentText()

            # write layer name to format field selection
            self.txt_layers.setText(layer.name)

            # write format entry to layer dictionary
            # convert the keys of the format dictionary keys into a list
            # get the proper key at the specified index
            layer.field_0 = format_dict[
                list(format_dict.keys())[layer.cmb_type.index-1]
            ][0]
            layer.field_1 = format_dict[
                list(format_dict.keys())[layer.cmb_type.index-1]
            ][1]

        # no valid selection on the type combobox
        # fill the format combobox with a dummy text
        else:
            layer.cmb_format.combobox.addItem("Please select dataset type")

            # no selection, no index
            # write index = 0 to the layer dictionary
            self.layers.layer_list[layer.row].cmb_type.index = 0

            self.label_format_fields(
                self.default_labels
            )

            self.layers.layer_list[layer.row].field_0 = None
            self.layers.layer_list[layer.row].field_1 = None

    def fill_comboboxes(self):
        """
        Fill the comboboxes with default values.
        """

        # when comboboxes are filled, also write a dummy index = 0 to layer dictionary
        for layer in self.layers.layer_list:
            # add text to the type comboboxes
            layer.cmb_type.combobox.addItems(list(self.type_entries.values()))

            # layer already has a type selected, assign selection to combobox
            # in this case the type index in the layer dictionary exceeds 0
            if layer.cmb_type.index > 0:
                # set index of combobox to index from layer dictionary
                layer.cmb_type.combobox.setCurrentIndex(layer.cmb_type.index)

            else:
                # layer has no type selected yet
                # fill comboboxes with default values
                layer.cmb_type.index = 0
                layer.cmb_format.index = 0
                layer.cmb_format.combobox.addItem("Please select dataset type")
                
            layer.cmb_type.dataset = layer.cmb_type.combobox.currentText()
            layer.cmb_format.dataset = layer.cmb_format.combobox.currentText()

    def insert_layers(self):
        """
        Insert all accepted vector layers from the QGIS layer TOC into the table.
        """

        # set row count of input data table to length of QGIS layer TOC
        self.tbl_layers.setRowCount(len(self.layers.layer_list))

        # insert layer into table
        # layer equals the layer ID
        # index equals the location in the dictionary and is used as line number
        for index, layer in enumerate(self.layers.layer_list):
            layer.row = index
            # get layer name
            # 1st table column equals layer name
            layer_input = QTableWidgetItem(layer.name)
            self.tbl_layers.setItem(index, 0, layer_input)

            # declare the comboboxes
            layer.cmb_type = ComboboxFormat()
            layer.cmb_format = ComboboxFormat()

            # set the row of the table where the combobox was clicked
            # add type combobox to table
            self.tbl_layers.setCellWidget(index, 1, layer.cmb_type.combobox)  # put combobox to table
            self.tbl_layers.cellWidget(index, 1).setCurrentIndex(layer.cmb_type.index)  # set index in combobox to 0

            # add format combobox to table
            self.tbl_layers.setCellWidget(index, 2, layer.cmb_format.combobox)  # put combobox to table
            self.tbl_layers.cellWidget(index, 2).setCurrentIndex(layer.cmb_format.index)

    def label_format_fields(self, format_dict, key=None):
        """
        Entry in the format combobox has been clicked.
        Adjust the format field labels to the corresponding format entry.
        E.g. when processing on lines, entry 'LL' clicked, labels are 'Longitude' & 'Latitude'.
        If index in type combobox changed, adjust the labels to default values.

        :param format_dict: Dictionary containing the available formats per structure,
        e.g. 'TP':('Trend', 'Plunge') etc. for lines
        :param key: Key of format dictionary, e.g. 'TP' for lines.
        """

        if not key:
            # labels have to be filled with default values from the format dictionary
            # get a list of keys from the format dictionary
            # pick the first key, e.g. 'TP' if processing lines
            key = list(format_dict.keys())[0]

        self.lbl_format_0.setText(format_dict[key][0])
        self.lbl_format_1.setText(format_dict[key][1])

    def fill_field_comboboxes(self, field_names):
        """
        Fill field comboboxes with the handed field names of the current layer.

        :param field_names: List of field names of the current layer.
        """
        self.cmb_field_0.clear()
        self.cmb_field_1.clear()

        self.cmb_field_0.addItems(field_names)
        self.cmb_field_1.addItems(field_names)

        
class ComboboxType:
    def __init__(self):
        self.combobox = QComboBox()
        self.index = 0
        self.dataset = None
        
        
class ComboboxFormat:
    def __init__(self):
        self.combobox = QComboBox()
        self.index = 0
        self.dataset = None
