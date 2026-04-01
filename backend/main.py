import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import sheets_router, action_router, config_router
from core.database import engine, Base

# 서버 시작 전 DB 테이블 최초 생성 (ORM 스키마 로드)
# Base 모델을 상속받은 모든 클래스들이 아직 DB에 없다면 테이블로 빌드합니다.
from models.history_model import ActionHistory
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Google Sheets AI APIs", description="Modularized API with Undo features")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(sheets_router.router)
app.include_router(action_router.router)
app.include_router(config_router.router)

# --------------------------------------------------------------------------
# 프론트엔드 통합 배포 설정 (React 빌드 파일 서빙)
# --------------------------------------------------------------------------
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

# API가 아닌 모든 GET 요청에 대해 정적 파일 존재 여부 확인 후 서빙
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    # 1. API 경로로 들어왔는데 라우터에서 매칭되지 않은 경우 (404)
    if full_path.startswith("api/"):
        return {"detail": "API Not Found", "path": full_path}
    
    # 2. 실제 파일이 존재하는지 확인 (favicon.svg, assets/*.js 등)
    file_path = os.path.join(frontend_path, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 3. 그 외엔 SPA 라우팅을 위해 index.html 반환
    index_file = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    return {"message": "Frontend build not found. Please run 'npm run build' in the frontend directory."}



if __name__ == "__main__":
    import uvicorn
    # Render.com 등 배포 환경의 PORT 변수를 우선 사용, 없으면 8000 사용
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
