from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from services.google_sheets import get_sheets_service, get_sheet_title
from services.ai_generator import generate_rows, generate_column_values, generate_new_sheet
from services.history_manager import push_action

router = APIRouter(prefix="/api/sheets", tags=["Sheets"])

@router.get("")
async def get_sheet_list(spreadsheet_id: str = Query(..., description="연결할 구글 스프레드시트의 ID")):
    service = get_sheets_service()
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        if not sheets:
            raise HTTPException(status_code=404, detail="시트를 찾을 수 없습니다.")
        
        sheet_info_list = [
            {
                "title": sheet.get("properties", {}).get("title", ""),
                "sheetId": sheet.get("properties", {}).get("sheetId", 0)
            } for sheet in sheets
        ]
        return {"sheets": sheet_info_list}
    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] Google API Error: {error_msg}")
        
        if "403" in error_msg or "permission" in error_msg.lower():
            from services.google_sheets import SERVICE_ACCOUNT_FILE
            import json
            import os
            email = "Service Email"
            if os.path.exists(SERVICE_ACCOUNT_FILE):
                with open(SERVICE_ACCOUNT_FILE, "r") as f:
                    email = json.load(f).get("client_email", email)
            raise HTTPException(
                status_code=403, 
                detail=f"구글 시트 권한 부족: 해당 스프레드시트 상단의 '공유' 버튼을 클릭하여 아래 이메일을 '편집자'로 추가해 주세요.\n{email}"
            )
        elif "404" in error_msg or "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail="스프레드시트를 찾을 수 없습니다. ID가 정확한지 확인해 주세요.")
        
        raise HTTPException(status_code=500, detail=f"목록 조회 오류: {error_msg}")

@router.get("/{sheet_name}")
async def get_sheet_data(sheet_name: str, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_name).execute()
        values = result.get('values', [])
        
        if not values:
            return {"data": [], "sheet_name": sheet_name}
            
        headers = values[0]
        dataList = []
        for row in values[1:]:
            rowData = {}
            for i, val in enumerate(row):
                if i < len(headers):
                    rowData[headers[i]] = val
            dataList.append(rowData)
            
        return {"data": dataList, "sheet_name": sheet_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 오류: {str(e)}")

class RowRequest(BaseModel):
    num_rows: int = 1

@router.post("/{sheetId}/rows")
async def add_row(sheetId: int, req: RowRequest, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_title).execute()
        values = result.get('values', [])
        
        if not values or len(values) < 1:
            raise HTTPException(status_code=400, detail="시트가 비어있어 AI가 유추할 수 없습니다.")
        
        new_rows = generate_rows(values[0], values, req.num_rows)
        
        # 길이 보정
        start_index = len(values) # appending adds to bottom

        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_title,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": new_rows}
        ).execute()
        
        # Undo history (백그라운드 실행)
        background_tasks.add_task(push_action, "ADD_ROW", {"sheetId": sheetId, "startIndex": start_index, "generatedData": new_rows, "numRows": req.num_rows}, spreadsheet_id)

        return {"message": f"AI 행 {req.num_rows}줄 일괄 추가 성공", "generated_data": new_rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류: {str(e)}")

class ColumnRequest(BaseModel):
    new_column_name: str

@router.post("/{sheetId}/columns")
async def add_column(sheetId: int, req: ColumnRequest, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_title).execute()
        values = result.get('values', [])
        
        if not values:
            values = [[req.new_column_name]]
        else:
            num_data_rows = len(values) - 1
            new_col_data = generate_column_values(req.new_column_name, num_data_rows, values)
            
            target_col_index = len(values[0])
            values[0].append(req.new_column_name)
            for i, row in enumerate(values[1:]):
                while len(row) < target_col_index:
                    row.append("")
                row.append(new_col_data[i])

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_title}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": values}
        ).execute()

        new_col_index = len(values[0]) - 1
        # Undo history (백그라운드 실행)
        background_tasks.add_task(push_action, "ADD_COLUMN", {"sheetId": sheetId, "startIndex": new_col_index, "generatedData": [req.new_column_name] + new_col_data}, spreadsheet_id)

        return {"message": "AI 열 추가 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류: {str(e)}")

@router.delete("/{sheetId}/rows/{row_index}")
async def delete_row(sheetId: int, row_index: int, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        # 백업을 위해 데이터 조회
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_title).execute()
        values = result.get('values', [])
        deleted_data = values[row_index] if row_index < len(values) else []

        request_body = {
            "requests": [{
                "deleteDimension": {
                    "range": {
                        "sheetId": sheetId,
                        "dimension": "ROWS",
                        "startIndex": row_index,
                        "endIndex": row_index + 1
                    }
                }
            }]
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()
        
        # 백그라운드 실행
        background_tasks.add_task(push_action, "DELETE_ROW", {"sheetId": sheetId, "startIndex": row_index, "deletedData": deleted_data}, spreadsheet_id)
        return {"message": "행 삭제 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"행 삭제 오류: {str(e)}")

@router.delete("/{sheetId}/columns/{col_index}")
async def delete_column(sheetId: int, col_index: int, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_title).execute()
        values = result.get('values', [])
        
        # 열의 각 행 데이터 백업
        deleted_data = []
        for row in values:
            if col_index < len(row):
                deleted_data.append(row[col_index])
            else:
                deleted_data.append("")

        request_body = {
            "requests": [{
                "deleteDimension": {
                    "range": {
                        "sheetId": sheetId,
                        "dimension": "COLUMNS",
                        "startIndex": col_index,
                        "endIndex": col_index + 1
                    }
                }
            }]
        }
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()
        
        # 백그라운드 실행
        background_tasks.add_task(push_action, "DELETE_COLUMN", {"sheetId": sheetId, "startIndex": col_index, "deletedData": deleted_data, "numRows": len(values)}, spreadsheet_id)
        return {"message": "열 삭제 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"열 삭제 오류: {str(e)}")

@router.post("/{sheetId}/audit")
async def audit_sheet(sheetId: int, spreadsheet_id: str = Query(...)):
    """현재 시트를 AI에게 보내어 밸런스 이상을 스캔합니다."""
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_title).execute()
        current_values = result.get('values', [])
        
        if not current_values or len(current_values) < 2:
            return {"issues": [], "status": "no_data", "message": "검사할 데이터가 충분치 않습니다."}

        from services.ai_generator import audit_balance_anomalies
        audit_result = audit_balance_anomalies(current_values)
        return audit_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시트 검수 중 서버 오류가 발생했습니다: {str(e)}")

class GenerateSheetRequest(BaseModel):
    new_sheet_title: str
    prompt: str

@router.post("/generate")
async def generate_action(req: GenerateSheetRequest, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        for sheet in sheet_metadata.get('sheets', []):
            if sheet.get("properties", {}).get("title") == req.new_sheet_title:
                raise HTTPException(status_code=400, detail="해당 시트 제목은 이미 존재합니다.")
        
        sheet_data = generate_new_sheet(req.prompt)

        # 3. 빈 시트 생성
        request_body = {
            "requests": [{
                "addSheet": {
                    "properties": {
                        "title": req.new_sheet_title
                    }
                }
            }]
        }
        res = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()
        new_sheet_id = res['replies'][0]['addSheet']['properties']['sheetId']

        # 4. 데이터 삽입
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{req.new_sheet_title}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": sheet_data}
        ).execute()

        # 백그라운드 실행
        background_tasks.add_task(push_action, "ADD_SHEET", {"sheetId": new_sheet_id, "sheetTitle": req.new_sheet_title, "generatedSheetData": sheet_data}, spreadsheet_id)

        return {"message": "시트 생성 성공", "sheetId": new_sheet_id, "title": req.new_sheet_title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"생성 오류: {str(e)}")

@router.post("/{sheetId}/init")
async def init_sheet(sheetId: int, req: GenerateSheetRequest, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    """현재 선택된 빈 시트를 AI 프롬프트 기반으로 초기화(데이터 채움)합니다."""
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        sheet_data = generate_new_sheet(req.prompt)

        # 현재 시트 내용 갱신 (헤더 포함)
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_title}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": sheet_data}
        ).execute()

        # 백그라운드 실행
        background_tasks.add_task(push_action, "UPDATE_SHEET", {"sheetId": sheetId, "sheetTitle": sheet_title, "oldData": [], "newData": sheet_data}, spreadsheet_id)

        return {"message": "시트 초기화 성공", "sheetId": sheetId, "title": sheet_title}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시트 초기화 오류: {str(e)}")

class ModifySheetRequest(BaseModel):
    prompt: str

@router.post("/{sheetId}/modify")
async def modify_sheet(sheetId: int, req: ModifySheetRequest, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        sheet_title = get_sheet_title(spreadsheet_id, sheetId)
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=sheet_title).execute()
        current_values = result.get('values', [])

        if not current_values:
            raise HTTPException(status_code=400, detail="백업할 데이터 표의 셀이 하나도 없습니다.")

        # AI 호출로 전체 치환 및 번역, 갱신된 새로운 배열 획득
        from services.ai_generator import modify_sheet_content
        new_values = modify_sheet_content(req.prompt, current_values)

        # 사이즈가 줄어드는 경우 지울 부분이 남을 수 있으므로 시트 싹 clear 처리 (범위 갱신)
        # 하지만 기존 구조를 파괴하지 말라고 지시했으므로 기본 clear->update 조합으로 깔끔하게.
        service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id,
            range=sheet_title
        ).execute()

        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_title}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": new_values}
        ).execute()

        # 백그라운드 실행
        background_tasks.add_task(push_action, "UPDATE_SHEET", {"sheetId": sheetId, "sheetTitle": sheet_title, "oldData": current_values, "newData": new_values}, spreadsheet_id)

        return {"message": "AI 시트 내용 일괄 수정 성공"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 수정 오류: {str(e)}")

class RenameSheetRequest(BaseModel):
    new_title: str

@router.put("/{sheetId}/rename")
async def rename_sheet(sheetId: int, req: RenameSheetRequest, background_tasks: BackgroundTasks, spreadsheet_id: str = Query(...)):
    service = get_sheets_service()
    try:
        current_title = get_sheet_title(spreadsheet_id, sheetId)
        
        # 이름 길이 제한 및 빈 문자열 방어
        if not req.new_title or len(req.new_title.strip()) == 0:
            raise HTTPException(status_code=400, detail="새로운 시트 이름을 입력해야 합니다.")
            
        request_body = {
            "requests": [{
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheetId,
                        "title": req.new_title.strip()
                    },
                    "fields": "title"
                }
            }]
        }
        
        # 실제 구글 API 호출 (이 부분이 누락되어 수정되지 않았음)
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()

        # 캐시 초기화: 이름이 변경되었으므로 기존 sheetId -> title 매핑 캐시를 비웁니다.
        # (이미 상단에서 임포트된 get_sheet_title 사용)
        get_sheet_title.cache_clear()
        
        # 백그라운드 히스토리 기록
        background_tasks.add_task(push_action, "RENAME_SHEET", {"sheetId": sheetId, "oldTitle": current_title, "newTitle": req.new_title.strip()}, spreadsheet_id)
        
        return {"message": f"시트 이름이 '{req.new_title}'(으)로 변경되었습니다.", "new_title": req.new_title.strip()}
    except Exception as e:
        error_msg = str(e)
        print(f"[DEBUG] Rename Error: {error_msg}")
        # 중복된 이름 등 구글 API 에러 발생 시 처리
        if "already exists" in error_msg.lower():
            raise HTTPException(status_code=400, detail="이미 동일한 이름의 시트가 존재합니다.")
        raise HTTPException(status_code=500, detail=f"시트 이름 변경 오류: {error_msg}")
