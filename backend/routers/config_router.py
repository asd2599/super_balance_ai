import os
import json
from fastapi import APIRouter, HTTPException

from core.config import SERVICE_ACCOUNT_FILE

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("/info", summary="클라이언트 설정 파일 메타데이터 반환")
async def get_config_info():
    """
    service_account.json 내부의 client_email 등을 파싱하여 프론트엔드로 전달합니다.
    """
    try:
        if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError("Google 서비스 계정 키 파일(service_account.json)이 서버에 존재하지 않습니다.")
            
        with open(SERVICE_ACCOUNT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"client_email": data.get("client_email", "Service Email Not Found")}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
