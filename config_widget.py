from PyQt6.QtWidgets import *


class ConfigWidget(QGroupBox):
    def __init__(self, presets_manager, table_generator):
        super().__init__("2. Podstawowa konfiguracja")
        self.presets_manager = presets_manager
        self.table_generator = table_generator
        self._setup_ui()

    def _setup_ui(self):
        config_layout = QFormLayout()

        # Nr_zal
        self.nr_zal_combo = QComboBox()
        self.nr_zal_combo.addItem("-- Wybierz kolumnę --", None)
        self.nr_zal_combo.setEnabled(False)
        self.nr_zal_combo.setToolTip("Kolumna po której będą grupowane tabelki.")
        config_layout.addRow("Kolumna z numerami załączników/nazwami przekrojów:", self.nr_zal_combo)

        # Długości odcinków
        self.dlugosci_combo = QComboBox()
        self.dlugosci_combo.addItem("-- Wybierz kolumnę --", None)
        self.dlugosci_combo.setEnabled(False)
        self.dlugosci_combo.setToolTip("Nazwa kolumny utworzonej w skrypcie qgis, domyślnie 'length'.")
        config_layout.addRow("Kolumna z długościami podzielonych linii przekrojów:", self.dlugosci_combo)

        # Skala przekroju
        self.skala_combo = QComboBox()
        self.skala_combo.addItem("-- Wybierz skalę --", None)
        self.skala_combo.setEnabled(False)
        config_layout.addRow("Skala przekrojów:", self.skala_combo)

        # Szerokość kolumn nagłówkowych
        self.width_input = QSpinBox()
        self.width_input.setEnabled(False)
        self.width_input.setSingleStep(50)
        self.width_input.setMaximum(1000)
        self.width_input.setMinimum(50)
        self.width_input.setValue(600)
        self.width_input.setSuffix(" px")
        config_layout.addRow("Szerokość kolumn nagłówkowych:", self.width_input)

        # Wybór presetu kolumn
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("-- Wybierz preset --", None)
        self.preset_combo.addItems(self.presets_manager.get_preset_names())
        self.preset_combo.setEnabled(False)
        config_layout.addRow("Preset wierszy tabeli:", self.preset_combo)

        self.setLayout(config_layout)

    def populate_columns(self, columns):
        """Wypełnia combo boxy kolumnami z wczytanego CSV"""
        self.nr_zal_combo.clear()
        self.nr_zal_combo.addItem("-- Wybierz kolumnę --", None)
        self.nr_zal_combo.addItems(columns)
        self.nr_zal_combo.setEnabled(True)

        self.dlugosci_combo.clear()
        self.dlugosci_combo.addItem("-- Wybierz kolumnę --", None)
        self.dlugosci_combo.addItems(columns)
        self.dlugosci_combo.setEnabled(True)

        self.skala_combo.clear()
        self.skala_combo.addItem("-- Wybierz skalę --", None)
        self.skala_combo.addItems(self.table_generator.get_scale_list())
        self.skala_combo.setEnabled(True)

        self.width_input.setEnabled(True)

        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.setEnabled(True)

    def is_valid(self):
        """Zwraca True jeśli wszystkie wymagane pola są wypełnione"""
        return (
            self.preset_combo.currentIndex() > 0
            and self.nr_zal_combo.currentIndex() > 0
            and self.dlugosci_combo.currentIndex() > 0
        )

    def get_nr_zal_col(self):
        return self.nr_zal_combo.currentText()

    def get_dlugosci_col(self):
        return self.dlugosci_combo.currentText()

    def get_scale(self):
        return self.skala_combo.currentText()

    def get_label_width(self):
        return self.width_input.value()

    def get_preset_name(self):
        return self.preset_combo.currentText()