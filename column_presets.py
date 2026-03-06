from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "presets": [
        {
            "name": "DBP",
            "columns": [
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
            "columns": [
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
            "columns": [
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
    ],
    "auto_columns": []
}

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

class ColumnPresets: 
    def __init__(self, config_path: str = "PRESETS.json"):
        self.config_path = config_path
        self.presets: Dict[str, ColumnPreset] = {}
        self.auto_columns: List[str] = []
        self.load_from_file()
    
    def load_from_file(self):
        """Load presets from JSON configuration file"""
        if not os.path.exists(self.config_path):
            print(f"Plik konfiguracyjny {self.config_path} nie istnieje. Tworzę domyślny...")
            self._create_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "presets" in data:
                for preset_data in data["presets"]:
                    styles = None
                    if "styles" in preset_data:
                        styles = {}
                        for value, style_data in preset_data["styles"].items():
                            styles[value] = ColumnStyle(
                                text_color=style_data.get("text_color"),
                                background_color=style_data.get("background_color")
                            )
                    
                    preset = ColumnPreset(
                        name=preset_data["name"],
                        columns=preset_data["columns"],
                        styles=styles
                    )
                    self.presets[preset.name] = preset
            
            if "auto_columns" in data:
                self.auto_columns = data["auto_columns"]
            
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku konfiguracyjnego: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        
        default_config = DEFAULT_CONFIG

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"Utworzono domyślny plik konfiguracyjny: {self.config_path}")
            
            self.presets = {}
            for preset_data in default_config["presets"]:
                preset = ColumnPreset(
                    name=preset_data["name"],
                    columns=preset_data["columns"],
                    styles=preset_data.get("styles")
                )
                self.presets[preset.name] = preset
            
            self.auto_columns = default_config["auto_columns"]
            
        except Exception as e:
            print(f"Błąd podczas tworzenia domyślnego pliku konfiguracyjnego: {e}")
    
    def get_preset_columns(self, preset_name: str) -> List[str]:
        if preset_name in self.presets:
            return self.presets[preset_name].columns.copy()
        return []
    
    def get_preset_names(self) -> List[str]:
        return list(self.presets.keys())
    
    def _save_to_file(self):
        data = {
            "presets": [],
            "auto_columns": self.auto_columns
        }
        
        for preset in self.presets.values():
            preset_data = {
                "name": preset.name,
                "columns": preset.columns
            }
            if preset.styles:
                styles_data = {}
                for value, style in preset.styles.items():
                    style_data = {}
                    if style.text_color:
                        style_data["text_color"] = style.text_color
                    if style.background_color:
                        style_data["background_color"] = style.background_color
                    styles_data[value] = style_data
                preset_data["styles"] = styles_data
            
            data["presets"].append(preset_data)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Błąd podczas zapisywania pliku konfiguracyjnego: {e}")

    def get_style_maps(self, preset_name: str):
        """
        Zwraca dwa słowniki: background_color_map i text_color_map dla danego presetu z kolorami w postaci rgb
        """
        
        preset = self.presets.get(preset_name)
        
        background_color_map: Dict[str, tuple] = {}
        text_color_map: Dict[str, tuple] = {}
        
        if preset and preset.styles:
            for value, style in preset.styles.items():
                if style.background_color:
                    background_color_map[value] = tuple(style.background_color)
                if style.text_color:
                    text_color_map[value] = tuple(style.text_color)
        
        return background_color_map, text_color_map
    