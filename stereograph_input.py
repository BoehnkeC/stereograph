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

        # define empty list to store format comboboxes
        # dedicated combobox has to be cleared when clicking on the type combobox from the same row
        self.cmbs_format = []
        self.cmbs_type = []
        self.cmbs_field = [self.cmb_field_0, self.cmb_field_1]

        # fill input data dialog
        self.insert_layers()
        self.fill_comboboxes()

        # set width of format field selection to width of 1st table column
        self.txt_layers.setFixedWidth(self.tbl_layers.columnWidth(0))

        for j in range(len(self.cmbs_type)):
            self.cmbs_type[j].currentIndexChanged.connect(self.cmb_type_slot)

        for k in range(len(self.cmbs_format)):
            self.cmbs_format[k].currentIndexChanged.connect(self.cmb_format_slot)

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
        for key in self.layers.keys():
            if self.tbl_layers.currentRow() == self.layers[key]["properties"]["row"]:
                self.layers[key]["properties"][
                    "index_field_0"
                ] = self.cmb_field_0.currentIndex()

    def cmb_field_1_slot(self):
        """
        Index of the first field combobox changed. Process on signal.
        """

        # loop over layers
        # find layer matching the current row
        for key in self.layers.keys():
            if self.tbl_layers.currentRow() == self.layers[key]["properties"]["row"]:
                self.layers[key]["properties"][
                    "index_field_1"
                ] = self.cmb_field_1.currentIndex()

    def txt_layer_slot(self, row, column):
        """
        Cell in table has been clicked. Process on signal.

        :param row: The row of the clicked cell.
        :param column: The column of the clicked cell.
        """

        if column == 0:
            # get the item at the clicked table coordinates
            item = self.tbl_layers.item(row, column)

            # write layer name to format field selection
            self.txt_layers.setText(item.text())

            # fill format fields with information from dictionary
            # loop over layer dictionary keys
            for key in self.layers.keys():
                # check if row of layer equals clicked table row
                if self.layers[key]["properties"]["row"] == row:
                    # get indices in field comboboxes from dictionary
                    # indices must be retrieved before resupplying the comboboxes with the field names
                    # otherwise the index would change again and
                    # the default index of 0 would be written to the dictionary
                    index_field_0 = self.layers[key]["properties"]["index_field_0"]
                    index_field_1 = self.layers[key]["properties"]["index_field_1"]

                    # get the current layer and its field names
                    layer = QgsProject.instance().mapLayers()[key]
                    field_names = [field.name() for field in layer.fields()]

                    # get type and format indices of current layer from dictionary
                    index_type = self.layers[key]["properties"]["index_type"]
                    index_format = self.layers[key]["properties"]["index_format"]

                    # set format and field comboboxes to current indices
                    # retrieve type and format text
                    self.cmbs_type[row].setCurrentIndex(index_type)
                    self.cmbs_format[row].setCurrentIndex(index_format)
                    dataset_type = self.cmbs_type[row].currentText()
                    dataset_format = self.cmbs_format[row].currentText()

                    # label the format fields according to the dictionary entries
                    # supply the field comboboxes with the field names of the current layer
                    self.label_format_fields(
                        self.format_entries[dataset_type.lower()], key=dataset_format
                    )
                    self.fill_field_comboboxes(field_names)

                    # set the index in the field comboboxes to the desired indices from the dictionary
                    # this step must be performed at the end
                    # otherwise the index would be set to 0 by default
                    self.cmb_field_0.setCurrentIndex(index_field_0)
                    self.cmb_field_1.setCurrentIndex(index_field_1)

    def cmb_format_slot(self, index):
        """Map custom structure type of record to required format.
        Custom structure type is obtained from the combobox cmb_type.
        The desired format is to be picked from the combobox cmb_format.
        Use corresponding format dictionary at the proper key, e.g. Lines when processing on lines.
        E.g. 'Lines':{'TP':('Trend', 'Plunge'), 'PQ':('Plunge', 'Trend Quadrant')}.

        :param index: Current index of the format combobox.
        """

        # get format combobox triggering the signal
        cmb_format = self.sender()

        # get corresponding type combobox
        # get current dataset type from type combobox, e.g. lines, planes etc.
        # get the corresponding sub-dictionary
        # key is dataset type
        cmb_type = cmb_format.property("type")
        dataset_type = cmb_type.currentText()

        # get current layer
        # get field names from current layer
        key = cmb_format.property("layer_id")
        layer = QgsProject.instance().mapLayers()[key]
        field_names = [field.name() for field in layer.fields()]

        # proceed to fill lower GUI labels if a valid dataset type has been selected
        # check if the current text is a key in the format dictionary
        if cmb_type.currentText().lower() in list(self.format_entries.keys()):
            # text in format combobox is empty for a short time when indices of type combobox change
            # set text of lower GUI labels to first entry of the selected dataset type, considered as default selection
            # hand the proper format sub-dictionary, depending on the dataset type
            # e.g. if dataset type = lines ==> {'TP':('Trend', 'Plunge'),'PQ':('Plunge', 'Trend Quadrant')} etc.
            # hand a None key, thus the first entry is picked from the format sub-dictionary
            if len(cmb_format.currentText()) == 0:
                # set the labels of the format fields to the selected format
                self.label_format_fields(
                    self.format_entries[dataset_type.lower()], key=None
                )
                self.fill_field_comboboxes(field_names)

                # no selection, no label
                # write index = 0 to the layer dictionary
                self.layers[key]["properties"]["index_format"] = 0

            # valid selection on the type combobox has been made
            # hand the corresponding format sub dictionary
            # hand the current text of the format combobox, depicting the key in the format sub-dictionary
            else:
                format_dict = self.format_entries[dataset_type.lower()]

                # write the index from the format combobox to the layer dictionary
                self.label_format_fields(
                    self.format_entries[dataset_type.lower()],
                    key=cmb_format.currentText(),
                )
                self.fill_field_comboboxes(field_names)

                # write the index from the format combobox to the layer dictionary
                self.layers[key]["properties"]["index_format"] = index

                # write format entry to layer dictionary
                # convert the keys of the format dictionary keys into a list
                # get the proper key at the specified index
                self.layers[key]["properties"]["field_0"] = format_dict[
                    list(format_dict.keys())[index]
                ][0]
                self.layers[key]["properties"]["field_1"] = format_dict[
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
        cmb_type = self.sender()
        cmb_format = cmb_type.property("format")
        cmb_format.clear()

        # get corresponding layer by its layer ID
        # write row of corresponding layer to layer dictionary
        key = cmb_type.property("layer_id")

        # if a valid selection on the type combobox has been made, fill the format combobox
        # check if the current text is a key in the format dictionary
        if cmb_type.currentText().lower() in list(self.format_entries.keys()):
            # get the current dataset type from type combobox, e.g. lines, planes etc.
            # get the corresponding sub-dictionary
            # key is dataset type
            dataset_type = cmb_type.currentText()
            format_dict = self.format_entries[dataset_type.lower()]

            # fill the format combobox with the keys of the sub-dictionary
            cmb_format.addItems(list(format_dict.keys()))

            # write layer name to format field selection
            self.txt_layers.setText(self.layers[key]["name"])

            # write the index from the type combobox to the layer dictionary
            self.layers[key]["properties"]["index_type"] = index

            # write format entry to layer dictionary
            # convert the keys of the format dictionary keys into a list
            # get the proper key at the specified index
            self.layers[key]["properties"]["field_0"] = format_dict[
                list(format_dict.keys())[index-1]
            ][0]
            self.layers[key]["properties"]["field_1"] = format_dict[
                list(format_dict.keys())[index-1]
            ][1]

        # no valid selection on the type combobox
        # fill the format combobox with a dummy text
        else:
            cmb_format.addItem("Please select dataset type")

            # no selection, no index
            # write index = 0 to the layer dictionary
            self.layers[key]["properties"]["index_type"] = 0

            self.label_format_fields(
                self.default_labels
            )

            self.layers[key]["properties"]["field_1"] = None
            self.layers[key]["properties"]["field_2"] = None

    def fill_comboboxes(self):
        """
        Fill the comboboxes with default values.
        """

        for i in range(len(self.cmbs_type)):
            self.cmbs_type[i].addItems(
                [
                    "",
                    "Lines",
                    "Planes",
                    "Lines on Planes (Rake)",
                    "Small Circles",
                    "Arcs",
                ]
            )

            self.cmbs_format[i].addItem("Please select dataset type")

        # when comboboxes are filled, also write a dummy index = 0 to layer dictionary
        for key in self.layers.keys():
            self.layers[key]["properties"]["index_type"] = 0
            self.layers[key]["properties"]["index_format"] = 0

    def insert_layers(self):
        """
        Insert all accepted vector layers from the QGIS layer TOC into the table.
        """

        # set row count of input data table to length of QGIS layer TOC
        self.tbl_layers.setRowCount(len(self.layers.items()))

        # insert layer into table
        for index, key in enumerate(self.layers.keys()):
            layer = self.layers[key]

            # get layer name
            # 1st table column equals layer name
            layer_input = QTableWidgetItem(layer["name"])
            self.tbl_layers.setItem(index, 0, layer_input)

            # get type field
            # add structure type to type combobox
            # type announces the type of the structural record
            cmb_type = QComboBox()

            # set the row of the table where the combobox was clicked
            # write row to layer dictionary
            # add type combobox to table
            cmb_type.setProperty("row", index)
            self.layers[key]["properties"]["row"] = index
            self.tbl_layers.setCellWidget(index, 1, cmb_type)

            # add format combobox to table
            cmb_format = QComboBox()
            self.tbl_layers.setCellWidget(index, 2, cmb_format)

            cmb_type.setProperty("format", cmb_format)
            cmb_type.setProperty("layer_id", key)
            cmb_format.setProperty("layer_id", key)
            cmb_format.setProperty("type", cmb_type)

            # append the combobox to the combobox table
            self.cmbs_format.append(cmb_format)
            self.cmbs_type.append(cmb_type)

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
