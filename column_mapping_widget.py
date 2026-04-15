from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QGroupBox, QCheckBox, QComboBox, QLabel
)

class ColumnMappingWidget(QWidget):
    """Widget do mapowania kolumn."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.combos: dict[str, QComboBox] = {}

        self._main_layout = QVBoxLayout(self)
        self.info_label = QLabel("")
        self._main_layout.addWidget(self.info_label)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._main_layout.addWidget(self._scroll_area)

    def setup_columns(self, preset_columns: list[str], input_columns: list[str], clear_info: bool = False) -> None:
        self.combos.clear()
        if clear_info:
            self.info_label.setText("")

        container = QWidget()
        layout = QVBoxLayout(container)
        for col in preset_columns:
            layout.addWidget(self._make_column_row(col, input_columns))
        layout.addStretch()
        self._scroll_area.setWidget(container)

    def _make_column_row(self, col: str, input_columns: list[str]) -> QGroupBox:
        group = QGroupBox(col)
        row = QHBoxLayout(group)
        combo = QComboBox()
        combo.addItem("-- Pomiń --", None)
        for input_col in input_columns:
            combo.addItem(input_col, input_col)
        self.combos[col] = combo
        row.addWidget(combo)
        return group

    def get_column_mapping(self) -> dict[str, str]:
        return {
            col: combo.currentData()
            for col, combo in self.combos.items()
            if combo.currentData() is not None
        }