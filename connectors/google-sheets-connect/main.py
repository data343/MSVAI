import argparse
import os
import pandas as pd
import json # For parsing --values argument
from google_sheets_api import (
    get_authenticated_service,
    get_sheet_data,
    get_all_sheets_data_as_dataframes,
    list_sheet_names,
    add_new_sheet,
    write_values_to_sheet
)

def save_dataframe_to_parquet(df, sheet_name, spreadsheet_id):
    """Saves a DataFrame to a Parquet file in the datastore."""
    datastore_dir = 'datastore/google-sheets-cache'
    if not os.path.exists(datastore_dir):
        os.makedirs(datastore_dir)
    
    # Sanitize sheet_name for use in filename
    safe_sheet_name = "".join(c if c.isalnum() else "_" for c in sheet_name)
    filename = f"{spreadsheet_id}_{safe_sheet_name}.parquet"
    filepath = os.path.join(datastore_dir, filename)
    
    try:
        df.to_parquet(filepath, index=False)
        print(f"Successfully saved '{sheet_name}' to {filepath}")
    except Exception as e:
        print(f"Error saving DataFrame for sheet '{sheet_name}' to Parquet: {e}")

def main():
    parser = argparse.ArgumentParser(description="Google Sheets Connector CLI")
    parser.add_argument("spreadsheet_id", help="The ID of the Google Spreadsheet.")
    
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--sheet_name", help="The specific sheet (tab) name to fetch data from.")
    action_group.add_argument("--all_sheets", action="store_true", help="Fetch data from all sheets in the spreadsheet.")
    action_group.add_argument("--list_sheets", action="store_true", help="List all sheet names in the spreadsheet.")
    action_group.add_argument("--create_sheet", help="Title of the new sheet to create.")
    action_group.add_argument("--write_sheet", help="Title of the sheet to write data to.")
    
    write_values_group = parser.add_mutually_exclusive_group()
    write_values_group.add_argument("--values", help="JSON string of a list of lists to write (e.g., '[[\"A1\", \"B1\"], [\"A2\", \"B2\"]]'). Used with --write_sheet.")
    write_values_group.add_argument("--values_file", help="Path to a JSON file containing a list of lists to write. Used with --write_sheet.")
    
    parser.add_argument("--range", help="The A1 notation of the range to write to (e.g., 'Sheet1!A1'). Used with --write_sheet. Defaults to A1 of the specified sheet if not provided, or if only sheet name is given in --write_sheet.")
    parser.add_argument("--save_parquet", action="store_true", help="Save the fetched sheet(s) as Parquet files in datastore/google-sheets-cache/.")

    args = parser.parse_args()

    # Determine if write access is needed
    needs_write_access = bool(args.create_sheet or args.write_sheet)
    service = get_authenticated_service(write_access=needs_write_access)

    if not service:
        access_type = "write" if needs_write_access else "read-only"
        print(f"Failed to authenticate Google Sheets service for {access_type} access. Exiting.")
        token_file_to_check = 'token_write.json' if needs_write_access else 'token.json'
        token_path = os.path.join(os.path.dirname(__file__), token_file_to_check)
        print(f"If you previously authenticated with a different scope, please delete '{token_path}' and try again to re-authorize.")
        return

    if args.sheet_name:
        print(f"Fetching data for sheet: '{args.sheet_name}' from spreadsheet: '{args.spreadsheet_id}'...")
        data = get_sheet_data(service, args.spreadsheet_id, args.sheet_name)
        if data:
            if len(data) > 1 and data[0]: # We have a header and at least one data row
                header = data[0]
                data_rows = data[1:]
                
                processed_rows = []
                num_header_cols = len(header)
                for row in data_rows:
                    num_row_cols = len(row)
                    if num_row_cols < num_header_cols:
                        processed_rows.append(row + [None] * (num_header_cols - num_row_cols))
                    elif num_row_cols > num_header_cols:
                        processed_rows.append(row[:num_header_cols]) # Truncate if longer
                    else:
                        processed_rows.append(row)
                df = pd.DataFrame(processed_rows, columns=header)
            elif data: # Only header or only data (no header)
                 df = pd.DataFrame(data)
            else: # No data at all
                df = pd.DataFrame()

            print(f"\nData from '{args.sheet_name}':")
            print(df.to_string())
            if args.save_parquet:
                save_dataframe_to_parquet(df, args.sheet_name, args.spreadsheet_id)
        else:
            print(f"No data retrieved for sheet '{args.sheet_name}'.")

    elif args.all_sheets:
        print(f"Fetching data for all sheets from spreadsheet: '{args.spreadsheet_id}'...")
        all_dataframes_dict = get_all_sheets_data_as_dataframes(service, args.spreadsheet_id)

        if not all_dataframes_dict:
            print("No dataframes retrieved for any sheets.")
            return

        for sheet_name, df in all_dataframes_dict.items():
            print(f"\nData from sheet ('{sheet_name}'):")
            print(df.to_string())
            if args.save_parquet:
                save_dataframe_to_parquet(df, sheet_name, args.spreadsheet_id)
    
    elif args.list_sheets:
        print(f"Listing sheet names and IDs for spreadsheet: '{args.spreadsheet_id}'...")
        sheet_details_list = list_sheet_names(service, args.spreadsheet_id)
        if sheet_details_list:
            print("Sheet details:")
            for details in sheet_details_list:
                print(f"- Title: {details['title']}, ID: {details['id']}")
        else:
            print("Could not retrieve sheet details or no sheets found.")

    elif args.create_sheet:
        print(f"Creating new sheet '{args.create_sheet}' in spreadsheet: '{args.spreadsheet_id}'...")
        sheet_properties = add_new_sheet(service, args.spreadsheet_id, args.create_sheet)
        if sheet_properties:
            print(f"Sheet '{sheet_properties.get('title')}' (ID: {sheet_properties.get('sheetId')}) created/verified successfully.")
        else:
            print(f"Failed to create or verify sheet '{args.create_sheet}'.")

    elif args.write_sheet:
        values_to_write = None
        if args.values:
            try:
                values_to_write = json.loads(args.values)
            except json.JSONDecodeError:
                print("Error: --values argument must be a valid JSON string representing a list of lists.")
                return
        elif args.values_file:
            try:
                with open(args.values_file, 'r') as f:
                    values_to_write = json.load(f)
            except FileNotFoundError:
                print(f"Error: File not found at --values_file path: {args.values_file}")
                return
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON from file: {args.values_file}")
                return
            except Exception as e:
                print(f"An unexpected error occurred reading the values file: {e}")
                return
        else:
            print("Error: Either --values or --values_file argument is required when using --write_sheet.")
            parser.print_help()
            return

        if not isinstance(values_to_write, list) or not all(isinstance(row, list) for row in values_to_write):
            print("Error: Values (from string or file) must be a list of lists.")
            return

        # Determine the range
        if args.range:
            range_to_write = args.range
        else:
            # Default to A1 of the specified sheet. Need to ensure sheet name is quoted if it contains spaces.
            sheet_title_for_range = args.write_sheet
            if ' ' in sheet_title_for_range or '!' in sheet_title_for_range: # Basic check for special chars
                 sheet_title_for_range = f"'{sheet_title_for_range}'"
            range_to_write = f"{sheet_title_for_range}!A1"

        print(f"Writing values to sheet '{args.write_sheet}', range '{range_to_write}' in spreadsheet: '{args.spreadsheet_id}'...")
        write_values_to_sheet(service, args.spreadsheet_id, range_to_write, values_to_write)

if __name__ == '__main__':
    main()
