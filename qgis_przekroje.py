from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QFormLayout, QComboBox, # type: ignore
                            QPushButton, QLabel, QCheckBox, QLineEdit, QApplication, 
                            QFileDialog, QGroupBox, QHBoxLayout, QScrollArea, QFrame,
                            QListWidget, QAbstractItemView) # type: ignore
from PyQt5.QtGui import QRegularExpressionValidator # type: ignore
from PyQt5.QtCore import Qt, QRegularExpression # type: ignore

def get_layer_names(layerType):
    """ 
    Funkcja pobiera nazwy dostępnych warstw wektorowych w projekcie o wybranej geometrii 
    
    :param layerType: Jeden z dostępnych typów geometrii QgsWkbTypes: PointGeometry, LineGeometry, PolygonGeometry, UnknownGeometry, NullGeometry.
    :return: Lista nazw warstw o typie layerType.
    """
    layers = []
    for layer in QgsProject.instance().mapLayers().values(): # type: ignore
        type = layerType
        if layer.type() == QgsMapLayer.VectorLayer: # type: ignore
            if layer.geometryType() == type:
                layers.append(layer.name())
    
    if layers:
        return layers

    return ["Brak warstw"]

def get_layer_field_names(line_layer_name):
    """
    Funkcja pobiera nazwy kolumn (pól) warstwy o nazwie line_layer_name.
    
    :param line_layer_name: Nazwa warstwy wektorowej w projekcie Qgis.
    :return: Lista nazw kolumn (pól) warstwy.
    """
    layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore
    return layer.fields().names()

def merge_polygon_layers(polygon_layer_names):
    """
    Funkcja łączy wiele warstw poligonowych w jedną warstwę.
    
    :param polygon_layer_names: Lista nazw warstw poligonowych do połączenia.
    :return: Połączona warstwa poligonowa.
    """
    # Jeżeli została wybrana tylko jedna warstwa z poligonami to od razu ją zwraca
    if len(polygon_layer_names) == 1:
        return QgsProject.instance().mapLayersByName(polygon_layer_names[0])[0] # type: ignore
    
    # W przeciwnym wypadku łączy wszystkie warstwy poligonowe
    polygon_layers = []
    for name in polygon_layer_names:
        layer = QgsProject.instance().mapLayersByName(name)[0] # type: ignore
        polygon_layers.append(layer)
    
    result = processing.run("native:mergevectorlayers", { # type: ignore
        'LAYERS': polygon_layers,
        'CRS': None,
        'OUTPUT': 'memory:merged_polygons'
    })
    
    merged_layer = result['OUTPUT']
    merged_layer.setName('merged_polygons_temp')
    QgsProject.instance().addMapLayer(merged_layer) # type: ignore
    
    print(f"Połączono {len(polygon_layer_names)} warstw poligonowych w jedną.")
    return merged_layer

def split_lines(line_layer_name, merged_polygon_layer, splitOnlySelected=True):
    """ 
    Funkcja dzieli warstwę o nazwie line_layer_name na odcinki. 
    Przecięcia są wykonywane w miejscach intersekcji z krańcami połączonej warstwy poligonowej.
    Tworzy warstwę tymczasową 'lines_split'

    :param line_layer_name: Nazwa warstwy wektorowej z obiektami w postaci linii.
    :param merged_polygon_layer: Połączona warstwa poligonowa.
    :param splitOnlySelected: True/False określa czy podzielone mają być tylko obecnie zaznaczone przekroje.
    :return: Jeżeli splitOnlySelected to True, a żadne przekroje nie są zaznaczone to zwraca 0, w przeciwnym wypadku zwraca podzieloną warstwę.
    """
    line_layer = QgsProject.instance().mapLayersByName(line_layer_name)[0] # type: ignore

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
        'LINES': merged_polygon_layer,
        'OUTPUT': 'memory:Split_Result'
    })

    split_layer = result['OUTPUT']
    split_layer.setName('lines_split')
    QgsProject.instance().addMapLayer(split_layer) # type: ignore
    
    print(f"Rozdzielono linie przekrojów na warstwie '{line_layer_name}' za pomocą połączonych warstw poligonowych.")
    print(f"Liczba otrzymanych fragmentów: {split_layer.featureCount()}")

    if not splitOnlySelected:
        line_layer.removeSelection()
    
    return split_layer

def connect_with_multiple_polygons(split_layer, polygon_layer_names):
    """
    Funkcja łączy podzieloną warstwę linii z wieloma warstwami poligonowymi.
    Dodaje atrybuty z każdej warstwy poligonowej jako osobne kolumny z prefiksem nazwy warstwy.
    
    :param split_layer: Podzielona warstwa linii.
    :param polygon_layer_names: Lista nazw warstw poligonowych.
    :return: Warstwa z połączonymi atrybutami.
    """
    current_layer = split_layer
    
    for polygon_name in polygon_layer_names:
        polygon_layer = QgsProject.instance().mapLayersByName(polygon_name)[0] # type: ignore
        
        result = processing.run("native:joinattributesbylocation", { # type: ignore
            'INPUT': current_layer,
            'PREDICATE': [0],  # intersects
            'JOIN': polygon_layer,
            'JOIN_FIELDS': [],  # all fields
            'METHOD': 2,  # one-to-one (take attributes of feature with largest overlap)
            'DISCARD_NONMATCHING': False,
            'PREFIX': f'{polygon_name}_',
            'OUTPUT': 'memory:'
        })
        
        current_layer = result['OUTPUT']
    
    current_layer.setName('line_polygon_final')
    QgsProject.instance().addMapLayer(current_layer) # type: ignore
    
    print(f"Połączono warstwę linii z {len(polygon_layer_names)} warstwami poligonowymi.")
    return current_layer

def add_length_field(line_layer, field_name='length'):
    """
    Funkcja oblicza długości linii w line_layer, a następnie dodaje kolumnę z obliczonymi długościami w liczbie całkowitej o nazwie field_name.
    Zwraca warstwę z dodanym polem długości.

    :param line_layer: Warstwa wektorowa z obiektami w postaci linii.
    :param field_name: Nazwa kolumny z długościami, którą tworzy funkcja.
    :return: Warstwa z dodanym polem długości.
    """
    result = processing.run("qgis:fieldcalculator", { # type: ignore
        'INPUT': line_layer,
        'FIELD_NAME': field_name,
        'FIELD_TYPE': 1,  # int, zaokrągla do całkowitej
        'FIELD_LENGTH': 10,
        'FIELD_PRECISION': 3,
        'FORMULA': '$length',
        'OUTPUT': 'memory:'
    })
    
    output_layer = result['OUTPUT']
    output_layer.setName(f'lines_with_length')
    QgsProject.instance().addMapLayer(output_layer) # type: ignore
    
    return output_layer

def add_unique_name_field(line_layer, field_name, selected_columns, separator="_"):
    """
    Funkcja tworzy nową kolumnę z unikalną nazwą poprzez połączenie wartości z wybranych kolumn.
    
    :param line_layer: Warstwa wektorowa z obiektami w postaci linii.
    :param field_name: Nazwa nowej kolumny z unikalną nazwą.
    :param selected_columns: Lista nazw kolumn do połączenia.
    :param separator: Separator między wartościami (domyślnie "_").
    :return: Warstwa z dodanym polem unikalnej nazwy.
    """
    # Zbuduj formułę do połączenia kolumn
    if len(selected_columns) == 1:
        # Dla pojedynczej kolumny, konwertuj na tekst
        formula = f'to_string( "{selected_columns[0]}" )'
    else:
        # Dla wielu kolumn, połącz je z separatorem
        columns_formatted = [f'to_string( "{col}" )' for col in selected_columns]
        formula = f'concat({", \'_\', ".join(columns_formatted)})'
    
    result = processing.run("qgis:fieldcalculator", { # type: ignore
        'INPUT': line_layer,
        'FIELD_NAME': field_name,
        'FIELD_TYPE': 2,  # string
        'FIELD_LENGTH': 255,
        'FIELD_PRECISION': 0,
        'FORMULA': formula,
        'OUTPUT': 'memory:'
    })
    
    output_layer = result['OUTPUT']
    
    output_layer.setName(f'{line_layer.name()}_with_unique_name')
    QgsProject.instance().addMapLayer(output_layer) # type: ignore
    
    return output_layer

def export_layer_to_csv(layer, output_path):
    """
    Funkcja eksportuje atrybuty warstwy do pliku csv znajdującego się w output_path.
    
    :param layer: Warstwa do eksportu.
    :param output_path: Ścieżka do zapisu.
    :return: Ścieżka zapisanego pliku lub None w przypadku błędu.
    """
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
        print(f"Warstwa wyeksportowana do: {output_path}")
        return output_path
    else:
        print(f"Error exporting layer: {error}")
        return None

def remove_created_memory_layers():
    """
    Funkcja usuwa wszystkie tymczasowe warstwy w projekcie.
    """
    project = QgsProject.instance() # type: ignore
    
    layers_to_remove = ['lines_split', 'lines_with_length', 'line_polygon_final', 'merged_polygons_temp']
    
    for layer in project.mapLayers().values():
        if (layer.name() in layers_to_remove) and (layer.dataProvider().name() == 'memory'):
            project.removeMapLayer(layer.id())
    
    print(f"Usunięto tymczasowe warstwy")

class Window(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Podział warstwy linii warstwami poligonów")
        self.setGeometry(500, 50, 600, 600)
        self.UiComponents()
        self.show()

    def UiComponents(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignTop)

        # SEKCJA 1: WYBÓR WARSTWY LINII
        lines_group = QGroupBox("Wybór warstwy linii przekrojów")
        lines_group.setStyleSheet("QGroupBox { font-weight: bold }")
        lines_layout = QVBoxLayout(lines_group)

        # Warstwy przekrojów
        self.lines_combo_box = QComboBox()
        lines_layers_list = get_layer_names(QgsWkbTypes.LineGeometry) #type: ignore
        self.lines_combo_box.addItems(lines_layers_list)
        self.lines_combo_box.currentTextChanged.connect(self.update_available_columns)
        lines_layout.addWidget(self.lines_combo_box)

        # Połącz tylko zaznaczone przekroje
        self.selection_checkbox = QCheckBox("Użyj tylko zaznaczonych linii przekrojów", self)
        lines_layout.addWidget(self.selection_checkbox)
        
        main_layout.addWidget(lines_group)

        # SEKCJA 2: WYBÓR WARSTW POLIGONOWYCH (WIELOKROTNY WYBÓR)
        polygons_group = QGroupBox("Wybór warstw poligonowych (możliwy wielokrotny wybór)")
        polygons_group.setStyleSheet("QGroupBox { font-weight: bold }") 
        polygons_layout = QVBoxLayout(polygons_group)

        # Obszar przewijany z checkboxami dla warstw poligonowych
        scroll_area = QScrollArea()
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setAlignment(Qt.AlignTop)
        
        # Pobierz wszystkie warstwy poligonowe i utwórz dla nich checkboxy
        self.polygon_checkboxes = []
        self.polygon_checkbox_layout = scroll_layout
        
        available_polygons = get_layer_names(QgsWkbTypes.PolygonGeometry) #type: ignore
        
        if available_polygons:
            for polygon_name in available_polygons:
                checkbox = QCheckBox(polygon_name)
                checkbox.stateChanged.connect(self.check_submit_button_state)
                scroll_layout.addWidget(checkbox)
                self.polygon_checkboxes.append(checkbox)
        else:
            no_layers_label = QLabel("Brak warstw poligonowych w projekcie")
            no_layers_label.setStyleSheet("color: #999; font-style: italic;")
            scroll_layout.addWidget(no_layers_label)
        
        scroll_area.setWidget(scroll_content)
        polygons_layout.addWidget(scroll_area)
        
        main_layout.addWidget(polygons_group)

        # SEKCJA 3: TWORZENIE UNIKALNEJ NAZWY
        unique_name_group = QGroupBox("Tworzenie unikalnej nazwy dla każdego odcinka")
        unique_name_group.setStyleSheet("QGroupBox { font-weight: bold }")
        unique_name_layout = QVBoxLayout(unique_name_group)
        
        # Checkbox do włączenia/wyłączenia funkcji
        self.unique_name_checkbox = QCheckBox("Utwórz kolumnę z unikalną nazwą dla każdego odcinka")
        self.unique_name_checkbox.setChecked(False)
        self.unique_name_checkbox.stateChanged.connect(self.on_unique_name_checkbox_changed)
        unique_name_layout.addWidget(self.unique_name_checkbox)
        
        # Ramka z ustawieniami unikalnej nazwy (domyślnie wyłączona)
        self.unique_name_settings = QFrame()
        self.unique_name_settings.setEnabled(False)
        settings_layout = QVBoxLayout(self.unique_name_settings)
        
        # Nazwa kolumny dla unikalnej nazwy
        name_layout = QFormLayout()
        self.unique_column_name = QLineEdit("unique_name")
        self.unique_column_name.setMaxLength(30)
        regex_column = QRegularExpression(r'^[\w\-]*$')
        validator = QRegularExpressionValidator(regex_column)
        self.unique_column_name.setValidator(validator)
        self.unique_column_name.setToolTip("Nazwa kolumny może zawierać tylko litery, cyfry, podkreślenia i myślniki.")
        name_layout.addRow("Nazwa kolumny z unikalną nazwą:", self.unique_column_name)
        settings_layout.addLayout(name_layout)
        
        # Przyciski do przenoszenia kolumn
        button_layout = QHBoxLayout()
        
        # Lewa lista - dostępne kolumny
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Dostępne kolumny:"))
        self.available_columns_list = QListWidget()
        self.available_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.available_columns_list.setMaximumHeight(150)
        left_layout.addWidget(self.available_columns_list)
        button_layout.addLayout(left_layout)
        
        # Przyciski środkowe
        mid_layout = QVBoxLayout()
        mid_layout.setAlignment(Qt.AlignCenter)
        
        self.add_button = QPushButton(">")
        self.add_button.setMaximumWidth(40)
        self.add_button.clicked.connect(self.add_selected_columns)
        mid_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("<")
        self.remove_button.setMaximumWidth(40)
        self.remove_button.clicked.connect(self.remove_selected_columns)
        mid_layout.addWidget(self.remove_button)
        
        button_layout.addLayout(mid_layout)
        
        # Prawa lista - wybrane kolumny
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Wybrane kolumny (kolejność łączenia):"))
        self.selected_columns_list = QListWidget()
        self.selected_columns_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.selected_columns_list.setMaximumHeight(150)
        self.selected_columns_list.setDragDropMode(QListWidget.InternalMove)  # Pozwala na przeciąganie
        right_layout.addWidget(self.selected_columns_list)
        button_layout.addLayout(right_layout)
        
        settings_layout.addLayout(button_layout)
        
        # Przyciski do zmiany kolejności
        order_layout = QHBoxLayout()
        order_layout.addStretch()
        
        self.move_up_button = QPushButton("↑")
        self.move_up_button.setMaximumWidth(40)
        self.move_up_button.clicked.connect(self.move_selected_up)
        order_layout.addWidget(self.move_up_button)
        
        self.move_down_button = QPushButton("↓")
        self.move_down_button.setMaximumWidth(40)
        self.move_down_button.clicked.connect(self.move_selected_down)
        order_layout.addWidget(self.move_down_button)
        
        settings_layout.addLayout(order_layout)
        
        unique_name_layout.addWidget(self.unique_name_settings)
        main_layout.addWidget(unique_name_group)

        # SEKCJA 4: USTAWIENIA EKSPORTU
        export_group = QGroupBox("Ustawienia eksportu")
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
        export_layout.addRow("Nazwa kolumny z długościami linii:", self.length_line_edit)

        # Nazwa pliku CSV do eksportu
        self.choose_file_path_button = QPushButton("Wybierz miejsce zapisu")
        self.choose_file_path_button.clicked.connect(self.chooseSaveFilePath)
        self.path_label = QLabel("Nie wybrano miejsca zapisu")
        self.path_label.setStyleSheet("font-weight: bold; color: #c00")
        export_layout.addRow(self.path_label, self.choose_file_path_button)
        
        main_layout.addWidget(export_group)

        # SEKCJA 5: ŁĄCZENIE WARSTW
        connect_group = QGroupBox("Łączenie warstw")
        connect_group.setStyleSheet("QGroupBox { font-weight: bold }")
        connect_layout = QVBoxLayout(connect_group)

        # Usuń tymczasowe warstwy
        self.delete_checkbox = QCheckBox("Usuń tymczasowe warstwy powstałe w trakcie łączenia.", self)
        self.delete_checkbox.setChecked(True)
        connect_layout.addWidget(self.delete_checkbox)

        # Połącz warstwy
        self.submit_button = QPushButton("Połącz wszystkie")
        self.submit_button.clicked.connect(self.on_submit)
        self.submit_button.setEnabled(False)
        connect_layout.addWidget(self.submit_button)
        
        main_layout.addWidget(connect_group)

        # SEKCJA 6: Result label
        self.result_label = QLabel("Wybierz warstwy do połączenia...")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-weight: bold; color:#999")
        self.result_label.setMaximumHeight(20)
        main_layout.addWidget(self.result_label)

    def update_available_columns(self):
        """Aktualizuje listę dostępnych kolumn dla wybranej warstwy linii"""
        self.available_columns_list.clear()
        self.selected_columns_list.clear()
        
        line_layer_name = self.lines_combo_box.currentText()
        if line_layer_name and line_layer_name != "Brak warstw":
            try:
                field_names = get_layer_field_names(line_layer_name)
                for field_name in field_names:
                    self.available_columns_list.addItem(field_name)
            except:
                pass

    def on_unique_name_checkbox_changed(self):
        """Włącza/wyłącza ustawienia unikalnej nazwy"""
        self.unique_name_settings.setEnabled(self.unique_name_checkbox.isChecked())
        if self.unique_name_checkbox.isChecked():
            self.update_available_columns()

    def add_selected_columns(self):
        """Dodaje zaznaczone kolumny z lewej listy do prawej"""
        selected_items = self.available_columns_list.selectedItems()
        for item in selected_items:
            # Sprawdź czy już istnieje na prawej liście
            existing_items = [self.selected_columns_list.item(i).text() 
                             for i in range(self.selected_columns_list.count())]
            if item.text() not in existing_items:
                self.selected_columns_list.addItem(item.text())
        
        # Usuń dodane kolumny z lewej listy
        for item in selected_items:
            self.available_columns_list.takeItem(self.available_columns_list.row(item))

    def remove_selected_columns(self):
        """Usuwa zaznaczone kolumny z prawej listy i przywraca je do lewej"""
        selected_items = self.selected_columns_list.selectedItems()
        for item in selected_items:
            # Sprawdź czy już istnieje na lewej liście
            existing_items = [self.available_columns_list.item(i).text() 
                             for i in range(self.available_columns_list.count())]
            if item.text() not in existing_items:
                self.available_columns_list.addItem(item.text())
            self.selected_columns_list.takeItem(self.selected_columns_list.row(item))

    def move_selected_up(self):
        """Przesuwa zaznaczone elementy w górę na liście"""
        current_row = self.selected_columns_list.currentRow()
        if current_row > 0:
            item = self.selected_columns_list.takeItem(current_row)
            self.selected_columns_list.insertItem(current_row - 1, item)
            self.selected_columns_list.setCurrentRow(current_row - 1)

    def move_selected_down(self):
        """Przesuwa zaznaczone elementy w dół na liście"""
        current_row = self.selected_columns_list.currentRow()
        if current_row < self.selected_columns_list.count() - 1:
            item = self.selected_columns_list.takeItem(current_row)
            self.selected_columns_list.insertItem(current_row + 1, item)
            self.selected_columns_list.setCurrentRow(current_row + 1)

    def get_selected_polygon_layers(self):
        """Zwraca listę zaznaczonych warstw poligonowych"""
        selected = []
        for checkbox in self.polygon_checkboxes:
            if checkbox.isChecked():
                selected.append(checkbox.text())
        return selected

    def get_selected_columns_for_unique_name(self):
        """Zwraca listę wybranych kolumn do utworzenia unikalnej nazwy"""
        columns = []
        for i in range(self.selected_columns_list.count()):
            columns.append(self.selected_columns_list.item(i).text())
        return columns

    def check_submit_button_state(self):
        """Sprawdza czy można włączyć przycisk submit"""
        line_layer = self.lines_combo_box.currentText()
        has_polygons = len(self.get_selected_polygon_layers()) > 0
        has_file_path = self.path_label.text() != "Nie wybrano miejsca zapisu"
        
        # Sprawdź czy jeśli opcja unikalnej nazwy jest włączona, to czy wybrano kolumny
        unique_name_ok = True
        if self.unique_name_checkbox.isChecked():
            unique_name_ok = len(self.get_selected_columns_for_unique_name()) > 0
        
        self.submit_button.setEnabled(line_layer != "Brak warstw" and has_polygons and has_file_path and unique_name_ok)

    def on_submit(self):
        self.submit_button.setEnabled(False)
        line_layer_name = self.lines_combo_box.currentText()
        length_column_name = self.length_line_edit.text().strip()
        polygon_layers = self.get_selected_polygon_layers()
        
        if not polygon_layers:
            self.result_label.setText("Nie wybrano żadnych warstw poligonowych.")
            self.result_label.setStyleSheet("color: #c00")
            self.submit_button.setEnabled(True)
            return
        
        if length_column_name in get_layer_field_names(line_layer_name):
            self.result_label.setText(f"Warstwa '{line_layer_name}' już posiada kolumnę o nazwie '{length_column_name}'. Wybierz inną nazwę.")
            self.result_label.setStyleSheet("color: #c00")
            self.submit_button.setEnabled(True)
            return
        
        # Sprawdź unikalną nazwę
        unique_column_name = None
        selected_columns = []
        if self.unique_name_checkbox.isChecked():
            unique_column_name = self.unique_column_name.text().strip()
            if not unique_column_name:
                self.result_label.setText("Musisz podać nazwę kolumny dla unikalnej nazwy.")
                self.result_label.setStyleSheet("color: #c00")
                self.submit_button.setEnabled(True)
                return
            
            selected_columns = self.get_selected_columns_for_unique_name()
            if len(selected_columns) == 0:
                self.result_label.setText("Musisz wybrać co najmniej jedną kolumnę do utworzenia unikalnej nazwy.")
                self.result_label.setStyleSheet("color: #c00")
                self.submit_button.setEnabled(True)
                return
            
            if unique_column_name in get_layer_field_names(line_layer_name):
                self.result_label.setText(f"Warstwa '{line_layer_name}' już posiada kolumnę o nazwie '{unique_column_name}'. Wybierz inną nazwę.")
                self.result_label.setStyleSheet("color: #c00")
                self.submit_button.setEnabled(True)
                return
        
        self.result_label.setText(f"Krok 1/5: Łączenie {len(polygon_layers)} warstw poligonowych w jedną...")
        self.result_label.setStyleSheet("color: #00c")
        QApplication.processEvents()
        
        # 1. Połącz wybrane warstwy poligonowe
        merged_polygon_layer = merge_polygon_layers(polygon_layers)
        
        self.result_label.setText(f"Krok 2/5: Dzielenie warstwy linii '{line_layer_name}' połączoną warstwą poligonową...")
        QApplication.processEvents()
        
        # 2. Podziel wybraną warstwę linii za pomocą połączonej warstwy poligonowej
        split_result = split_lines(line_layer_name, merged_polygon_layer, self.selection_checkbox.isChecked())
        
        if split_result == 0:
            self.result_label.setText(f"Nie wybrano przekrojów do podziału.")
            self.result_label.setStyleSheet("color: #c00")
            self.submit_button.setEnabled(True)
            return
        
        split_layer = QgsProject.instance().mapLayersByName('lines_split')[0] # type: ignore
        
        self.result_label.setText(f"Krok 3/5: Dodawanie pola długości '{length_column_name}' do podzielonych linii...")
        QApplication.processEvents()
        
        # 3. Oblicz długości podzielonych linii i dodaj pole z wynikiem
        lines_with_length = add_length_field(split_layer, length_column_name)
        
        # 4. Dodaj pole z unikalną nazwą jeśli zaznaczone
        current_layer = lines_with_length
        if unique_column_name and selected_columns:
            self.result_label.setText(f"Krok 4/5: Tworzenie kolumny z unikalną nazwą '{unique_column_name}'...")
            QApplication.processEvents()
            
            current_layer = add_unique_name_field(current_layer, unique_column_name, selected_columns, "_")
        
        self.result_label.setText(f"Krok 5/5: Łączenie atrybutów z {len(polygon_layers)} warstwami poligonowymi...")
        QApplication.processEvents()
        
        # 5. Połącz warstwę linii z warstwą poligonów
        final_layer = connect_with_multiple_polygons(current_layer, polygon_layers)
        
        # 6. Eksportuj do CSV
        filename = self.path_label.text().strip()
        self.result_label.setText(f"Eksportowanie do pliku CSV...")
        QApplication.processEvents()
        
        exported_file = export_layer_to_csv(final_layer, filename)
        
        if exported_file:
            self.result_label.setText(f"Sukces! Wyeksportowano połączoną warstwę do pliku: {exported_file}")
            self.result_label.setStyleSheet("color: #0c0")
        else:
            self.result_label.setText(f"Błąd podczas eksportu do pliku CSV.")
            self.result_label.setStyleSheet("color: #c00")
        
        # 7. Wyczyść warstwy tymczasowe
        if self.delete_checkbox.isChecked():
            remove_created_memory_layers()
        
        self.submit_button.setEnabled(True)

    def chooseSaveFilePath(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Wybierz miejsce zapisu pliku CSV", "", "Pliki CSV (*.csv);;Wszystkie pliki (*.*)")
        
        if file_path:
            if not file_path.lower().endswith('.csv'):
                file_path += '.csv'
            
            self.path_label.setText(file_path)
            self.path_label.setStyleSheet("font-weight: normal; color: #000")
            self.choose_file_path_button.setText("Zmień miejsce eksportu")
            self.check_submit_button_state()
        
        return file_path

window = Window()