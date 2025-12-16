import math
from PIL import Image, ImageDraw, ImageFont
import pandas as pd

df = pd.read_csv("output.csv")

def clean_segments(name_series, len_series):
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

def draw(group_df, nr_zal_value):
    row_segments = {
        "Charakterystyka drogi:": clean_segments(group_df["Charakterystyka drogi"], group_df["Charakterystyka drogi len"]),
        "Warunki geotechniczne:": clean_segments(group_df["Warunki geotechniczne"], group_df["Warunki geotechniczne len"]),
        "Warunki wodne:": clean_segments(group_df["Warunki wodne"], group_df["Warunki wodne len"]),
        "Grupy nośności:": clean_segments(group_df["Grupy nośności"], group_df["Grupy nośności len"]),
        "Poziom posadowienia:": clean_segments(group_df["Poziom posadowienia"], group_df["Poziom posadowienia len"]),
        "Poziom wzmocnienia:": clean_segments(group_df["Poziom wzmocnienia"], group_df["Poziom wzmocnienia len"]),
        "Przydatności gruntów/skał na potrzeby budownictwa drogowego:": clean_segments(group_df["Przydatności gruntów/skał na potrzeby budownictwa drogowego"], group_df["Przydatności gruntów/skał na potrzeby budownictwa drogowego len"]),
        "Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych:": clean_segments(group_df["Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych"], group_df["Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych len"]),
        "Odległości:": clean_segments(group_df["Odległości"], group_df["Odległości len"]),
        "Kilometraż:": clean_segments(group_df["Kilometraż"], group_df["Kilometraż len"])
    }

    scale = 10
    row_height = 40
    margin = 20
    label_width = 600
    font_size = 18

    color_map = {
        "Proste": (0, 150, 0),       
        "Złożone": (255, 140, 0),     
        "Skomplikowane": (200, 0, 0),
        "dobre": (0, 150, 0),  
        "przeciętne": (255, 140, 0),
        "złe": (200, 0, 0)
    }

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except:
            font = ImageFont.load_default()
            print("Uwaga: font nie obsługuje polskich znaków!")

    # 4. Wymiary obrazu
    max_width = max(
        (sum(length for _, length in segments) * scale if segments else 0
        for segments in row_segments.values()),
        default=0  # This ensures max() doesn't fail on empty iterables
    )

    img_width = int(label_width + max_width + 2 * margin)
    img_height = len(row_segments) * row_height + 2 * margin

    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # 5. Rysowanie segmentów i podpisów
    y = margin
    for row_name, segments in row_segments.items():

        total_row_width = max_width  

        draw.rectangle(
            [margin, y, margin + label_width + total_row_width, y + row_height],
            outline="black",
            width=1
        )

        # Podpis wiersza
        text = f"{row_name}"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        text_x = margin + (label_width - tw) / 2
        text_y = y + (row_height - th) / 2
        draw.text((int(text_x), int(text_y)), text, fill="black", font=font)

        # Segmenty
        x = margin + label_width
        for name, length in segments:
            if not name or length <= 0:
                continue  # ignorujemy puste lub 0

            if math.isnan(length):
                length = 0
                continue

            width_px = int(length * scale)
            box = [x, y, x + width_px, y + row_height]
            draw.rectangle(box, outline="black", fill="white", width=1)

            # Tekst w segmencie
            text_color = color_map.get(name, (0, 0, 0)) 
            text = str(name)
            bbox = draw.textbbox((0, 0), text, font=font)
            tw_seg = bbox[2] - bbox[0]
            th_seg = bbox[3] - bbox[1]
            draw.text(
                (int(x + (width_px - tw_seg) / 2), int(y + (row_height - th_seg) / 2)),
                text,
                fill=text_color,
                font=font
            )
            x += width_px

        y += row_height

    filename = f"tabele/tabela_{nr_zal_value}.jpg"
    img.save(filename, quality=600)
    print(f"Zapisano: {filename}")

for nr_zal, group in df.groupby('nr_zal', sort=False):
    safe_nr_zal = str(nr_zal).replace('.', '_').replace('/', '_')
    draw(group, safe_nr_zal)