from fastapi import APIRouter, HTTPException, Query
from services.google_sheets import get_sheets_service, get_sheet_title
from services.history_manager import pop_action, push_redo_action, pop_redo_action, push_action

router = APIRouter(prefix="/api/action", tags=["Action"])

@router.post("/undo")
async def undo_last_action(spreadsheet_id: str = Query(...)):
    action = pop_action(spreadsheet_id)
    if not action:
        raise HTTPException(status_code=400, detail="되돌릴 작업이 없습니다.")

    service = get_sheets_service()
    a_type = action["type"]
    p = action["payload"]

    try:
        if a_type == "ADD_ROW":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            num_rows = p.get("numRows", 1)
            reqs = [{"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": start_index, "endIndex": start_index + num_rows}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()

        elif a_type == "ADD_COLUMN":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            reqs = [{"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": start_index, "endIndex": start_index + 1}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()

        elif a_type == "ADD_SHEET":
            sheet_id = p["sheetId"]
            reqs = [{"deleteSheet": {"sheetId": sheet_id}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()

        elif a_type == "DELETE_ROW":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            deleted_data = p["deletedData"]
            reqs = [{"insertDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": start_index, "endIndex": start_index + 1}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()
            
            sheet_title = get_sheet_title(service, spreadsheet_id, sheet_id)
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A{start_index+1}",
                valueInputOption="USER_ENTERED",
                body={"values": [deleted_data]}
            ).execute()

        elif a_type == "DELETE_COLUMN":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            deleted_data = p["deletedData"]
            num_rows = p.get("numRows", len(deleted_data))

            reqs = [{"insertDimension": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": start_index, "endIndex": start_index + 1}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()
            
            col_data_2d = [[val] for val in deleted_data]

            def _col_idx_to_letter(idx):
                res = ""
                idx += 1
                while idx > 0:
                    idx, rem = divmod(idx - 1, 26)
                    res = chr(65 + rem) + res
                return res

            col_letter = _col_idx_to_letter(start_index)
            sheet_title = get_sheet_title(service, spreadsheet_id, sheet_id)

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!{col_letter}1:{col_letter}{num_rows}",
                valueInputOption="USER_ENTERED",
                body={"values": col_data_2d}
            ).execute()
        
        elif a_type == "UPDATE_SHEET":
            sheet_id = p["sheetId"]
            sheet_title = get_sheet_title(service, spreadsheet_id, sheet_id)
            old_data = p["oldData"]
            
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=sheet_title
            ).execute()
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A1",
                valueInputOption="USER_ENTERED",
                body={"values": old_data}
            ).execute()
        
        elif a_type == "RENAME_SHEET":
            sheet_id = p["sheetId"]
            old_title = p["oldTitle"]
            
            request_body = {
                "requests": [{
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "title": old_title
                        },
                        "fields": "title"
                    }
                }]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()
        
        # Redo 스택에 저장 (Undo 실행 시점)
        push_redo_action(action)

        return {"message": f"{a_type} 이전 상태로 되돌리기 성공", "restoredType": a_type}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"복구 중 오류 발생: {str(e)}")


@router.post("/redo")
async def redo_last_action(spreadsheet_id: str = Query(...)):
    action = pop_redo_action(spreadsheet_id)
    if not action:
        raise HTTPException(status_code=400, detail="앞으로 돌릴 작업이 없습니다.")

    service = get_sheets_service()
    a_type = action["type"]
    p = action["payload"]

    try:
        if a_type == "ADD_ROW":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            generated_data = p["generatedData"]
            num_rows = p.get("numRows", 1)
            
            # 구버전 호환용 방어코드 (이전 1줄짜리 페이로드 대비)
            if num_rows == 1 and (not generated_data or not isinstance(generated_data[0], list)):
                generated_data = [generated_data]

            reqs = [{"insertDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": start_index, "endIndex": start_index + num_rows}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()
            
            sheet_title = get_sheet_title(service, spreadsheet_id, sheet_id)
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A{start_index+1}",
                valueInputOption="USER_ENTERED",
                body={"values": generated_data}
            ).execute()

        elif a_type == "ADD_COLUMN":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            generated_data = p["generatedData"]
            reqs = [{"insertDimension": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": start_index, "endIndex": start_index + 1}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()
            
            col_data_2d = [[val] for val in generated_data]
            def _col_idx_to_letter(idx):
                res = ""
                idx += 1
                while idx > 0:
                    idx, rem = divmod(idx - 1, 26)
                    res = chr(65 + rem) + res
                return res

            col_letter = _col_idx_to_letter(start_index)
            sheet_title = get_sheet_title(service, spreadsheet_id, sheet_id)
            num_rows = len(generated_data)

            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!{col_letter}1:{col_letter}{num_rows}",
                valueInputOption="USER_ENTERED",
                body={"values": col_data_2d}
            ).execute()

        elif a_type == "ADD_SHEET":
            sheet_id = p["sheetId"]
            sheet_title = p["sheetTitle"]
            sheet_data = p["generatedSheetData"]
            
            # 시트 다시 생성 시 기존 sheetId 그대로 부여
            request_body = {
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "sheetId": sheet_id,
                            "title": sheet_title
                        }
                    }
                }]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()

            # 데이터 삽입
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A1",
                valueInputOption="USER_ENTERED",
                body={"values": sheet_data}
            ).execute()

        elif a_type == "DELETE_ROW":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            reqs = [{"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "ROWS", "startIndex": start_index, "endIndex": start_index + 1}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()

        elif a_type == "DELETE_COLUMN":
            sheet_id = p["sheetId"]
            start_index = p["startIndex"]
            reqs = [{"deleteDimension": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": start_index, "endIndex": start_index + 1}}}]
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={"requests": reqs}).execute()

        elif a_type == "UPDATE_SHEET":
            sheet_id = p["sheetId"]
            sheet_title = get_sheet_title(service, spreadsheet_id, sheet_id)
            new_data = p["newData"]
            
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=sheet_title
            ).execute()
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A1",
                valueInputOption="USER_ENTERED",
                body={"values": new_data}
            ).execute()
            
        elif a_type == "RENAME_SHEET":
            sheet_id = p["sheetId"]
            new_title = p["newTitle"]
            
            request_body = {
                "requests": [{
                    "updateSheetProperties": {
                        "properties": {
                            "sheetId": sheet_id,
                            "title": new_title
                        },
                        "fields": "title"
                    }
                }]
            }
            service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=request_body).execute()
        
        # 순방향 수행 완료 시 플래그 재전환(is_undone=False)은 
        # pop_redo_action 내부에서 이미 수행되었으므로 별도 처리 불필요
        
        return {"message": f"{a_type} 앞으로 돌리기(Redo) 완료", "restoredType": a_type, "title": p.get("sheetTitle")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redo 오류: {str(e)}")

@router.get("/logs")
async def get_action_logs(spreadsheet_id: str = Query(..., description="필터링할 시트 ID")):
    """특정 시트의 히스토리 액션 기록을 반환합니다."""
    from core.database import SessionLocal
    from models.history_model import ActionHistory
    
    db = SessionLocal()
    try:
        query = db.query(ActionHistory).filter(ActionHistory.spreadsheet_id == spreadsheet_id)
        logs = query.order_by(ActionHistory.id.desc()).limit(100).all()
        result = []
        for log in logs:
            summary_txt = "AI 요약 내용 없음"
            if isinstance(log.payload, dict):
                summary_txt = log.payload.get("summary", summary_txt)
                
            result.append({
                "id": log.id,
                "action_type": log.action_type,
                "summary": summary_txt,
                "is_undone": log.is_undone,
                "created_at": log.created_at.isoformat()
            })
        return {"logs": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그 조회 오류: {str(e)}")
    finally:
        db.close()
