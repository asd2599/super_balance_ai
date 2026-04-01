import os
import json
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/info", summary="클라이언트 설정 파일 메타데이터 반환")
async def get_config_info():
    """
    service_account.json 내부의 client_email 등을 파싱하여 프론트엔드로 전달합니다.
    """
    try:
        service_account_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json")
        if not os.path.exists(service_account_path):
            raise FileNotFoundError("service_account.json 파일이 존재하지 않습니다.")
            
        with open(service_account_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"client_email": data.get("client_email", "Service Email Not Found")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
