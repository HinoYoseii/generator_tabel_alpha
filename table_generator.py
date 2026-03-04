import math
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from typing import Dict, List, Tuple
import os

class TableGenerator:
    
    def __init__(self, output_dir: str = "tabele", preset_columns: list = None):
        self.output_dir = output_dir
        self.preset_columns = preset_columns or []
        self.scale = 2.5
        self.row_height = 40
        self.margin = 20
        self.label_width = 600
        self.font_size = 18
        
        # Kolory dla określonych wartości
        self.color_map = {
            "Proste": (0, 150, 0),
            "Złożone": (255, 140, 0),
            "Skomplikowane": (200, 0, 0),
            "dobre": (0, 150, 0),
            "przeciętne": (255, 140, 0),
            "złe": (200, 0, 0)
        }
        
        os.makedirs(output_dir, exist_ok=True)
        self.font = self._load_font()
    
    def _load_font(self):
        """Ładuje czcionkę obsługującą polskie znaki"""
        try:
            return ImageFont.truetype("arial.ttf", self.font_size)
        except:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", self.font_size)
            except:
                print("Uwaga: Nie udało się załadować wybranej czcionkifont nie obsługuje polskich znaków!")
                return ImageFont.load_default()
    
    @staticmethod
    def clean_segments(name_series, len_series) -> List[Tuple[str, float]]:
        """Wyczyść i przygotuj segmenty do rysowania"""
        segments = []
        for name, length in zip(name_series, len_series):
            if pd.isna(name) or pd.isna(length):
                continue
            try:
                length = float(length)
                if math.isnan(length):
                    continue
            except:
                continue
            segments.append((str(name), length))
        return segments
    
    def generate_table(self, group_df: pd.DataFrame, nr_zal_value: str) -> str:
        row_segments = self._prepare_row_segments(group_df)
        
        max_width = max(
            sum(length for _, length in segments) * self.scale if segments else 0
            for segments in row_segments.values()
        )
        
        img_width = int(self.label_width + max_width + 2 * self.margin)
        img_height = len(row_segments) * self.row_height + 2 * self.margin

        img = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)
        
        self._draw_rows(draw, row_segments, max_width)
        
        safe_nr_zal = str(nr_zal_value).replace('.', '_').replace('/', '_')
        filename = os.path.join(self.output_dir, f"tabela_{safe_nr_zal}.jpg")
        img.save(filename, quality=95)
        
        return filename
    
    def set_preset_columns(self, preset_columns: list):
        """Ustawia kolumny presetu do użycia przy generowaniu tabeli"""
        self.preset_columns = preset_columns
    
    def _prepare_row_segments(self, group_df: pd.DataFrame) -> Dict[str, List[Tuple[str, float]]]:
        """Przygotowuje segmenty dla wszystkich wierszy do rysowania"""
        row_segments = {}
        
        columns_to_draw = []
        
        for col in self.preset_columns:
            columns_to_draw.append((f"{col}:", col))
        
        for label, col_name in columns_to_draw:
            if col_name in group_df.columns and f"{col_name} len" in group_df.columns:
                segments = self.clean_segments(
                    group_df[col_name],
                    group_df[f"{col_name} len"]
                )
                if segments: 
                    row_segments[label] = segments
        
        return row_segments
    
    def _draw_rows(self, draw: ImageDraw, row_segments: Dict[str, List], max_width: float):
        """Rysuje wszystkie wiersze na obrazie"""
        y = self.margin
        
        for row_name, segments in row_segments.items():
            total_row_width = max_width

            draw.rectangle(
                [self.margin, y, 
                 self.margin + self.label_width + total_row_width, 
                 y + self.row_height],
                outline="black",
                width=1
            )
            
            self._draw_text(draw, row_name, 
                          self.margin, y, 
                          self.label_width, self.row_height)
            
            x = self.margin + self.label_width
            for name, length in segments:
                if not name or length <= 0 or math.isnan(length):
                    continue
                
                width_px = int(length * self.scale)
                
                draw.rectangle([x, y, x + width_px, y + self.row_height],
                             outline="black", fill="white", width=1)
                
                text_color = self.color_map.get(name, (0, 0, 0))
                self._draw_text(draw, str(name), 
                              x, y, 
                              width_px, self.row_height,
                              fill=text_color)
                
                x += width_px
            
            y += self.row_height
    
    def _draw_text(self, draw: ImageDraw, text: str, x: int, y: int, width: int, height: int, fill=(0, 0, 0)):
        """Rysuje wyśrodkowany tekst w podanym prostokącie"""
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = x + (width - text_width) / 2
        text_y = y + (height - text_height) / 2
        
        draw.text((int(text_x), int(text_y)), text, fill=fill, font=self.font)
    
    def generate_all_tables(self, df: pd.DataFrame, nr_zal_column: str) -> List[str]:
        generated_files = []
        
        for nr_zal, group in df.groupby(nr_zal_column, sort=False):
            try:
                filename = self.generate_table(group, nr_zal)
                generated_files.append(filename)
                print(f"Zapisano: {filename}")
            except Exception as e:
                print(f"Błąd przy generowaniu tabeli dla {nr_zal}: {e}")
        
        return generated_files