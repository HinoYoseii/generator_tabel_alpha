import pandas as pd
from typing import List, Optional

class DataProcessor:
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.input_columns: List[str] = []
        
    def load_csv(self, file_path: str) -> bool:
        try:
            self.df = pd.read_csv(file_path)
            self.input_columns = list(self.df.columns)
            return True
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return False
    
    def get_columns(self) -> List[str]:
        return self.input_columns if self.input_columns else []
    
    @staticmethod
    def aggregate_consecutive_with_lengths(df, column, length_column):
        """
        Sumuje kolejne parametry.
        
        :param df: Dataframe z pierwotnymi danymi z Qgis.
        :param column: Nazwy kolumn do sumowania
        """
        result = []
        if len(df) == 0:
            return result
        
        current_val = df[column].iloc[0]
        current_sum = df[length_column].iloc[0]
        
        for idx in range(1, len(df)):
            val = df[column].iloc[idx]
            length = df[length_column].iloc[idx]
            
            is_current_null = pd.isna(current_val) or current_val == ''
            is_val_null = pd.isna(val) or val == ''
            
            if (is_current_null and is_val_null) or (val == current_val):
                current_sum += length
            else:
                # null na brak danych
                display_val = "brak danych" if is_current_null else current_val
                result.append((display_val, current_sum))
                current_val = val
                current_sum = length
        
        is_current_null = pd.isna(current_val) or current_val == ''
        display_val = "brak danych" if is_current_null else current_val
        result.append((display_val, current_sum))
        return result
    
    def process_data(self, nr_zal_column: str,column_mapping: dict, length_column: str) -> pd.DataFrame:

        if self.df is None:
            raise ValueError("No data loaded")
        
        kilometraz_column = column_mapping.get("Kilometraż")
        
        columns_needed = [nr_zal_column, length_column] + [
            col for col in column_mapping.values() if col
        ]
        working_df = self.df[columns_needed].copy()
        
        result_rows = []
        
        for nr_zal, group in working_df.groupby(nr_zal_column, sort=False):
            group = group.reset_index(drop=True)
            total_length = group[length_column].sum()
            
            aggregated = {}
            for output_col, input_col in column_mapping.items():
                if input_col:
                    aggregated[output_col] = self.aggregate_consecutive_with_lengths(group, input_col, length_column)
            
            if kilometraz_column:
                aggregated["Odległości"] = aggregated.get("Kilometraż", [])
            
            max_rows = max(len(agg) for agg in aggregated.values()) if aggregated else 1
            
            for i in range(max_rows):
                row = {nr_zal_column: nr_zal}
                
                for output_col, agg_data in aggregated.items():
                    if output_col == "Odległości":
                        if i < len(agg_data):
                            row["Odległości"] = f"{agg_data[i][1]}m"
                            row["Odległości len"] = agg_data[i][1]
                        else:
                            row["Odległości"] = ''
                            row["Odległości len"] = ''
                    else:
                        row[output_col] = agg_data[i][0] if i < len(agg_data) else ''
                        row[f"{output_col} len"] = agg_data[i][1] if i < len(agg_data) else ''
                
                result_rows.append(row)
        
        return pd.DataFrame(result_rows)