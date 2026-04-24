from typing import List, Dict
import json
import os
from models import RowPreset, RowStyle, DEFAULT_ROW_PRESETS

class PresetManager: 
    def __init__(self, config_path: str = "data/PRESETS.json"):
        self.config_path = config_path
        self.presets: Dict[str, RowPreset] = {}
        self.load_from_file()
    
    def load_from_file(self):
        """Wczytuje presety z pliku PRESETS.json"""
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
                            styles[value] = RowStyle(
                                text_color=style_data.get("text_color"),
                                background_color=style_data.get("background_color")
                            )
                    
                    preset = RowPreset(
                        name=preset_data["name"],
                        rows=preset_data["rows"],
                        styles=styles
                    )
                    self.presets[preset.name] = preset
            
        except Exception as e:
            print(f"Błąd podczas wczytywania pliku konfiguracyjnego: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        
        default_config = DEFAULT_ROW_PRESETS

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"Utworzono domyślny plik konfiguracyjny: {self.config_path}")
            
            self.presets = {}
            for preset_data in default_config["presets"]:
                preset = RowPreset(
                    name=preset_data["name"],
                    rows=preset_data["rows"],
                    styles=preset_data.get("styles")
                )
                self.presets[preset.name] = preset
            
        except Exception as e:
            print(f"Błąd podczas tworzenia domyślnego pliku konfiguracyjnego: {e}")
    
    def get_preset_rows(self, preset_name: str) -> List[str]:
        if preset_name in self.presets:
            return self.presets[preset_name].rows.copy()
        return []
    
    def get_preset_names(self) -> List[str]:
        return list(self.presets.keys())
    
    def _save_to_file(self):
        data = {
            "presets": []
        }
        
        for preset in self.presets.values():
            preset_data = {
                "name": preset.name,
                "rows": preset.rows
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
        """Zwraca dwa słowniki: background_color_map i text_color_map dla danego presetu z kolorami w postaci rgb"""
        
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

    def save_preset(self, name: str, rows: List[str]):
        existing = self.presets.get(name)
        self.presets[name] = RowPreset(
            name=name,
            rows=rows,
            styles=existing.styles if existing else None
        )
        self._save_to_file()

    def delete_preset(self, name: str):
        if name in self.presets:
            del self.presets[name]
            self._save_to_file()