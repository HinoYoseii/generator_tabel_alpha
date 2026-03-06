from PyQt6.QtWidgets import *
from column_presets import ColumnPresets

class ColumnMappingWidget(QWidget):
    """ Widget do mapowania kolumn """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mappings = {}
        self.checkboxes = {}
        self.combos = {}
        self.layout = QVBoxLayout(self)
        self.info_label = QLabel("")
        self.setup_columns([], [], clear_info=True)
        
    def setup_columns(self, preset_columns: list, input_columns: list, clear_info=False):
        """ Setup kolumn do mapowania kolumn wejściowych i kolumn z presetu """
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.mappings.clear()
        self.checkboxes.clear()
        self.combos.clear()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # auto_columns = ColumnPresets.AUTO_COLUMNS
        
        for col in preset_columns:
            # Tworzy group box dla każdej kolumny
            group = QGroupBox(col)
            group_layout = QHBoxLayout()
            
            # Checbox do włączania/wyłączania mapowania kolumny
            enable_check = QCheckBox("Włącz")
            enable_check.setChecked(True)
            self.checkboxes[col] = enable_check
            
            # Combo box z kolumnami wejściowymi z CSV
            combo = QComboBox()
            combo.addItem("-- Wybierz kolumnę --", None)
            for input_col in input_columns:
                combo.addItem(input_col, input_col)
            self.combos[col] = combo

            # Połączenie sygnału checkboxa z włączaniem/wyłączaniem combo boxa
            def make_toggle(c):
                return lambda checked: (c.setEnabled(checked))
            enable_check.toggled.connect(make_toggle(combo))

            group_layout.addWidget(enable_check)
            group_layout.addWidget(combo, stretch=2)
            group.setLayout(group_layout)
            
            scroll_layout.addWidget(group)
        
        # # Informacja o kolumnach automatycznych
        # if auto_columns and not clear_info:
        #     self.info_label = QLabel(f"Kolumny {auto_columns} są generowane automatycznie na podstawie innych kolumn więc nie wymagają przypisania.")
        #     scroll_layout.addWidget(self.info_label)
            
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        self.layout.addWidget(scroll)
    
    def get_column_mapping(self):
        """ Pobiera aktualne mapowanie kolumn do słownika"""
        mapping = {}
        for col, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                combo = self.combos[col]
                selected = combo.currentData()
                if selected:
                    mapping[col] = selected
        return mapping