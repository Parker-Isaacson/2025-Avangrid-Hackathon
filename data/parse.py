# file: load_all_sheets.py
import os
import pandas as pd

def load_all_sheets(filepath: str, output_dir: str = "clean_data") -> dict[str, pd.DataFrame]:
    # Read all sheets
    sheets = pd.read_excel(filepath, sheet_name=None)
    os.makedirs(output_dir, exist_ok=True)

    all_data = {}

    for sheet_name, df in sheets.items():
        # Clean column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Convert $-formatted cells to numeric if possible
        for col in df.columns:
            if df[col].dtype == object and df[col].astype(str).str.contains(r"\$").any():
                df[col] = df[col].replace(r"[\$,()]", "", regex=True)
                # try numeric conversion
                df[col] = pd.to_numeric(df[col], errors="ignore")

        # Combine Date + HE if both exist
        if "date" in df.columns and "he" in df.columns:
            try:
                df["timestamp"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["he"] - 1, unit="h")
            except Exception:
                pass

        # Sort by timestamp if present
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp")

        # Write to CSV
        out_name = f"{sheet_name}_clean.csv".replace(" ", "_")
        out_path = os.path.join(output_dir, out_name)
        df.to_csv(out_path, index=False)
        all_data[sheet_name] = df

    return all_data


# Example usage
if __name__ == "__main__":
    excel_path = "HackathonDatasetCleaned.xlsx"
    all_data = load_all_sheets(excel_path)

