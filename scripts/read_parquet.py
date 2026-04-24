import pandas as pd
import sys

def view_parquet(file_path):
    try:
        df = pd.read_parquet(file_path)
        print(f"Contents of {file_path}:")
        print(df.to_string())
    except Exception as e:
        print(f"Error reading Parquet file {file_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parquet_file_path = sys.argv[1]
        view_parquet(parquet_file_path)
    else:
        print("Please provide the path to the Parquet file as a command-line argument.")
        print("Usage: python scripts/read_parquet.py <path_to_parquet_file>")
