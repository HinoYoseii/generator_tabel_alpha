import pandas as pd

def aggregate_consecutive_with_lengths(df, column, use_brak_danych=False):
    """
    Sumuje kolejne parametry.
    
    :param df: Dataframe z pierwotnymi danymi z Qgis.
    :param column: Nazwy kolumn do 
    :param use_brak_danych: Description
    """
    result = []
    if len(df) == 0:
        return result
    
    current_val = df[column].iloc[0]
    current_sum = df['length'].iloc[0]
    
    for idx in range(1, len(df)):
        val = df[column].iloc[idx]
        length = df['length'].iloc[idx]
        
        is_current_null = pd.isna(current_val) or current_val == ''
        is_val_null = pd.isna(val) or val == ''
        
        if (is_current_null and is_val_null) or (val == current_val):
            current_sum += length
        else:
            # null na brak danych
            display_val = "brak danych" if (use_brak_danych and is_current_null) else current_val
            result.append((display_val, current_sum))
            current_val = val
            current_sum = length
    
    is_current_null = pd.isna(current_val) or current_val == ''
    display_val = "brak danych" if (use_brak_danych and is_current_null) else current_val
    result.append((display_val, current_sum))
    return result

df = pd.read_csv("dane.csv")
input_column_names = ["nr_zal", "length", "sko_war_gr", "war_wod", "gr_nosnosc", "poz_posado", "poz_wzmocn", "przyd_budo", "przyd_wyko", "kilometraz"]
brak_danych_columns = ["poz_posado", "poz_wzmocn", "przyd_budo", "przyd_wyko"]
df = df[input_column_names]

output_column_names = [
    "nr_zal",
    "Charakterystyka drogi",
    "Charakterystyka drogi len",
    "Warunki geotechniczne",
    "Warunki geotechniczne len",
    "Warunki wodne",
    "Warunki wodne len",
    "Grupy nośności",
    "Grupy nośności len",
    "Poziom posadowienia",
    "Poziom posadowienia len",
    "Poziom wzmocnienia",
    "Poziom wzmocnienia len",
    "Przydatności gruntów/skał na potrzeby budownictwa drogowego",
    "Przydatności gruntów/skał na potrzeby budownictwa drogowego len",
    "Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych",
    "Przydatności gruntów/skał z wykopów do wykonania budowli ziemnych len",
    "Odległości",
    "Odległości len",
    "Kilometraż",
    "Kilometraż len"
]

result_rows = []

for nr_zal, group in df.groupby('nr_zal', sort=False):
    # Reset index to ensure proper iteration
    group = group.reset_index(drop=True)

    total_length = group['length'].sum()
    # Aggregate consecutive values for each column (skip nr_zal and length)
    aggregated = [
        aggregate_consecutive_with_lengths(group, column, use_brak_danych=(column in brak_danych_columns))
        for column in input_column_names[2:]
    ]

    # Determine maximum rows needed
    max_rows = max(len(agg) for agg in aggregated)

    # Create rows for this nr_zal
    for i in range(max_rows):
        row = {'nr_zal': nr_zal}

        if i == 0:
            row["Charakterystyka drogi"] = "klasa drogi: S; kategoria ruchu: KR6; długość projektowanej drogi: 14,7 km"
            row["Charakterystyka drogi len"] = total_length
        else:
            row["Charakterystyka drogi"] = ''
            row["Charakterystyka drogi len"] = ''
        
        # Iterate through aggregated data and corresponding output column names
        for j, agg in enumerate(aggregated):
            input_col = input_column_names[2 + j]  # Get the input column name
            value_col = output_column_names[3 + j * 2]  # 1, 3, 5, 7...
            len_col = output_column_names[4 + j * 2]    # 2, 4, 6, 8...
            
            # Special handling for kilometraz
            if input_col == "kilometraz":
                # Kilometraż uses the value from kilometraz
                row["Kilometraż"] = agg[i][0] if i < len(agg) else ''
                row["Kilometraż len"] = agg[i][1] if i < len(agg) else ''
                
                # Odległości uses the length + "m"
                if i < len(agg):
                    row["Odległości"] = f"{agg[i][1]}m"
                    row["Odległości len"] = agg[i][1]
                else:
                    row["Odległości"] = ''
                    row["Odległości len"] = ''

            else:
                # Normal handling for other columns
                row[value_col] = agg[i][0] if i < len(agg) else ''
                row[len_col] = agg[i][1] if i < len(agg) else ''
        
        result_rows.append(row)

# Create result DataFrame
result_df = pd.DataFrame(result_rows)

# Save to CSV
result_df.to_csv('output.csv', index=False)
result_df.to_excel('output.xlsx', index=False)