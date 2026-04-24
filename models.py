from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TableConfig:
    enabled_columns: list[str]
    bg_color_map: dict
    text_color_map: dict
    label_width: int
    scale: float | None        # None gdy skala pochodzi z kolumny
    scale_column: str | None   # None gdy skala jest stała

@dataclass
class ColumnStyle:
    """ Reprezentuje style kolumn """
    text_color: Optional[List[int]] = None
    background_color: Optional[List[int]] = None

@dataclass
class ColumnPreset:
    """ Reprezentuje preset kolumn (w sumie to wierszy tabeli lol ale ok) """
    name: str
    columns: List[str]
    styles: Optional[Dict[str, ColumnStyle]] = None