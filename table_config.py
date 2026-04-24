from dataclasses import dataclass, field

@dataclass
class TableConfig:
    enabled_columns: list[str]
    bg_color_map: dict
    text_color_map: dict
    label_width: int
    scale: float | None        # None gdy skala pochodzi z kolumny
    scale_column: str | None   # None gdy skala jest stała