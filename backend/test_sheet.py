import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'service_account.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1HSJ4sQc_uXV2g82uYTfcvET2dgPkzaxYvHcGquGwcmw'

def test():
    try:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"Error: {SERVICE_ACCOUNT_FILE} not found")
            return

        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=credentials)
        
        print(f"Attempting to fetch metadata for: {SPREADSHEET_ID}")
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        print(f"Success! Found {len(sheets)} sheets.")
        for s in sheets:
            print(f" - {s.get('properties', {}).get('title')}")

    except Exception as e:
        print(f"FAILED with error: {str(e)}")

if __name__ == "__main__":
    test()
