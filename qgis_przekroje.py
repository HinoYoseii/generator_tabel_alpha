from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QFormLayout, QComboBox, QPushButton, QLabel, QCheckBox, QLineEdit, QApplication, QFileDialog) # type: ignore
from PyQt5.QtGui import QRegularExpressionValidator # type: ignore
from PyQt5.QtCore import Qt, QRegularExpression # type: ignore

def get_layer_names(layerType):
    """ 
    Funkcja pobiera nazwy dostępnych warstw wektorowych w projekcie o wybranej geometrii (np. linie, poligony) 
    
    :param layerType: Jeden z dostępnych typów geometrii QgsWkbTypes: PointGeometry, LineGeometry, PolygonGeometry, UnknownGeometry, NullGeometry.
    :return: Lista nazw warstw o typie layerType.
    """
    layers = []
    for layer in QgsProject.instance().mapLayers().values(): # type: ignore
        type = layerType
        if layer.type() == QgsMapLayer.VectorLayer: # type: ignore
            if layer.geometryType() == type:
                layers.append(layer.name())
    return layers

def get_layer_field_names(line_layer_name):
    """
    Funkcja pobiera nazwy kolumn (pól) warstwy o nazwie line_layer_name.
    
    :param line_layer_name: Nazwa warstwy wektorowej w projekcie Qgis.
    :return: Lista nazw kolumn (pól) warstwy.
    """
    layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore
    return layer.fields().names()

def split_lines(line_layer_name, polygon_layer_name, splitOnlySelected=True):
    """ 
    Funkcja dzieli warstwę o nazwie line_layer_name na odcinki. 
    Przecięcia są wykonywane w miejscach intersekcji z krańcami poligonów warstwy o nazwie polygon_layer_name.
    Tworzy warstwę tymczasową 'lines_split'

    :param line_layer_name: Nazwa warstwy wektorowej z obiektami w postaci linii.
    :param polygon_layer_name: Nazwa warstwy wektorowej z obiektami w postaci poligonów.
    :param splitOnlySelected: True/False określa czy podzielone mają być tylko obecnie zaznaczone przekroje.
    :return: Jeżeli splitOnlySelected to True, a żadne przekroje nie są zaznaczone to zwraca 0.
    """
    line_layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore
    polygon_layer = QgsProject.instance().mapLayersByName(polygon_layer_name)[0] # type: ignore

    if not splitOnlySelected:
        line_layer.selectAll()
    
    selected_features = line_layer.selectedFeatures()
    
    if splitOnlySelected and len(selected_features) == 0:
        print("Nie zaznaczono przekrojów do eksportu.")
        return 0
    
    print(f"Liczba wybranych przekrojów: {len(selected_features)}")
    
    selected_layer = processing.run("native:saveselectedfeatures", { # type: ignore
        'INPUT': line_layer,
        'OUTPUT': 'memory:'
    })['OUTPUT']
    
    result = processing.run("native:splitwithlines", { # type: ignore
        'INPUT': selected_layer,
        'LINES': polygon_layer,
        'OUTPUT': 'memory:Split_Result'
    })

    split_layer = result['OUTPUT']
    split_layer.setName('lines_split')
    QgsProject.instance().addMapLayer(split_layer) # type: ignore
    
    print(f"Rozdzielono linie przerojów na warstwie '{line_layer_name}' za pomocą '{polygon_layer_name}'.")
    print(f"Liczba otrzymanych fragmentów: {split_layer.featureCount()}")

    if not splitOnlySelected:
        line_layer.removeSelection()

def connect_layers(line_layer_name, polygon_layer_name):
    """
    Funkcja łączy line_layer_name i polygon_layer_name na podstawie lokalizacji.
    Wybiera atrybuty obiektu z warstwy polygon_layer_name z największym nakładaniem z warstwą line_layer i łączy je w relacji jeden do jednego.
    Tworzy warstwę tymczasową 'line_polygon_final'.
    
    :param line_layer_name,: Nazwa warstwy wektorowej z obiektami w postaci linii.
    :param polygon_layer_name: Nazwa warstwy wektorowej z obiektami w postaci poligonów.
    """
    line_layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore
    polygon_layer = QgsProject.instance().mapLayersByName(polygon_layer_name)[0] # type: ignore

    result = processing.run("native:joinattributesbylocation", { # type: ignore
        'INPUT':line_layer,
        'PREDICATE':[0],
        'JOIN':polygon_layer,
        'JOIN_FIELDS':[],
        'METHOD':2,
        'DISCARD_NONMATCHING':False,
        'PREFIX':'',
        'OUTPUT':'memory:Combine_Result'
        })
    
    combined_layer = result['OUTPUT']
    combined_layer.setName('line_polygon_final')
    QgsProject.instance().addMapLayer(combined_layer) # type: ignore

    print(f"Połączono warstwy '{line_layer_name}' i '{polygon_layer_name}'.")

def add_length_field(line_layer_name, field_name='length'):
    """
    Funkcja oblicza długości linii w line_layer_name, a następnie dodaje kolumnę z obliczonymi długościami w liczbie całkowitej o nazwie field_name.
    Tworzy warstwę tymczasową 'input_later_with_length'.

    :param line_layer_name: Nazwa warstwy wektorowej z obiektami w postaci linii z liniami przekrojów.
    :param field_name: Nazwa kolumny z długościami, którą tworzy funkcja.
    """
    line_layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore
     
    result = processing.run("qgis:fieldcalculator", { # type: ignore
        'INPUT': line_layer,
        'FIELD_NAME': field_name,
        'FIELD_TYPE': 1, # int, zaokrągla do całkowitej
        'FIELD_LENGTH': 10,
        'FIELD_PRECISION': 3,
        'FORMULA': '$length',
        'OUTPUT': 'memory:with_length'
    })
    
    output_layer = result['OUTPUT']
    output_layer.setName(f'{line_layer_name}_with_length')
    QgsProject.instance().addMapLayer(output_layer) # type: ignore
    
    print(f"Dodano pole z długościami linii do '{line_layer_name}'")

def export_layer_to_csv(line_layer_name, output_path):
    """
    Funkcja eksportuje atrybuty warstwy o nazwie line_layer_name do pliku csv znajdującego się w output_path.
    
    :param line_layer_name: Nazwa warstwy do eksportu.
    :param output_path: Nazwa pod jaką ma być zapisany wyeksportowany plik.
    """
    layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore
    
    save_options = QgsVectorFileWriter.SaveVectorOptions() # type: ignore
    save_options.driverName = "CSV"
    save_options.fileEncoding = "UTF-8"
    
    error = QgsVectorFileWriter.writeAsVectorFormatV3( # type: ignore
        layer,
        output_path,
        QgsProject.instance().transformContext(), # type: ignore
        save_options
    )
    
    if error[0] == QgsVectorFileWriter.NoError: # type: ignore
        print(f"Warstwa '{line_layer_name}' wyeksportowana do: {output_path}")
    else:
        print(f"Error exporting layer: {error}")

def remove_created_memory_layers():
    """
    Funkcja usuwa wszytskie tymczasowe warstwy w projekcie.
    """
    project = QgsProject.instance() # type: ignore
    layers_to_remove = ['lines_split', 'lines_split_with_length', 'line_polygon_final']
    
    for layer in project.mapLayers().values():
        if (layer.name() in layers_to_remove) and (layer.dataProvider().name() == 'memory'):
            project.removeMapLayer(layer.id())
    
    print(f"Usunięto tymczasowe warstwy")

class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Podział warstwy linii warstwą poligonów")
        self.setGeometry(500, 100, 600, 300)
        self.UiComponents()
        self.show()

    def UiComponents(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignTop)

        # SEKCJA 1: WYBÓR WARSTW
        layers_group = QGroupBox("Wybór warstw") #type: ignore
        layers_group.setStyleSheet("QGroupBox { font-weight: bold }")
        layers_layout = QFormLayout(layers_group)

        # Warstwy przekrojów
        self.lines_combo_box = QComboBox()
        returnLayers = get_layer_names(QgsWkbTypes.LineGeometry) #type: ignore
        if returnLayers:
            lines_layers_list = returnLayers
        else:
            lines_layers_list = ["Brak warstw"]
            self.submit_button.setEnabled(False)
        self.lines_combo_box.addItems(lines_layers_list)
        layers_layout.addRow("Linie przekrojów:", self.lines_combo_box)

        # Połącz tylko zaznaczone przekroje
        self.selection_checkbox = QCheckBox("Użyj tylko zaznaczonych linii przekrojów", self)
        self.selection_checkbox.setToolTip("Jeżeli ta opcja jest zaznaczona to tylko obecnie zaznaczone linie przekrojów zostaną połączone z warstwami geotechnicznymi. W przeciwny wypadek zostaną połączone wszystkie linie przekrojów na wybranej warstwie.")
        self.selection_checkbox.setChecked(True)
        layers_layout.addRow("", self.selection_checkbox)

        # Warstwy poligonowe
        self.polygons_combo_box = QComboBox()
        returnLayers = get_layer_names(QgsWkbTypes.PolygonGeometry) #type: ignore
        if returnLayers:
            polygons_layers_list = returnLayers
        else:
            polygons_layers_list = ["Brak warstw"]
            self.submit_button.setEnabled(False)
        self.polygons_combo_box.addItems(polygons_layers_list)
        layers_layout.addRow("Warstwa dzieląca:", self.polygons_combo_box)
        
        main_layout.addWidget(layers_group)

        # SEKCJA 2: USTAWIENIA EKSPORTU
        export_group = QGroupBox("Ustawienia eksportu") #type: ignore
        export_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        export_layout = QFormLayout(export_group)
        
        # Nazwa kolumny z długościami linii przekrojów
        self.length_line_edit = QLineEdit("length")
        self.length_line_edit.setMaxLength(20)
        regex_column = QRegularExpression(r'^[\w\-]*$')
        validator = QRegularExpressionValidator(regex_column)
        self.length_line_edit.setValidator(validator)
        self.length_line_edit.setToolTip("Nazwa kolumny może zawierać tylko litery, cyfry, podkreślenia i myślniki.")
        self.length_line_edit.setPlaceholderText("Domyślna nazwa kolumny 'length'")
        export_layout.addRow("Nazwa kolumny z długościami podzielonych linii:", self.length_line_edit)

        # Nazwa pliku CSV do eksportu
        self.choose_file_path_button = QPushButton("Wybierz miejsce zapisu")
        self.choose_file_path_button.clicked.connect(self.chooseSaveFilePath)
        self.path_label = QLabel("Nie wybrano miejsca zapisu")
        self.path_label.setStyleSheet("font-weight: bold; color: #c00")
        export_layout.addRow(self.path_label, self.choose_file_path_button)
        
        main_layout.addWidget(export_group)

        # SEKCJA 3: ŁĄCZENIE WARSTW
        connect_group = QGroupBox("Łączenie warstw") #type: ignore
        connect_group.setStyleSheet("QGroupBox { font-weight: bold }")
        connect_layout = QVBoxLayout(connect_group)

        # Usuń tymczasowe warstwy
        self.delete_checkbox = QCheckBox("Usuń tymczasowe warstwy powstałe w trakcie łączenia.", self)
        self.delete_checkbox.setChecked(True)
        connect_layout.addWidget(self.delete_checkbox)

        # Połącz warstwy
        self.submit_button = QPushButton("Połącz")
        self.submit_button.clicked.connect(self.on_submit)
        self.submit_button.setEnabled(False)
        connect_layout.addWidget(self.submit_button)
        
        main_layout.addWidget(connect_group)

        # SEKCJA 4: Result label
        self.result_label = QLabel("Czekam na rozpoczęcie łączenia...")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-weight: bold; color:#999")
        main_layout.addWidget(self.result_label)

    def on_submit(self):
        self.submit_button.setEnabled(False)
        layer1 = self.lines_combo_box.currentText()
        layer2 = self.polygons_combo_box.currentText()
        length_column_name = self.length_line_edit.text().strip()

        if(layer1 == layer2):
            self.result_label.setText(f"Wybrano te same warstwy, nie można ich połączyć.")
            self.result_label.setStyleSheet("color: #c00")

        elif length_column_name in get_layer_field_names(layer1):
            self.result_label.setText(f"Warstwa '{layer1}' już posiada kolumnę o nazwie '{length_column_name}'. Nie można przeprowadzić łączenia.\nWybierz inną nazwę kolumny z długościami linii i spróbuj ponownie.")
            self.result_label.setStyleSheet("color: #c00")
        
        else:
            self.result_label.setText(f"Trwa dzielenie warstwy '{layer1}'...")
            self.result_label.setStyleSheet("color: #00c")
            QApplication.processEvents()
            result = split_lines(layer1, layer2, self.selection_checkbox.isChecked())

            if result == 0:
                self.result_label.setText(f"Nie wybrano przekrojów.")
                self.result_label.setStyleSheet("color: #c00")
            else:
                self.result_label.setText(f"Trwa łączenie atrybutów warstw '{layer1}' i '{layer2}'...")
                QApplication.processEvents()

                self.result_label.setText(f"Trwa obliczanie długości segmentów linii z podzielonej warstwy...")
                QApplication.processEvents()
                add_length_field('lines_split', length_column_name)
                connect_layers('lines_split_with_length', layer2)

                filename = self.path_label.text().strip()
                export_layer_to_csv('line_polygon_final', filename)
                self.result_label.setText(f"Wyeksportowano połączoną warstwę do pliku: {filename}")
                self.result_label.setStyleSheet("color: #0c0")

                if self.delete_checkbox.isChecked():
                    remove_created_memory_layers()

        self.submit_button.setEnabled(True)

    def chooseSaveFilePath(self):
        file_path, _ = QFileDialog.getSaveFileName(self,"Wybierz miejsce zapisu pliku CSV","","Pliki CSV (*.csv);;Wszystkie pliki (*.*)")
        
        if file_path:
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            self.submit_button.setEnabled(True)
            self.path_label.setText(file_path)
            self.path_label.setStyleSheet("font-weight: normal; color: #000")
            self.choose_file_path_button.setText("Zmień miejsce eksportu")
        
        return file_path

window = Window()