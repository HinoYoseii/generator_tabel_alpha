from PIL import Image, ImageDraw, ImageFont
from typing import Dict, List, Tuple
from models import TableConfig
import math
import os
import pandas as pd

class TableGenerator:
    def __init__(self):
        self.output_dir = "tabele"
        self.enabled_rows = []
        self.row_height = 40
        self.font_size = 18
        self.margin = 20
        self.label_width = 300
        self.scale = 4
        self.scale_column = None
        self.font = self._load_font()

        self.background_color_map = {}
        self.text_color_map = {}
        self.scale_map = {
            "1:1000":10,
            "1:2500":4,
            "1:8000":1.25
        }

    def set_scale_column(self, col: str | None):
        self.scale_column = col
    
    def get_scale_list(self) -> List[str]:
        return list(self.scale_map.keys()) if self.scale_map else []
    
    def set_enabled_rows(self, enabled_rows: list):
        self.enabled_rows = enabled_rows
    
    def set_color_maps(self, background_colors:dict, text_colors: dict):
        self.background_color_map = background_colors
        self.text_color_map = text_colors
    
    def set_label_width(self, label_width:int):
        self.label_width = label_width

    def set_scale(self, scale):
        self.scale = self.scale_map.get(scale)
    
    def _load_font(self):
        """Ładuje czcionkę obsługującą polskie znaki"""
        try:
            return ImageFont.truetype("arial.ttf", self.font_size)
        except:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", self.font_size)
            except:
                print("Uwaga: Nie udało się załadować wybranej czcionki.")
                return ImageFont.load_default()
    
    @staticmethod
    def _clean_segments(name_series, len_series) -> List[Tuple[str, float]]:
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
    
    def _prepare_row_segments(self, group_df: pd.DataFrame, enabled_rows: list[str]) -> Dict[str, List[Tuple[str, float]]]:
        row_segments = {}
        for col in enabled_rows:
            label = f"{col}:"
            if col in group_df.columns and f"{col} len" in group_df.columns:
                segments = self._clean_segments(group_df[col], group_df[f"{col} len"])
                if segments:
                    row_segments[label] = segments
        return row_segments
    
    def _draw_rows(self, draw: ImageDraw, row_segments: Dict[str, List], max_width: float, config: TableConfig, scale: float):
        y = self.margin
        
        for row_name, segments in row_segments.items():
            draw.rectangle(
                [self.margin, y,
                self.margin + config.label_width + max_width,
                y + self.row_height],
                outline="black",
                width=1
            )
            
            self._draw_text(draw, row_name,
                        self.margin, y,
                        config.label_width, self.row_height)
            
            x = self.margin + config.label_width
            for name, length in segments:
                if not name or length <= 0 or math.isnan(length):
                    continue
                
                width_px = int(length * scale)
                
                background_color = config.bg_color_map.get(name, (255, 255, 255))
                draw.rectangle([x, y, x + width_px, y + self.row_height], outline="black", fill=background_color, width=1)
                
                text_color = config.text_color_map.get(name, (0, 0, 0))
                self._draw_text(draw, str(name), x, y, width_px, self.row_height, fill=text_color)
                
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

    def generate_table(self, group_df: pd.DataFrame, nr_zal_value: str, config: TableConfig) -> str:
        # Skala
        if config.scale_column and config.scale_column in group_df.columns:
            raw = group_df[config.scale_column].iloc[0]
            try:
                scale = 10000 / float(raw)
            except (ValueError, ZeroDivisionError):
                scale = self.scale  # fallback
        else:
            scale = self.scale_map.get(config.scale, config.scale)  # nazwa -> liczba lub liczba wprost

        row_segments = self._prepare_row_segments(group_df, config.enabled_rows)

        max_width = max(
            (sum(l for _, l in segs) * scale for segs in row_segments.values() if segs),
            default=0
        )

        img_width = int(config.label_width + max_width + 2 * self.margin)
        img_height = len(row_segments) * self.row_height + 2 * self.margin

        img = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)
        self._draw_rows(draw, row_segments, max_width, config, scale)

        safe = str(nr_zal_value).replace('.', '_').replace('/', '_')
        filename = os.path.join(self.output_dir, f"{safe}.jpg")
        img.save(filename, quality=95)
        return filename

    def generate_all_tables(self, df: pd.DataFrame, nr_zal_column: str, config: TableConfig) -> list[str]:
        generated_files = []
        os.makedirs(self.output_dir, exist_ok=True)
        for nr_zal, group in df.groupby(nr_zal_column, sort=False):
            try:
                generated_files.append(self.generate_table(group, nr_zal, config))
            except Exception as e:
                import traceback
                print(f"Błąd przy generowaniu tabeli dla {nr_zal}: {e}")
                traceback.print_exc()
        return generated_files