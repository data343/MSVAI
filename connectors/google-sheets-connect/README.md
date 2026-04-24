# Google Sheets Connector

This connector provides functionality to read data from Google Sheets.

## Prerequisites

- Python 3.x
- Pip (Python package installer)

## Setup

    Navigate to the `connectors/google-sheets-connect` directory and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Enable Google Sheets API & Download Credentials:**
    *   Go to the [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project or select an existing one.
    *   Navigate to "APIs & Services" > "Library".
    *   Search for "Google Sheets API" and enable it for your project.
    *   Navigate to "APIs & Services" > "Credentials".
    *   Click "+ CREATE CREDENTIALS" and choose "OAuth client ID".
    *   If prompted, configure the OAuth consent screen. For "Application type", select "Desktop app".
    *   Give the client ID a name (e.g., "Cline Sheets Connector Client").
    *   Click "CREATE". You will see a pop-up with your client ID and secret. Click "DOWNLOAD JSON" to download the `credentials.json` file.
    *   **Important:** Place the downloaded `credentials.json` file into the `connectors/google-sheets-connect/` directory. This file is required for authentication.

3.  **Authentication Token:**
    *   The first time you run the `main.py` script, it will attempt to open a web browser to guide you through the Google authentication flow.
    *   After successful authentication, a `token.json` file will be created in the `connectors/google-sheets-connect/` directory. This token will be used for subsequent authentications.
    *   **Security Note:** Both `credentials.json` and `token.json` contain sensitive information. Ensure they are **NOT** committed to version control. They should be added to your project's `.gitignore` file.

## Usage

The `main.py` script can be used to fetch data from a Google Sheet.

(Further usage instructions will be added as the script is developed.)

## Modules

*   `main.py`: Main executable script.
*   `google_sheets_api.py`: Handles interactions with the Google Sheets API.
*   `requirements.txt`: Lists Python dependencies.
