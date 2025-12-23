from PyQt6.QtWidgets import *
import sys
from data_processor import DataProcessor
from column_presets import ColumnPresets
from table_generator import TableGenerator
from column_mapping_widget import ColumnMappingWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generator tabel DGI i DBP")
        self.setGeometry(100, 100, 900, 700)
        
        self.processor = DataProcessor()
        self.table_generator = TableGenerator()
        self.processed_df = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup głównego interfejsu użytkownika"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Wybór pliku CSV
        file_group = QGroupBox("1. Wybór pliku CSV")
        file_layout = QHBoxLayout()
        self.file_button = QPushButton("Wybierz plik CSV")
        self.file_button.clicked.connect(self.load_csv)
        self.file_label = QLabel("Nie wybrano pliku")
        file_layout.addWidget(self.file_button)
        file_layout.addWidget(self.file_label, stretch=1)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # Podstawowa konfiguracja nr_zal, charakterystyka, preset
        config_group = QGroupBox("2. Podstawowa konfiguracja")
        config_layout = QFormLayout()
        
        # Nr_zal
        self.nr_zal_combo = QComboBox()
        self.nr_zal_combo.addItem("-- Wybierz kolumnę --", None)
        self.nr_zal_combo.setEnabled(False)
        self.nr_zal_combo.currentIndexChanged.connect(self.validate_process_button)
        config_layout.addRow("Kolumna z numerami załączników/nazwami przekrojów:", self.nr_zal_combo)

        # Długości odcinków
        self.dlugosci_combo = QComboBox()
        self.dlugosci_combo.addItem("-- Wybierz kolumnę --", None)
        self.dlugosci_combo.setEnabled(False)
        self.dlugosci_combo.currentIndexChanged.connect(self.validate_process_button)
        config_layout.addRow("Kolumna z długościami odcinków:", self.dlugosci_combo)
        
        # Charakterystyka drogi
        self.charakterystyka_input = QLineEdit()
        self.charakterystyka_input.setText(
            "klasa drogi: S; kategoria ruchu: KR6; długość projektowanej drogi: 14,7 km"
        )
        config_layout.addRow("Charakterystyka drogi:", self.charakterystyka_input)
        
        # Wybór presetu kolumn
        preset_layout = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("-- Wybierz preset --", None)
        self.preset_combo.addItems(ColumnPresets.get_preset_types())
        self.preset_combo.setEnabled(False)
        self.preset_combo.currentIndexChanged.connect(self.apply_preset)
        preset_layout.addWidget(self.preset_combo)
        config_layout.addRow("Preset kolumn:", preset_layout)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)
        
        # Mapowanie kolumn
        mapping_group = QGroupBox("3. Mapowanie kolumn")
        self.mapping_layout = QVBoxLayout()
        self.column_mapping_widget = ColumnMappingWidget()
        self.mapping_layout.addWidget(self.column_mapping_widget)
        mapping_group.setLayout(self.mapping_layout)
        main_layout.addWidget(mapping_group, stretch=1)
        
        # Przyciski akcji
        button_layout = QHBoxLayout()
        
        self.process_button = QPushButton("Przetwórz dane")
        self.process_button.clicked.connect(self.process_data)
        self.process_button.setEnabled(False)
        
        self.export_button = QPushButton("Eksportuj do CSV/Excel")
        self.export_button.clicked.connect(self.export_data)
        self.export_button.setEnabled(False)
        
        self.generate_button = QPushButton("Generuj tabele (obrazy)")
        self.generate_button.clicked.connect(self.generate_tables)
        self.generate_button.setEnabled(False)
        
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.generate_button)
        main_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Wczytaj plik CSV aby rozpocząć")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px")
        main_layout.addWidget(self.status_label)
    
    def load_csv(self):
        """Wczytuje plik CSV"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik CSV", "", "CSV Files (*.csv);;All Files (*)")
        
        if file_path:
            # Wywołanie processora danych do wczytania CSV
            if self.processor.load_csv(file_path):
                self.file_label.setText(f"Wczytano: {file_path}")
                columns = self.processor.get_columns()
                
                # Uzupełnij combo box z num_zal dostępnymi kolumnami
                self.nr_zal_combo.clear()
                self.nr_zal_combo.addItem("-- Wybierz kolumnę --", None)
                self.nr_zal_combo.addItems(columns)
                self.nr_zal_combo.setEnabled(True)

                # Uzupełnij combo box z num_zal dostępnymi kolumnami
                self.dlugosci_combo.clear()
                self.dlugosci_combo.addItem("-- Wybierz kolumnę --", None)
                self.dlugosci_combo.addItems(columns)
                self.dlugosci_combo.setEnabled(True)
                
                # Włącz wybór presetu
                self.preset_combo.setEnabled(True)
                
                self.status_label.setText(f"✓ Wczytano {len(self.processor.df)} wierszy, {len(columns)} kolumn\nWybierz preset i zmapuj kolumny")
            else:
                self.status_label.setText("✗ Błąd wczytywania pliku")
    
    def apply_preset(self):
        """ Pobiera i stosuje wybrany preset kolumn """
        if self.processor.df is None:
            return
        if self.preset_combo.currentIndex() == 0:
            self.column_mapping_widget.setup_columns([], [], True)
            self.column_mapping_widget.info_label.setText("")
            self.validate_process_button()
            return
        
        preset_type = self.preset_combo.currentText()
        preset_columns = ColumnPresets.get_preset(preset_type)
        input_columns = self.processor.get_columns()
        
        self.column_mapping_widget.setup_columns(preset_columns, input_columns)
        self.validate_process_button()
        
        self.status_label.setText(f"✓ Zastosowano preset {preset_type} z {len(preset_columns)} kolumnami\nUzupełnij mapowanie kolumn i kliknij 'Przetwórz dane'")
    
    def validate_process_button(self):
        """Waliduje czy przycisk 'Przetwórz dane' powinien być aktywny"""
        # Sprawdza czy wybrano preset
        preset_selected = self.preset_combo.currentIndex() > 0
        
        # Sprawdza czy wybrano kolumnę z numerem załącznika
        nr_zal_selected = self.nr_zal_combo.currentIndex() > 0

        # Sprawdza czy wybrano kolumnę z długościami odcinków
        dlugosci_selected = self.dlugosci_combo.currentIndex() > 0
        
        # Włącz przycisk tylko gdy oba warunki są spełnione
        self.process_button.setEnabled(preset_selected and nr_zal_selected and dlugosci_selected)
    
    def process_data(self):
        """Przetwarza dane na podstawie mapowania kolumn"""
        try:
            nr_zal_col = self.nr_zal_combo.currentText()
            dlugosci_col = self.dlugosci_combo.currentText()
            charakterystyka = self.charakterystyka_input.text() # TODO: zamień na combo box tak jak nr_zal gdy będzie to uzupełnione w QGIS
            column_mapping = self.column_mapping_widget.get_column_mapping()
            
            if not column_mapping:
                QMessageBox.warning(self, "Brak mapowania", "Musisz zmapować przynajmniej jedną kolumnę")
                return

            self.processed_df = self.processor.process_data(nr_zal_col, charakterystyka, column_mapping)

            self.export_button.setEnabled(True)
            self.generate_button.setEnabled(True)
            
            self.status_label.setText(f"✓ Przetworzono dane: {len(self.processed_df)} wierszy\nMożesz eksportować lub generować tabele")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd przetwarzania: {str(e)}")
            self.status_label.setText(f"✗ Błąd: {str(e)}")
    
    def export_data(self):
        """Eksportuje przetworzone dane do CSV i Excel"""

        if self.processed_df is None:
            return
        
        try:
            self.status_label.setText("Eksportowanie danych...")
            self.processed_df.to_csv('output.csv', index=False)
            self.processed_df.to_excel('output.xlsx', index=False)
            
            self.status_label.setText("✓ Wyeksportowano dane do output.csv i output.xlsx")
            QMessageBox.information(self, "Sukces", "Dane wyeksportowane do:\n- output.csv\n- output.xlsx")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd eksportu: {str(e)}")
    
    def generate_tables(self):
        """Generuje tabele jako obrazy dla każdego nr_zal"""

        if self.processed_df is None:
            return
        
        try:
            self.status_label.setText("Generowanie tabel...")
            nr_zal_col = self.nr_zal_combo.currentText()
            
            # Pobiera tylko włączone kolumny z mapowania
            enabled_columns = [
                col for col, checkbox in self.column_mapping_widget.checkboxes.items()
                if checkbox.isChecked()
            ]
            
            # Jeżeli włączony jest "Kilometraż" dodaje wcześniej "Odległości"
            if "Kilometraż" in enabled_columns and "Odległości" not in enabled_columns:
                km_index = enabled_columns.index("Kilometraż")
                enabled_columns.insert(km_index,"Odległości")
            
            # Ustawia kolumny w generatorze tabel na te wybrane z presetu przez użytkownika
            self.table_generator.set_preset_columns(enabled_columns)
            
            # Wywołanie generatora
            files = self.table_generator.generate_all_tables(self.processed_df, nr_zal_col)
            
            self.status_label.setText(f"✓ Wygenerowano {len(files)} tabel w folderze 'tabele/'")
            QMessageBox.information(self, "Sukces", f"Wygenerowano {len(files)} tabel w folderze 'tabele/'")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd generowania: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())