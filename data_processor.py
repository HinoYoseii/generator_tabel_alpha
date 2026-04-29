import pandas as pd
from typing import List, Optional

class DataProcessor:
    def __init__(self):
        self.df: pd.DataFrame = None
        self.input_columns: List[str] = []
        
    def load_csv(self, file_path: str) -> bool:
        try:
            self.df = pd.read_csv(file_path)
            self.input_columns = list(self.df.columns)
            return True
        except Exception as e:
            print(f"Błąd wczytywania piku csv: {e}")
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
        
        def to_scalar(val):
            """Zawsze używa skalara"""
            if isinstance(val, pd.Series):
                val = val.iloc[0]
            return val

        current_val = to_scalar(df[column].iloc[0])
        current_sum = to_scalar(df[length_column].iloc[0])
        
        for idx in range(1, len(df)):
            val = to_scalar(df[column].iloc[idx])
            length = to_scalar(df[length_column].iloc[idx])
            
            is_current_null = pd.isna(current_val) or current_val == ''
            is_val_null = pd.isna(val) or val == ''
            
            both_null = is_current_null and is_val_null
            both_equal = (not is_current_null and not is_val_null and val == current_val)
            
            if both_null or both_equal:
                current_sum += length
            else:
                display_val = "brak danych" if is_current_null else current_val
                result.append((display_val, current_sum))
                current_val = val
                current_sum = length
        
        is_current_null = pd.isna(current_val) or current_val == ''
        display_val = "brak danych" if is_current_null else current_val
        result.append((display_val, current_sum))
        return result
    
    def process_data(self, nr_zal_column: str, row_mapping: dict, length_column: str, scale_column: str | None = None) -> pd.DataFrame:
        if self.df is None:
            raise ValueError("No data loaded")
        
        def validate_numeric_column(column_name: str, df: pd.DataFrame) -> None:
            non_numeric_mask = pd.to_numeric(df[column_name], errors='coerce').isna()
            if non_numeric_mask.any():
                non_numeric_values = df.loc[non_numeric_mask, column_name].unique()
                raise ValueError(f"\nWybrana kolumna '{column_name}' zawiera wartości nienumeryczne: {non_numeric_values.tolist()}")
        
        validate_numeric_column(length_column, self.df)

        const_mapping = {k: v[len("__const__:"):] for k, v in row_mapping.items() if v and v.startswith("__const__:")}
        col_mapping = {k: v for k, v in row_mapping.items() if v and not v.startswith("__const__:")}

        rows_required = [nr_zal_column, length_column] + list(col_mapping.values())
        
        if scale_column in self.df.columns:
            validate_numeric_column(scale_column, self.df)
            rows_required.append(scale_column)

        rows_required = list(dict.fromkeys(rows_required))

        working_df = self.df[rows_required].copy()

        result_rows = []

        for nr_zal, group in working_df.groupby(nr_zal_column, sort=False):
            group = group.reset_index(drop=True)
            total_length = group[length_column].sum()
            aggregated = {}

            for output_col, input_col in col_mapping.items():
                aggregated[output_col] = self.aggregate_consecutive_with_lengths(group, input_col, length_column)

            for output_col, const_val in const_mapping.items():
                aggregated[output_col] = [(const_val, total_length)]

            max_rows = max(len(agg) for agg in aggregated.values()) if aggregated else 1

            for i in range(max_rows):
                row = {nr_zal_column: nr_zal}

                # Przepisz wartość skali do każdego wiersza grupy
                if scale_column and scale_column in group.columns:
                    row[scale_column] = group[scale_column].iloc[0]

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