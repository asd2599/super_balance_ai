from core.database import SessionLocal
from models.history_model import ActionHistory
from services.ai_generator import summarize_action_with_ai

def push_action(action_type: str, payload: dict, spreadsheet_id: str = None):
    db = SessionLocal()
    try:
        # AI 요약기 태우기
        summary_text = summarize_action_with_ai(action_type, payload)
        
        # 원본 보호를 위해 페이로드 복사본에 요약 주입 (JSONB 저장용)
        final_payload = payload.copy()
        final_payload["summary"] = summary_text

        # 새로운 작업이 발생하면 해당 시트의 향후 분기된 Redo(is_undone=True) 이력들은 폐기
        db.query(ActionHistory).filter(
            ActionHistory.spreadsheet_id == spreadsheet_id,
            ActionHistory.is_undone == True
        ).delete()
        
        # 신규 Action Insert
        new_action = ActionHistory(
            spreadsheet_id=spreadsheet_id,
            action_type=action_type,
            payload=final_payload,
            is_undone=False
        )
        db.add(new_action)
        db.commit()
        print(f"[DB Undo History] Pushed for {spreadsheet_id}: {action_type}")
    except Exception as e:
        db.rollback()
        print(f"[DB Push Error] {e}")
    finally:
        db.close()

def pop_action(spreadsheet_id: str):
    db = SessionLocal()
    try:
        # 해당 시트의 반환 안 된(False) 내역 중 가장 최후의 로깅(id DESC)을 검색
        last_action = db.query(ActionHistory).filter(
            ActionHistory.spreadsheet_id == spreadsheet_id,
            ActionHistory.is_undone == False
        ).order_by(ActionHistory.id.desc()).first()
        
        if not last_action:
            return None
            
        # 프론트 반환을 위해 Dictionary 변환
        action = {"type": last_action.action_type, "payload": last_action.payload, "db_id": last_action.id}
        
        # Redo 큐로 이전한다는 의미로 is_undone = True 플래그 변경
        last_action.is_undone = True
        db.commit()
        
        print(f"[DB Undo History] Popped ID {last_action.id} for {spreadsheet_id}")
        return action
    finally:
        db.close()

def push_redo_action(action_dict: dict):
    """
    Undo 시점에 Redo 스택으로 이동시키는 로직.
    DB 기반에서는 pop_action 시점에 이미 is_undone=True 처리가 되므로 별도 작업이 필요없으나,
    인터페이스 호환성을 위해 유지합니다.
    """
    pass

def pop_redo_action(spreadsheet_id: str):
    db = SessionLocal()
    try:
        # 해당 시트의 취소 처리된(True) 내역 중 가장 예전에(id ASC) 등록된 로깅 검색
        first_redo = db.query(ActionHistory).filter(
            ActionHistory.spreadsheet_id == spreadsheet_id,
            ActionHistory.is_undone == True
        ).order_by(ActionHistory.id.asc()).first()
        
        if not first_redo:
            return None
            
        action = {"type": first_redo.action_type, "payload": first_redo.payload, "db_id": first_redo.id}
        
        # 다시 Undo 큐로 복구완료했다는 의미로 is_undone = False 플래그 변경
        first_redo.is_undone = False
        db.commit()
        
        print(f"[DB Redo History] Popped ID {first_redo.id} for {spreadsheet_id}")
        return action
    finally:
        db.close()

def clear_history(spreadsheet_id: str = None):
    db = SessionLocal()
    try:
        query = db.query(ActionHistory)
        if spreadsheet_id:
            query = query.filter(ActionHistory.spreadsheet_id == spreadsheet_id)
        query.delete()
        db.commit()
    finally:
        db.close()

