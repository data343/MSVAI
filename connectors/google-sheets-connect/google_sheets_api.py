import os.path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd

# If modifying these scopes, delete the file token.json.
SCOPES_READONLY = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SCOPES_WRITE = ['https://www.googleapis.com/auth/spreadsheets']
CREDENTIALS_FILE = 'connectors/google-sheets-connect/credentials.json'
TOKEN_FILE_READONLY = 'connectors/google-sheets-connect/token.json'
TOKEN_FILE_WRITE = 'connectors/google-sheets-connect/token_write.json' # Separate token for write operations

def get_authenticated_service(write_access=False):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    Set write_access=True to get a service with write permissions.
    """
    creds = None
    current_scopes = SCOPES_WRITE if write_access else SCOPES_READONLY
    current_token_file = TOKEN_FILE_WRITE if write_access else TOKEN_FILE_READONLY

    if os.path.exists(current_token_file):
        with open(current_token_file, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e: # Broad exception to catch refresh errors
                print(f"Error refreshing token for {'write' if write_access else 'read-only'} access: {e}. Re-initiating auth flow.")
                creds = None # Force re-authentication
        
        if not creds: # If refresh failed or no creds initially
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"Credentials file not found at {CREDENTIALS_FILE}. "
                    f"Please download it from Google Cloud Console and place it in the specified path. "
                    f"Refer to README.md for instructions."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, current_scopes)
            creds = flow.run_local_server(port=0)
        
        with open(current_token_file, 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('sheets', 'v4', credentials=creds)
        return service
    except HttpError as err:
        print(f"An API error occurred: {err}")
        return None

def get_sheet_data(service, spreadsheet_id, sheet_name):
    """
    Fetches all data from a specific sheet (tab) within a spreadsheet.
    Returns data as a list of lists.
    """
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        
        target_sheet = None
        for s in sheets:
            if s['properties']['title'] == sheet_name:
                target_sheet = s
                break
        
        if not target_sheet:
            print(f"Sheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")
            return None

        # Construct the range to get all data from the sheet.
        # Assumes sheet names don't contain special characters needing quoting,
        # which is generally true for Sheets API when referring to the whole sheet.
        range_name = f"'{sheet_name}'!A1:{get_last_column_letter(target_sheet)}{target_sheet['properties']['gridProperties']['rowCount']}"
        
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])

        if not values:
            print(f"No data found in sheet '{sheet_name}'.")
            return []
        else:
            return values
    except HttpError as err:
        print(f"An API error occurred while fetching sheet data: {err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def get_all_sheets_data_as_dataframes(service, spreadsheet_id):
    """
    Fetches all data from all sheets (tabs) in a spreadsheet.
    Returns a dictionary where keys are sheet names and values are pandas DataFrames.
    """
    all_dataframes = {}
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')

        if not sheets:
            print(f"No sheets found in spreadsheet '{spreadsheet_id}'.")
            return {}

        for s in sheets:
            sheet_title = s['properties']['title']
            print(f"Fetching data from sheet: {sheet_title}...")
            
            # Construct range to get all data.
            # This is a simplified way; for very sparse sheets, it might be inefficient.
            # A more robust way would be to find the actual data boundaries if needed.
            col_count = s['properties']['gridProperties']['columnCount']
            row_count = s['properties']['gridProperties']['rowCount']
            range_name = f"'{sheet_title}'!A1:{get_column_letter(col_count)}{row_count}"

            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])

            if not values:
                print(f"No data found in sheet '{sheet_title}'.")
                all_dataframes[sheet_title] = pd.DataFrame()
            else:
                header = values[0]
                data_rows = values[1:]
                
                # Ensure all data rows have the same number of columns as the header
                # Pad with None if a row is shorter
                processed_rows = []
                for row in data_rows:
                    if len(row) < len(header):
                        processed_rows.append(row + [None] * (len(header) - len(row)))
                    elif len(row) > len(header):
                        processed_rows.append(row[:len(header)]) # Truncate if longer
                    else:
                        processed_rows.append(row)
                
                df = pd.DataFrame(processed_rows, columns=header) if processed_rows else pd.DataFrame(columns=header)
                all_dataframes[sheet_title] = df
        return all_dataframes

    except HttpError as err:
        print(f"An API error occurred while fetching all sheets data: {err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def get_column_letter(col_idx):
    """Converts a 1-based column index into a column letter (A, B, ..., Z, AA, AB, ...)."""
    if col_idx <= 0:
        raise ValueError("Column index must be positive")
    letter = ''
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter

def get_last_column_letter(sheet_properties_or_data):
    """
    Determines the last column letter.
    Accepts either sheet properties (from metadata) or actual data (list of lists).
    """
    if isinstance(sheet_properties_or_data, dict) and 'gridProperties' in sheet_properties_or_data.get('properties', {}):
        # Input is sheet properties from metadata
        column_count = sheet_properties_or_data['properties']['gridProperties']['columnCount']
        return get_column_letter(column_count)
    elif isinstance(sheet_properties_or_data, list) and sheet_properties_or_data:
        # Input is data (list of lists)
        max_cols = 0
        for row in sheet_properties_or_data:
            if isinstance(row, list): # Ensure row is a list
                 max_cols = max(max_cols, len(row))
        return get_column_letter(max_cols) if max_cols > 0 else 'A' # Default to 'A' if no columns
    return 'A' # Default if no valid input

def list_sheet_names(service, spreadsheet_id):
    """Lists the names and GIDs of all sheets in a spreadsheet."""
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', '')
        sheet_details = [{'title': s['properties']['title'], 'id': s['properties']['sheetId']} for s in sheets]
        return sheet_details
    except HttpError as err:
        print(f"An API error occurred while listing sheet names: {err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while listing sheet names: {e}")
        return None

def add_new_sheet(service, spreadsheet_id, new_sheet_title):
    """Adds a new sheet (tab) to a spreadsheet."""
    try:
        body = {
            'requests': [{
                'addSheet': {
                    'properties': {
                        'title': new_sheet_title
                    }
                }
            }]
        }
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body).execute()
        print(f"Sheet '{new_sheet_title}' created successfully.")
        # Extract the sheetId of the newly created sheet from the response
        new_sheet_properties = response.get('replies')[0].get('addSheet').get('properties')
        return new_sheet_properties
    except HttpError as err:
        print(f"An API error occurred while creating sheet '{new_sheet_title}': {err}")
        # Check if the error is due to the sheet already existing
        if err.resp.status == 400 and 'already exists' in str(err.content).lower():
            print(f"Sheet '{new_sheet_title}' might already exist.")
            # Try to find the existing sheet's properties
            existing_sheets = list_sheet_names(service, spreadsheet_id)
            if new_sheet_title in existing_sheets:
                sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                for s in sheet_metadata.get('sheets', ''):
                    if s['properties']['title'] == new_sheet_title:
                        print(f"Returning properties for existing sheet '{new_sheet_title}'.")
                        return s['properties']
        return None
    except Exception as e:
        print(f"An unexpected error occurred while creating sheet '{new_sheet_title}': {e}")
        return None

def write_values_to_sheet(service, spreadsheet_id, range_name, values):
    """
    Writes values to a specific range in a sheet.
    range_name should be like 'Sheet1!A1' or 'Sheet1!A1:C5'.
    values should be a list of lists, e.g., [['A1_val', 'B1_val'], ['A2_val', 'B2_val']].
    """
    try:
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        print(f"{result.get('updatedCells')} cells updated in range '{range_name}'.")
        return result
    except HttpError as err:
        print(f"An API error occurred while writing to sheet: {err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while writing to sheet: {e}")
        return None

if __name__ == '__main__':
    # This block is for direct testing of this module.
    # It won't run if the script is imported by main.py and main.py is the entry point.
    # However, to prevent it from running during the initial auth flow triggered by main.py,
    # we add an explicit check.
    import sys
    if len(sys.argv) == 1: # Only run if executed directly with no arguments (typical test scenario)
        print("Testing google_sheets_api.py directly...")
        service = get_authenticated_service()
        if service:
            SAMPLE_SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_HERE' # Replace for direct testing
            SAMPLE_SHEET_NAME = 'Sheet1' # Replace for direct testing

            if SAMPLE_SPREADSHEET_ID == 'YOUR_SPREADSHEET_ID_HERE':
                print("Please update SAMPLE_SPREADSHEET_ID in the if __name__ == '__main__' block of google_sheets_api.py with a real ID to test this module directly.")
            else:
                print(f"\n--- Fetching specific sheet: '{SAMPLE_SHEET_NAME}' ---")
                data = get_sheet_data(service, SAMPLE_SPREADSHEET_ID, SAMPLE_SHEET_NAME)
                if data:
                    df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(data)
                    print(f"Data from '{SAMPLE_SHEET_NAME}':")
                    print(df.head())

                print(f"\n--- Fetching all sheets from spreadsheet: '{SAMPLE_SPREADSHEET_ID}' ---")
                all_dfs = get_all_sheets_data_as_dataframes(service, SAMPLE_SPREADSHEET_ID)
                if all_dfs:
                    for sheet_name, df_sheet in all_dfs.items():
                        print(f"\nData from sheet: {sheet_name} (first 5 rows):")
                        print(df_sheet.head())
                else:
                    print("Could not retrieve dataframes for all sheets.")
        else:
            print("Failed to get authenticated service for direct testing.")
    else:
        # This means the script is likely being run with arguments, probably by main.py's import.
        # Or, it's being run directly but with arguments, which is not the intended test scenario for this block.
        pass
