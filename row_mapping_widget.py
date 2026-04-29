from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QComboBox, QLabel,
    QLineEdit, QPushButton, QButtonGroup, QSizePolicy, QFrame
)

class MyComboBox(QComboBox):
    """ComboBox ale bez scrolla"""
    def wheelEvent(self, event):
        event.ignore()

class RowMappingWidget(QScrollArea):
    """Widget do mapowania kolumn."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self._rows: dict[str, tuple[MyComboBox, QLineEdit, QButtonGroup]] = {}

    @property
    def combos(self) -> dict[str, MyComboBox]:
        return {row: data[0] for row, data in self._rows.items()}

    def setup_rows(self, preset_rows: list[str], input_columns: list[str]) -> None:
        self._rows.clear()

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(10)
        for row in preset_rows:
            layout.addWidget(self._make_mapping_row(row, input_columns))
        layout.addStretch()
        self.setWidget(container)

    def _make_mapping_row(self, row: str, input_columns: list[str]) -> QWidget:
        widget = QWidget()
        row_layout = QVBoxLayout(widget)
        row_layout.setContentsMargins(0, 2, 0, 2)

        label = QLabel(row)
        row_layout.addWidget(label)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        btn_map = QPushButton("Kolumna")
        btn_val = QPushButton("Stała wartość")
        for btn in (btn_map, btn_val):
            btn.setCheckable(True)
            btn.setFixedHeight(26)

        btn_group = QButtonGroup(widget)
        btn_group.setExclusive(True)
        btn_group.addButton(btn_map, id=0)
        btn_group.addButton(btn_val, id=1)
        btn_map.setChecked(True)

        controls.addWidget(btn_map)
        controls.addWidget(btn_val)

        combo = MyComboBox()
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        combo.addItem("-- Pomiń --", None)
        for input_col in input_columns:
            combo.addItem(input_col, input_col)
        controls.addWidget(combo)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("Wpisz wartość…")
        line_edit.setVisible(False)
        controls.addWidget(line_edit)
        
        row_layout.addLayout(controls)

        self._rows[row] = (combo, line_edit, btn_group)

        def on_mode_changed(btn_id: int) -> None:
            combo.setVisible(btn_id == 0)
            line_edit.setVisible(btn_id == 1)

        btn_group.idClicked.connect(on_mode_changed)

        return widget

    def get_row_mapping(self) -> dict[str, str | None]:
        result: dict[str, str | None] = {}
        for row, (combo, line_edit, btn_group) in self._rows.items():
            if btn_group.checkedId() == 1:
                text = line_edit.text()
                if text:
                    result[row] = f"__const__:{text}"  # tag stałej wartości
            else:
                mapped = combo.currentData()
                if mapped is not None:
                    result[row] = mapped
        return result