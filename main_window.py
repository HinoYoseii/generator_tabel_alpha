from PyQt6.QtWidgets import *
import sys
from data_processor import DataProcessor
from column_presets import ColumnPresets
from table_generator import TableGenerator
from column_mapping_widget import ColumnMappingWidget
from config_widget import ConfigWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generator tabel DGI i DBP")
        self.setGeometry(100, 100, 900, 700)

        self.processor = DataProcessor()
        self.table_generator = TableGenerator()
        self.presets_manager = ColumnPresets()
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

        # Podstawowa konfiguracja
        self.config_widget = ConfigWidget(self.presets_manager, self.table_generator)
        self.config_widget.nr_zal_combo.currentIndexChanged.connect(self.validate_process_button)
        self.config_widget.dlugosci_combo.currentIndexChanged.connect(self.validate_process_button)
        self.config_widget.skala_combo.currentIndexChanged.connect(self.validate_process_button)
        self.config_widget.preset_combo.currentIndexChanged.connect(self.apply_preset)
        main_layout.addWidget(self.config_widget)

        # Mapowanie kolumn
        mapping_group = QGroupBox("3. Mapowanie kolumn")
        mapping_layout = QVBoxLayout()
        self.column_mapping_widget = ColumnMappingWidget()
        mapping_layout.addWidget(self.column_mapping_widget)
        mapping_group.setLayout(mapping_layout)
        main_layout.addWidget(mapping_group, stretch=1)

        # Przyciski akcji
        button_layout = QHBoxLayout()

        self.process_button = QPushButton("Przetwórz dane")
        self.process_button.clicked.connect(self.process_data)
        self.process_button.setEnabled(False)

        self.export_button = QPushButton("Eksportuj do CSV")
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
            if self.processor.load_csv(file_path):
                self.file_label.setText(f"Wczytano: {file_path}")
                columns = self.processor.get_columns()

                self.config_widget.populate_columns(columns)

                self.export_button.setEnabled(False)
                self.generate_button.setEnabled(False)

                self.status_label.setText(
                    f"Wczytano {len(self.processor.df)} wierszy, {len(columns)} kolumn\n"
                    "Wybierz preset i zmapuj kolumny"
                )
            else:
                self.status_label.setText("Błąd wczytywania pliku")

    def apply_preset(self):
        """Pobiera i stosuje wybrany preset kolumn"""
        if self.processor.df is None:
            return
        if self.config_widget.preset_combo.currentIndex() == 0:
            self.column_mapping_widget.setup_columns([], [], True)
            self.column_mapping_widget.info_label.setText("")
            self.validate_process_button()
            return

        preset_type = self.config_widget.get_preset_name()
        preset_columns = self.presets_manager.get_preset_columns(preset_type)
        input_columns = self.processor.get_columns()

        self.column_mapping_widget.setup_columns(preset_columns, input_columns)
        self.validate_process_button()

        self.status_label.setText(
            f"✓ Zastosowano preset {preset_type} z {len(preset_columns)} kolumnami\n"
            "Uzupełnij mapowanie kolumn i kliknij 'Przetwórz dane'"
        )

    def validate_process_button(self):
        """Waliduje czy przycisk 'Przetwórz dane' powinien być aktywny"""
        self.process_button.setEnabled(self.config_widget.is_valid())

    def process_data(self):
        """Przetwarza dane na podstawie mapowania kolumn"""
        try:
            self.status_label.setText("Przetwarzanie danych...")
            QApplication.processEvents()

            nr_zal_col = self.config_widget.get_nr_zal_col()
            dlugosci_col = self.config_widget.get_dlugosci_col()
            column_mapping = self.column_mapping_widget.get_column_mapping()

            if not column_mapping:
                QMessageBox.warning(self, "Brak mapowania", "Musisz zmapować przynajmniej jedną kolumnę")
                return

            self.processed_df = self.processor.process_data(nr_zal_col, column_mapping, dlugosci_col)

            self.export_button.setEnabled(True)
            self.generate_button.setEnabled(True)

            self.status_label.setText(
                f"Przetworzono dane: {len(self.processed_df)} wierszy\n"
                "Możesz eksportować lub generować tabele"
            )
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd przetwarzania: {str(e)}")
            self.status_label.setText(f"Błąd: {str(e)}")

    def export_data(self):
        """Eksportuje przetworzone dane do CSV"""
        if self.processed_df is None:
            return

        try:
            self.status_label.setText("Eksportowanie danych...")
            QApplication.processEvents()
            self.processed_df.to_csv('output.csv', index=False)

            self.status_label.setText("Wyeksportowano dane do output.csv")
            QMessageBox.information(self, "Sukces", "Dane wyeksportowane do:\n- output.csv")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd eksportu: {str(e)}")

    def generate_tables(self):
        """Generuje tabele jako obrazy dla każdego nr_zal"""
        if self.processed_df is None:
            return

        try:
            self.status_label.setText("Generowanie tabel...")
            QApplication.processEvents()

            nr_zal_col = self.config_widget.get_nr_zal_col()

            enabled_columns = [
                col for col, checkbox in self.column_mapping_widget.checkboxes.items()
                if checkbox.isChecked()
            ]

            self.table_generator.set_enabled_columns(enabled_columns)

            preset_name = self.config_widget.get_preset_name()
            background_colors_map, text_colors_map = self.presets_manager.get_style_maps(preset_name=preset_name)
            self.table_generator.set_color_maps(background_colors_map, text_colors_map)

            self.table_generator.set_scale(self.config_widget.get_scale())
            self.table_generator.set_label_width(self.config_widget.get_label_width())

            files = self.table_generator.generate_all_tables(self.processed_df, nr_zal_col)

            self.status_label.setText(f"Wygenerowano {len(files)} tabel w folderze 'tabele'")
            QMessageBox.information(self, f"Wygenerowano {len(files)} tabel w folderze 'tabele'")

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd generowania: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())