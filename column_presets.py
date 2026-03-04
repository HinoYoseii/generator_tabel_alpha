from typing import List, Dict
from dataclasses import dataclass

@dataclass
class ColumnPreset:
    """Represents a column preset configuration"""
    name: str
    columns: List[str]

class ColumnPresets:
    """Manages column preset configurations for DGI and DBP"""
    # TODO dorobić presenty kolumn dla tego hrydro idk, w sumie można to wywalić do pliku
    DBP_COLUMNS = [
        "Warunki geotechniczne",
        "Warunki wodne",
        "Grupy nośności",
        "Poziom posadowienia",
        "Poziom wzmocnienia",
        "Przydatności gruntów/skał na potrzeby budownictwa drogowego",
        "Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych",
        "Odległości",
        "Kilometraż"
    ]
    
    DGI_COLUMNS = [
        "Warunki geomorfologiczne",
        "Warunki hydrogeologiczne",
        "Warunki geologiczne",
        "Zagrożenia geologiczne",
        "Ocena warunków geologiczno-inżynierskich",
        "Prognoza zmian warunków geologiczno-inżynierskich",
        "Odległości",
        "Kilometraż"
    ]

    HYDRO_COLUMNS = [
        "Klasy podatności",
        "Jednostka Hydrogeologiczna"
    ]
    
    # Columns that are auto-generated and shouldn't be mapped
    AUTO_COLUMNS = []
    
    @classmethod
    def get_preset(cls, preset_type: str) -> List[str]:
        """Get column list for a preset type"""
        if preset_type == "DBP":
            return cls.DBP_COLUMNS.copy()
        elif preset_type == "DGI":
            return cls.DGI_COLUMNS.copy()
        elif preset_type == "HYDRO":
            return cls.HYDRO_COLUMNS.copy()
        return []
    
    @classmethod
    def get_preset_types(cls) -> List[str]:
        """Get available preset types"""
        return ["DBP", "DGI", "HYDRO"]