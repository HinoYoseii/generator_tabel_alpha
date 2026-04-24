from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class TableConfig:
    enabled_rows: list[str]
    bg_color_map: dict
    text_color_map: dict
    label_width: int
    scale: float | None        # None gdy skala pochodzi z kolumny
    scale_column: str | None   # None gdy skala jest stała

@dataclass
class RowStyle:
    """ Reprezentuje style kolumn """
    text_color: Optional[List[int]] = None
    background_color: Optional[List[int]] = None

@dataclass
class RowPreset:
    """ Reprezentuje preset wierszy """
    name: str
    rows: List[str]
    styles: Optional[Dict[str, RowStyle]] = None

DEFAULT_ROW_PRESETS = {
    "presets": [
        {
            "name": "DBP",
            "rows": [
                "Warunki geotechniczne",
                "Warunki wodne",
                "Grupy nośności",
                "Poziom posadowienia",
                "Poziom wzmocnienia",
                "Przydatności gruntów/skał na potrzeby budownictwa drogowego",
                "Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych",
                "Odległości",
                "Kilometraż"
            ],
            "styles": {
                "Proste": {
                    "text_color": [
                        0,
                        150,
                        0
                    ]
                },
                "Złożone": {
                    "text_color": [
                        255,
                        140,
                        0
                    ]
                },
                "Skomplikowane": {
                    "text_color": [
                        200,
                        0,
                        0
                    ]
                },
                "dobre": {
                    "text_color": [
                        0,
                        150,
                        0
                    ]
                },
                "przeciętne": {
                    "text_color": [
                        255,
                        140,
                        0
                    ]
                },
                "złe": {
                    "text_color": [
                        200,
                        0,
                        0
                    ]
                }
            }
        },
        {
            "name": "DGI",
            "rows": [
                "Warunki geomorfologiczne",
                "Warunki hydrogeologiczne",
                "Warunki geologiczne",
                "Zagrożenia geologiczne",
                "Ocena warunków geologiczno-inżynierskich",
                "Prognoza zmian warunków geologiczno-inżynierskich",
                "Odległości",
                "Kilometraż"
            ],
            "styles": {
                "Proste": {
                    "text_color": [
                        0,
                        150,
                        0
                    ]
                },
                "Złożone": {
                    "text_color": [
                        255,
                        140,
                        0
                    ]
                },
                "Skomplikowane": {
                    "text_color": [
                        200,
                        0,
                        0
                    ]
                },
                "dobre": {
                    "text_color": [
                        0,
                        150,
                        0
                    ]
                },
                "przeciętne": {
                    "text_color": [
                        255,
                        140,
                        0
                    ]
                },
                "złe": {
                    "text_color": [
                        200,
                        0,
                        0
                    ]
                }
            }
        },
        {
            "name": "HYDRO",
            "rows": [
                "Klasy podatności",
                "Jednostka Hydrogeologiczna"
            ],
            "styles": {
                "A1": {
                    "background_color": [
                        215,
                        25,
                        28
                    ]
                },
                "A2": {
                    "background_color": [
                        245,
                        144,
                        83
                    ]
                },
                "B": {
                    "background_color": [
                        254,
                        223,
                        154
                    ]
                },
                "C": {
                    "background_color": [
                        219,
                        240,
                        158
                    ]
                },
                "D": {
                    "background_color": [
                        138,
                        204,
                        98
                    ]
                }
            }
        }
    ]
}