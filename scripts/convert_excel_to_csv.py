import pandas as pd
import json

def convert_excel_to_csv(excel_file_path, output_csv_path):
    df = pd.read_excel(excel_file_path)
    df.to_csv(output_csv_path, index=False)
    print(f"Converted {excel_file_path} to {output_csv_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert Excel file to CSV")
    parser.add_argument("input_file", help="Path to input Excel file")
    parser.add_argument("output_file", help="Path to output CSV file")
    args = parser.parse_args()
    
    convert_excel_to_csv(args.input_file, args.output_file)
