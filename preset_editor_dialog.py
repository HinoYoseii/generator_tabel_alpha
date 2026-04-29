from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon


class PresetEditorDialog(QDialog):
    Deleted = 2

    def __init__(self, presets_manager, preset_name: str | None = None, parent=None):
        super().__init__(parent)
        self.presets_manager = presets_manager
        self.editing_name = preset_name
        self.row_inputs: list[QLineEdit] = []

        title = f"Edytuj preset — {preset_name}" if preset_name else "Nowy preset"
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setMinimumHeight(400)
        self._setup_ui()

        if preset_name:
            self._load_preset(preset_name)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Nazwa presetu:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Podaj nazwę presetu...")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Wiersze tabeli:"))
        add_btn = QPushButton("+ Dodaj wiersz")
        add_btn.setFlat(True)
        add_btn.clicked.connect(lambda: self._add_row_input(""))
        row_layout.addWidget(add_btn)
        layout.addLayout(row_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setSpacing(6)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.rows_container)
        layout.addWidget(self.scroll_area)

        btn_layout = QHBoxLayout()

        if self.editing_name:
            delete_btn = QPushButton("Usuń preset")
            delete_btn.setToolTip(f"Trwale usuń preset '{self.editing_name}'")
            delete_btn.clicked.connect(self._delete_preset)
            btn_layout.addWidget(delete_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Anuluj")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Zapisz")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _add_row_input(self, text: str):
        row_widget = QWidget()
        row_h = QHBoxLayout(row_widget)
        row_h.setContentsMargins(0, 0, 0, 0)
        row_h.setSpacing(4)

        line = QLineEdit(text)
        line.setPlaceholderText("Nazwa wiersza...")
        row_h.addWidget(line)

        remove_btn = QToolButton()
        remove_btn.setText("✕")
        remove_btn.setFixedSize(26, 26)
        remove_btn.setToolTip("Usuń wiersz")
        remove_btn.clicked.connect(lambda: self._remove_row(row_widget, line))
        row_h.addWidget(remove_btn)

        self.rows_layout.addWidget(row_widget)
        self.row_inputs.append(line)
        line.setFocus()

    def _remove_row(self, row_widget: QWidget, line: QLineEdit):
        self.row_inputs.remove(line)
        row_widget.deleteLater()
    
    def _delete_preset(self):
        reply = QMessageBox.warning(
            self,
            "Usuń preset",
            f"Czy na pewno chcesz trwale usunąć preset '{self.editing_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.presets_manager.delete_preset(self.editing_name)
            self.done(PresetEditorDialog.Deleted)

    def _load_preset(self, name: str):
        self.name_input.setText(name)
        rows = self.presets_manager.get_preset_rows(name)
        for row in rows:
            self._add_row_input(row)

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Błąd", "Podaj nazwę presetu.")
            return

        rows = [i.text().strip() for i in self.row_inputs if i.text().strip()]
        if not rows:
            QMessageBox.warning(self, "Błąd", "Preset musi zawierać co najmniej jeden wiersz.")
            return
        if len(rows) != len(set(rows)):
            QMessageBox.warning(self, "Błąd", "Nazwy kolumn w presecie nie mogą się powtarzać.")
            return

        existing = self.presets_manager.get_preset_names()

        if self.editing_name and self.editing_name != name:
            if name in existing:
                QMessageBox.warning(self, "Błąd", f"Preset o nazwie '{name}' już istnieje.")
                return
            self.presets_manager.delete_preset(self.editing_name)

        elif not self.editing_name and name in existing:
            QMessageBox.warning(self, "Błąd", f"Preset o nazwie '{name}' już istnieje.")
            return

        self.presets_manager.save_preset(name, rows)
        self.accept()

    def get_saved_name(self) -> str:
        return self.name_input.text().strip()