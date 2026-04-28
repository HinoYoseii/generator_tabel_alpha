from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,QGroupBox, QPushButton, QLabel, QFileDialog, QMessageBox, QApplication)
from data_processor import DataProcessor
from preset_manager import PresetManager
from table_generator import TableGenerator
from column_mapping_widget import ColumnMappingWidget
from config_widget import ConfigWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generator tabel pod przekroje")
        self.setGeometry(400, 100, 1000, 800)

        self.data_processor = DataProcessor()
        self.table_generator = TableGenerator()
        self.presets_manager = PresetManager()
        self.processed_df = None

        self._setup_ui()

    def _setup_ui(self):
        """Setup głównego interfejsu użytkownika"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Wybór pliku CSV
        file_group = QGroupBox("1. Wybór pliku CSV")
        file_layout = QHBoxLayout()
        self.file_button = QPushButton("Wybierz plik CSV")
        self.file_button.clicked.connect(self._load_csv)
        self.file_label = QLabel("Nie wybrano pliku")
        file_layout.addWidget(self.file_button)
        file_layout.addWidget(self.file_label, stretch=1)
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)

        # Podstawowa konfiguracja
        self.config_widget = ConfigWidget(self.presets_manager, self.table_generator.get_scale_list())
        self.config_widget.nr_zal_combo.currentIndexChanged.connect(self._validate_process_button)
        self.config_widget.dlugosci_combo.currentIndexChanged.connect(self._validate_process_button)
        self.config_widget.skala_combo.currentIndexChanged.connect(self._validate_process_button)
        self.config_widget.width_input.valueChanged.connect(self._validate_process_button)
        self.config_widget.preset_combo.currentIndexChanged.connect(self._apply_preset)
        self.config_widget.preset_changed.connect(self._apply_preset)
        main_layout.addWidget(self.config_widget)

        # Mapowanie kolumn
        mapping_label = QLabel("3. Mapowanie kolumn")
        mapping_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(mapping_label)
        self.column_mapping_widget = ColumnMappingWidget()
        main_layout.addWidget(self.column_mapping_widget, stretch=1)

        # Przyciski akcji
        button_layout = QHBoxLayout()

        self.process_button = QPushButton("Przetwórz dane")
        self.process_button.clicked.connect(self._process_data)
        self.process_button.setEnabled(False)
        button_layout.addWidget(self.process_button)

        self.export_button = QPushButton("Eksportuj do CSV")
        self.export_button.clicked.connect(self._export_data)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)

        self.generate_button = QPushButton("Generuj tabele")
        self.generate_button.clicked.connect(self._generate_tables)
        self.generate_button.setEnabled(False)
        button_layout.addWidget(self.generate_button)

        main_layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Wczytaj plik CSV aby rozpocząć")
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

    def _set_status(self, text: str):
        self.status_label.setText(text)
        QApplication.processEvents()
    
    def _validate_process_button(self):
        self.process_button.setEnabled(self.config_widget.is_valid())
        self.export_button.setEnabled(False)
        self.generate_button.setEnabled(False)

    def _load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Wybierz plik CSV", "", "CSV Files (*.csv);;All Files (*)")
        
        if not file_path:
            return
        if not self.data_processor.load_csv(file_path):
            self._set_status("Błąd wczytywania pliku")
            return

        self.file_label.setText(f"Wczytano: {file_path}")
        self.config_widget.populate_columns(self.data_processor.get_columns())
        self._set_status("Wczytano plik CSV, wybierz preset i zmapuj kolumny")

    def _apply_preset(self):
        if self.data_processor.df is None:
            return
        if self.config_widget.preset_combo.currentIndex() == 0:
            self.column_mapping_widget.setup_columns([], [])
            self._validate_process_button()
            return

        preset_type = self.config_widget.get_preset_name()
        preset_columns = self.presets_manager.get_preset_rows(preset_type)
        self.column_mapping_widget.setup_columns(preset_columns, self.data_processor.get_columns())
        self._validate_process_button()
        self._set_status(f"Zastosowano preset {preset_type} z {len(preset_columns)} kolumnami\nUzupełnij mapowanie kolumn i kliknij 'Przetwórz dane'")

    def _process_data(self):
        column_mapping = self.column_mapping_widget.get_column_mapping()
        if not column_mapping:
            QMessageBox.warning(self, "Brak mapowania", "Musisz zmapować przynajmniej jedną kolumnę")
            return

        try:
            self._set_status("Przetwarzanie danych...")
            self.processed_df = self.data_processor.process_data(
                nr_zal_column=self.config_widget.get_nr_zal_col(),
                column_mapping=column_mapping,
                length_column=self.config_widget.get_dlugosci_col(),
                scale_column=self.config_widget.get_scale_column(),
            )
            
            self.export_button.setEnabled(True)
            self.generate_button.setEnabled(True)
            QMessageBox.information(self, "Sukces", f"Przetworzono dane. Możesz eksportować dane lub generować tabele")
            self._set_status(f"Przetworzono dane: {len(self.processed_df)} wierszy\nMożesz eksportować lub generować tabele")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd przetwarzania danych: {e}")
            self._set_status(f"Błąd przetwarzania danych: {e}")

    def _export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Zapisz plik CSV", "output.csv", "CSV Files (*.csv)")
        if not file_path: 
            return

        try:
            self.processed_df.to_csv(file_path, index=False)
            QMessageBox.information(self, "Sukces", f"Dane wyeksportowane do {file_path}")
            self._set_status(f"Dane wyeksportowane do {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd eksportu: {e}")
            self._set_status(f"Błąd eksportu: {e}")

    def _generate_tables(self):
        self._set_status("Generowanie tabel...")

        try:
            column_mapping = self.column_mapping_widget.get_column_mapping()
            config = self.config_widget.build_table_config(column_mapping)
            files = self.table_generator.generate_all_tables(
                df=self.processed_df,
                nr_zal_column=self.config_widget.get_nr_zal_col(),
                config=config
            )
            if not files:
                QMessageBox.critical(self, "Błąd", "\nNie udało się wygenerować tabel. Sprawdź dane wejściowe i mapowanie kolumn.")
                return
            QMessageBox.information(self, "Sukces", f"Wygenerowano {len(files)} tabel w folderze 'tabele'")
            self._set_status(f"Wygenerowano {len(files)} tabel w folderze 'tabele'")
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd generowania: {e}")
            self._set_status(f"Błąd generowania: {e}")