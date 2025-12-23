from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QFormLayout, QComboBox, QPushButton, QLabel, QCheckBox, QLineEdit, QApplication)
from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtCore import Qt, QRegularExpression

def getLayerNames(layerType):
    """ 
    Funkcja pobiera nazwy dostępnych warstw wektorowych w projekcie o wybranej geometrii (np. linie, poligony) 
    
    :param layerType: QgsWkbTypes typ geometrii warstwy QgsMapLayer.
    :return: Lista nazw warstw spełniających o typie layerType.
    """
    layers = []
    for layer in QgsProject.instance().mapLayers().values():
        type = layerType
        if layer.type() == QgsMapLayer.VectorLayer:
            if layer.geometryType() == type:
                layers.append(layer.name())
    return layers

def split_lines(input_layer, lines_layer, splitOnlySelected=True):
    """ 
    Funkcja dzieli input_layer (wartstwa przekrojów) na odcinki. 
    Przecięcia są wykonywane w miejscach intersekcji z krańcami poligonów warstwy lines_layer (warstwa warunków geotechnicznych).
    Tworzy warstwę tymczasową 'warunki_split'

    :param input_layer: Nazwa warstwy wektorowej z obiektami w postaci linii z liniami przekrojów.
    :param lines_layer: Nazwa warstwy wektorowej z obiektami w postaci poligonów z warunkami geotechnicznymi.
    :param splitOnlySelected: True/False określa czy podzielone mają być tylko obecnie zaznaczone przekroje.
    :return: Jeżeli splitOnlySelected to True, a żadne przekroje nie są zaznaczone to zwraca 0.
    """
    przekroje_layer = QgsProject.instance().mapLayersByName(input_layer)[0]
    warunki_layer = QgsProject.instance().mapLayersByName(lines_layer)[0]

    if not splitOnlySelected:
        przekroje_layer.selectAll()
    
    selected_features = przekroje_layer.selectedFeatures()
    
    if splitOnlySelected and len(selected_features) == 0:
        print("Nie zaznaczono przekrojów do eksportu.")
        return 0
    
    print(f"Liczba wybranych przekrojów: {len(selected_features)}")
    
    selected_layer = processing.run("native:saveselectedfeatures", {
        'INPUT': przekroje_layer,
        'OUTPUT': 'memory:'
    })['OUTPUT']
    
    result = processing.run("native:splitwithlines", {
        'INPUT': selected_layer,
        'LINES': warunki_layer,
        'OUTPUT': 'memory:Split_Result'
    })

    split_layer = result['OUTPUT']
    split_layer.setName('warunki_split')
    QgsProject.instance().addMapLayer(split_layer)
    
    print(f"Rozdzielono linie przerojów na warstwie '{input_layer}' za pomocą '{lines_layer}'.")
    print(f"Liczba otrzymanych fragmentów: {split_layer.featureCount()}")

    if not splitOnlySelected:
        przekroje_layer.removeSelection()

def connect_layers(input_layer, join_layer):
    """
    Funkcja łączy input_layer (podzieloną warstwę z liniami przekrojów) i join_layer (warstwę z warstwami geotechnicznymi) na podstawie lokalizacji.
    Wybiera atrybuty obiektu z największym nakładaniem się i łączy je w relacji jeden do jednego.
    Tworzy warstwę tymczasową 'przekroje_warunki_polaczone'.
    
    :param input_layer: Nazwa warstwy wektorowej z obiektami w postaci linii z liniami przekrojów podzielonymi według join_layer.
    :param join_layer: Nazwa warstwy wektorowej z obiektami w postaci poligonów z warunkami geotechnicznymi.
    """
    przekroje_layer = QgsProject.instance().mapLayersByName(input_layer)[0]
    warunki_layer = QgsProject.instance().mapLayersByName(join_layer)[0]

    result = processing.run("native:joinattributesbylocation", {
        'INPUT':przekroje_layer,
        'PREDICATE':[0],
        'JOIN':warunki_layer,
        'JOIN_FIELDS':[],
        'METHOD':2,
        'DISCARD_NONMATCHING':False,
        'PREFIX':'',
        'OUTPUT':'memory:Combine_Result'
        })
    
    combined_layer = result['OUTPUT']
    combined_layer.setName('przekroje_warunki_polaczone')
    QgsProject.instance().addMapLayer(combined_layer)

    print(f"Połączono warstwy '{input_layer}' i '{join_layer}'.")

def add_length_field(input_layer, field_name='length'):
    """
    Funkcja oblicza długości linii w input_layer, a następnie dodaje kolumnę z obliczonymi długościami w liczbie całkowitej o nazwie field_name.
    Tworzy warstwę tymczasową 'input_later_with_length'.

    :param input_layer: Nazwa warstwy wektorowej z obiektami w postaci linii z liniami przekrojów.
    :param field_name: Nazwa kolumny z długościami, którą tworzy funkcja.
    """
    layer = QgsProject.instance().mapLayersByName(input_layer)[0]
    
    result = processing.run("qgis:fieldcalculator", {
        'INPUT': layer,
        'FIELD_NAME': field_name,
        'FIELD_TYPE': 1, # int
        'FIELD_LENGTH': 10,
        'FIELD_PRECISION': 3,
        'FORMULA': '$length',
        'OUTPUT': 'memory:with_length'
    })
    
    output_layer = result['OUTPUT']
    output_layer.setName(f'{input_layer}_with_length')
    QgsProject.instance().addMapLayer(output_layer)
    
    print(f"Dodano pole z długościami linii do '{input_layer}'")

def export_layer_to_csv(input_layer, output_path = "przekroje_z_warunkami_geotechnicznymi.csv"):
    """
    Funkcja eksportuje atrybuty warstwy o nazwie input_layer do pliku csv do nazwie output_path.
    
    :param input_layer: Nazwa warstwy do eksportu.
    :param output_path: Nazwa pod jaką ma być zapisany wyeksportowany plik.
    """
    layer = QgsProject.instance().mapLayersByName(input_layer)[0]
    
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = "CSV"
    save_options.fileEncoding = "UTF-8"
    
    error = QgsVectorFileWriter.writeAsVectorFormatV3(
        layer,
        output_path,
        QgsProject.instance().transformContext(),
        save_options
    )
    
    if error[0] == QgsVectorFileWriter.NoError:
        print(f"Warstwa '{input_layer}' wyeksportowana do: {output_path}")
    else:
        print(f"Error exporting layer: {error}")

def remove_created_memory_layers():
    """
    Funkcja usuwa wszytskie tymczasowe warstwy w projekcie.
    """
    project = QgsProject.instance()
    layers_to_remove = ['warunki_split', 'warunki_split_with_length', 'przekroje_warunki_polaczone']
    
    for layer in project.mapLayers().values():
        if (layer.name() in layers_to_remove) and (layer.dataProvider().name() == 'memory'):
            project.removeMapLayer(layer.id())
    
    print(f"Usunięto tymczasowe warstwy")

def getFieldNames(input_layer):
    """
    Funkcja pobiera nazwy kolumn (pól) warstwy o nazwie input_layer.
    
    :param input_layer: Nazwa warstwy wektorowej w projekcie Qgis.
    :return: Lista nazw kolumn (pól) warstwy.
    """
    layer = QgsProject.instance().mapLayersByName(input_layer)[0]
    field_names = layer.fields().names()
    return field_names

class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tworzenie warstwy linii przekrojów z warstwami geotechnicznymi")

        self.setGeometry(500, 100, 600, 300)

        self.UiComponents()

        self.show()

    def UiComponents(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignTop)

        form_layout = QFormLayout()

        # Połącz warstwy
        self.submit_button = QPushButton("Połącz")
        self.submit_button.clicked.connect(self.on_submit)

        # Warstwy przekrojów
        self.combo_box1 = QComboBox()
        returnLayers = getLayerNames(QgsWkbTypes.LineGeometry)
        if returnLayers:
            list1 = returnLayers
        else:
            list1 = ["Brak warstw"]
            self.submit_button.setEnabled(False)
        self.combo_box1.addItems(list1)
        form_layout.addRow("Linie przekrojów:", self.combo_box1)

        # Połącz tylko zaznaczone przekroje
        self.selection_checkbox = QCheckBox("Połącz tylko zaznaczone linie przekrojów", self)
        self.selection_checkbox.setChecked(True)
        form_layout.addRow("",self.selection_checkbox)

        # Warstwy z warstwami geotechnicznymi
        self.combo_box2 = QComboBox()
        list2 = getLayerNames(QgsWkbTypes.PolygonGeometry)
        if returnLayers:
            list1 = returnLayers
        else:
            list1 = ["Brak warstw"]
            self.submit_button.setEnabled(False)
        self.combo_box2.addItems(list2)
        form_layout.addRow("Warunki geotechniczne:", self.combo_box2)

        # Nazwa kolumny z długościami linii przekrojów
        self.length_line_edit = QLineEdit("length")
        self.length_line_edit.setMaxLength(20)
        regex_column = QRegularExpression(r'^[\w\-]*$')
        validator = QRegularExpressionValidator(regex_column)
        self.length_line_edit.setValidator(validator)
        self.length_line_edit.setToolTip("Nazwa kolumny może zawierać tylko litery, cyfry, podkreślenia i myślniki.")
        self.length_line_edit.setPlaceholderText("Domyślna nazwa kolumny 'length'")
        form_layout.addRow("Nazwa kolumny z długościami linii przekrojów:", self.length_line_edit)

        # Nazwa pliku CSV do eksportu
        self.filename_line_edit = QLineEdit("przekroje_z_warunkami_geotechnicznymi")
        self.filename_line_edit.setMaxLength(40)
        regex_filename = QRegularExpression(r'^[\w]*$')
        validator = QRegularExpressionValidator(regex_filename)
        self.filename_line_edit.setValidator(validator)
        self.filename_line_edit.setToolTip("Nazwa pliku może zawierać tylko litery, cyfry i podkreślenia.")
        self.filename_line_edit.setPlaceholderText("Domyślna nazwa pliku 'przekroje_z_warunkami_geotechnicznymi'")
        form_layout.addRow("Nazwa pliku CSV do eksportu:", self.filename_line_edit)
        
        main_layout.addLayout(form_layout)

        # Usuń tymczasowe warstwy
        self.delete_checkbox = QCheckBox("Usuń tymczasowe warstwy powstałe w trakcie łączenia.", self)
        self.delete_checkbox.setChecked(True)
        main_layout.addWidget(self.delete_checkbox)

        main_layout.addWidget(self.submit_button)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        main_layout.addWidget(self.result_label)

    def on_submit(self):
        layer1 = self.combo_box1.currentText()
        layer2 = self.combo_box2.currentText()
        column_name = self.length_line_edit.text().strip()

        if(layer1 == layer2):
            self.result_label.setText(f"Wybrano te same warstwy, nie można ich połączyć.")
        elif column_name in getFieldNames(layer1):
            self.result_label.setText(f"Warstwa '{layer1}' już posiada kolumnę o nazwie '{column_name}'. Nie można przeprowadzić łączenia.\nZmień nazwę kolumny z długościami i spróbuj ponownie.")
        else:
            result = split_lines(layer1, layer2, self.selection_checkbox.isChecked())

            if result == 0:
                self.result_label.setText(f"Nie wybrano przekrojów.")
            else:
                self.result_label.setText(f"Trwa łączenie warstw '{layer1}' i '{layer2}'.")
                QApplication.processEvents()

                add_length_field('warunki_split', column_name)
                connect_layers('warunki_split_with_length', layer2)

                filename = self.filename_line_edit.text().strip()
                export_layer_to_csv('przekroje_warunki_polaczone', filename)
                self.result_label.setText(f"Wyeksportowano połączoną warstwę do pliku: {filename}")

                if self.delete_checkbox.isChecked():
                    remove_created_memory_layers()

window = Window()