from PyQt6.QtWidgets import *
from PyQt6.QtCore import pyqtSignal

from preset_editor_dialog import PresetEditorDialog

class ConfigWidget(QGroupBox):
    preset_changed = pyqtSignal()
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

        # Preset combo + edit/new buttons in a single row widget
        preset_row = QWidget()
        preset_h = QHBoxLayout(preset_row)
        preset_h.setContentsMargins(0, 0, 0, 0)
        preset_h.setSpacing(4)

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("-- Wybierz preset --", None)
        self.preset_combo.addItems(self.presets_manager.get_preset_names())
        self.preset_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        preset_h.addWidget(self.preset_combo)

        self.edit_preset_btn = QToolButton()
        self.edit_preset_btn.setText("✎")
        self.edit_preset_btn.setFixedSize(28, 28)
        self.edit_preset_btn.setToolTip("Edytuj wybrany preset")
        self.edit_preset_btn.clicked.connect(self._open_edit_preset)
        self.edit_preset_btn.setEnabled(False)
        preset_h.addWidget(self.edit_preset_btn)

        self.new_preset_btn = QToolButton()
        self.new_preset_btn.setText("+")
        self.new_preset_btn.setFixedSize(28, 28)
        self.new_preset_btn.setToolTip("Utwórz nowy preset")
        self.new_preset_btn.clicked.connect(self._open_new_preset)
        preset_h.addWidget(self.new_preset_btn)

        config_layout.addRow("Preset wierszy tabeli:", preset_row)

        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        self.setLayout(config_layout)

    def _on_preset_changed(self, index: int):
        self.edit_preset_btn.setEnabled(index > 0)

    def _open_edit_preset(self):
        name = self.preset_combo.currentText()
        if not name or self.preset_combo.currentIndex() == 0:
            return
        dlg = PresetEditorDialog(self.presets_manager, preset_name=name, parent=self)
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            self._refresh_preset_combo(select_name=dlg.get_saved_name())
        elif result == PresetEditorDialog.Deleted:
            self._refresh_preset_combo()
        self.preset_changed.emit()  # always emit, main window decides what to do

    def _open_new_preset(self):
        dlg = PresetEditorDialog(self.presets_manager, preset_name=None, parent=self)
        result = dlg.exec()
        if result == QDialog.DialogCode.Accepted:
            self._refresh_preset_combo(select_name=dlg.get_saved_name())
        self.preset_changed.emit()  # always emit

    def _refresh_preset_combo(self, select_name: str | None = None):
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("-- Wybierz preset --", None)
        self.preset_combo.addItems(self.presets_manager.get_preset_names())
        if select_name:
            idx = self.preset_combo.findText(select_name)
            self.preset_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.preset_combo.blockSignals(False)
        self._on_preset_changed(self.preset_combo.currentIndex())

    def populate_columns(self, columns):
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
        # Dodaj separator i kolumny CSV
        self.skala_combo.insertSeparator(self.skala_combo.count())
        for col in columns:
            self.skala_combo.addItem(f"[kolumna] {col}", f"__col__:{col}")
        self.skala_combo.setEnabled(True)

        self.width_input.setEnabled(True)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.setEnabled(True)
        self.new_preset_btn.setEnabled(True)

    def get_scale(self):
        """Zwraca nazwę skali preset lub '__col__:nazwa_kolumny'"""
        data = self.skala_combo.currentData()
        if data:
            return data
        return self.skala_combo.currentText()

    def is_scale_from_column(self) -> bool:
        data = self.skala_combo.currentData()
        return isinstance(data, str) and data.startswith("__col__:")

    def get_scale_column(self) -> str | None:
        if self.is_scale_from_column():
            return self.skala_combo.currentData()[len("__col__:"):]
        return None

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