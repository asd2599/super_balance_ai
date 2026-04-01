import os
from dotenv import load_dotenv
import openai

# 환경 변수 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

# 앱 설정 상수
SPREADSHEET_ID = "1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
# --------------------------------------------------------------------------
# 구글 서비스 계정 키 파일 경로 (배포 환경 호환성 대응)
# --------------------------------------------------------------------------
# 1. Render.com 공식 시크릿 경로 확인
# 2. 프로젝트 루트(backend 한 단계 위) 확인
# 3. 현재 backend 내부 경로 확인
potential_paths = [
    "/etc/secrets/service_account.json", # Render.com Production
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "service_account.json"), # Repo Root (for combined)
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json") # Local backend/
]

SERVICE_ACCOUNT_FILE = None
for p in potential_paths:
    if os.path.exists(p):
        SERVICE_ACCOUNT_FILE = p
        break

# OpenAI 클라이언트 전역 인스턴스
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

