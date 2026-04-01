from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from fastapi import HTTPException
from core.config import SERVICE_ACCOUNT_FILE, SCOPES

def get_sheets_service():
    """Google Sheets API 서비스 객체 초기화"""
    try:
        credentials = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google API 인증 오류: {str(e)}")

def get_sheet_title(service, spreadsheet_id: str, sheetId: int) -> str:
    """sheetId를 기반으로 탭(시트)의 문자열 이름을 반환합니다."""
    sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    for sheet in sheet_metadata.get('sheets', []):
        if sheet.get("properties", {}).get("sheetId") == sheetId:
            return sheet.get("properties", {}).get("title")
    raise Exception(f"해당 sheetId({sheetId})를 가진 시트를 찾을 수 없습니다.")
