import os
from dotenv import load_dotenv
import openai

# 환경 변수 로드
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(env_path)

# 앱 설정 상수
SPREADSHEET_ID = "1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "service_account.json")

# OpenAI 클라이언트 전역 인스턴스
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
