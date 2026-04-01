# 🎮 Super-Balance AI
> **게임 데이터 기획 및 밸런스 QA 자동화 시스템**

본 프로젝트는 게임 제작 및 서비스 과정에서 기획자가 겪는 데이터 관리의 휴먼 에러를 방지하고, AI를 통해 밸런싱 작업의 효율을 극대화하기 위해 개발된 **게임 기획 서포트 툴**입니다.

---

## 📌 1. 프로젝트 개요 (Problem & Solution)

### **기존의 문제 (Problem)**
*   **밸런싱 오류**: 수만 줄의 데이터 시트에서 수치 하나가 잘못 기입될 경우 게임 경제 붕괴로 이어짐.
*   **반복 작업**: 신규 콘텐츠 추가 시 초기 더미 데이터를 수동으로 기합하는 단순 반복 작업의 비중이 높음.
*   **이력 관리 부재**: 구글 시트만으로는 "누가 어떤 의도로 이 수치를 바꿨는지"에 대한 히스토리 추적이 어려움.

### **해결 방안 (Solution)**
*   **AI 이상 탐지**: AI가 테이블 전체 수치를 교차 스캔하여 불합리한 밸런스(가성비 오류 등)를 즉시 시각화.
*   **자연어 데이터 핸들링**: "모든 몬스터 공격력을 20% 올려줘" 같은 프롬프트만으로 복잡한 수치 연산 자동화.
*   **영구 히스토리 시스템**: 모든 수정 사항을 DB에 기록하고 AI 요약을 제공하여 협업 효율 증대.

---

## ✨ 2. 핵심 기능 (Key Features)

### ⚠️ AI 밸런스 감사 (Audit) - **[핵심 기능]**
*   현재 활성화된 시트 데이터를 AI가 분석하여 수치적 모순이 있는 행을 찾아 리포트를 제공합니다.
*   예: "롱소드의 가격 대비 공격력이 다른 무기에 비해 비정상적으로 높음" 등의 기획적 결함을 자동 포착.

### 🤖 AI 자동 생성 및 수정
*   **행/열 생성**: 기존 데이터의 맥락을 파악하여 다음 단계에 어울리는 데이터를 예측 생성합니다.
*   **시트 전체 변환**: 번역, 수치 일괄 조정, 속성 변경 등을 자연어로 지시할 수 있습니다.

### 📜 작업 로그 및 Undo/Redo
*   모든 데이터 변경 액션은 PostgreSQL(또는 SQLite)에 저장됩니다.
*   AI가 해당 작업이 무엇이었는지 한 문장 요약을 제공하며, 언제든 이전 상태로 되돌릴 수 있습니다.

### ⬇️ 데이터 원클릭 추출 (Export)
*   편집된 기획 데이터를 즉시 클라이언트/서버 엔진에서 사용할 수 있도록 **CSV** 및 **JSON** 포맷으로 제작하여 다운로드합니다.

---

## 🛠 3. 기술 스택 (Tech Stack)

### **Frontend**
*   **React (Vite)**: 빠르고 반응성 있는 UI 제공.
*   **Vanilla CSS**: 경량화된 스타일링 및 성능 최적화.

### **Backend**
*   **FastAPI (Python)**: 고성능 비동기 API 서버 구성.
*   **SQLAlchemy**: 데이터베이스 ORM 관리.
*   **OpenAI API (GPT-3.5/4o)**: 밸런스 분석 및 데이터 생성 엔진.
*   **Google Sheets API**: 실시간 클라우드 데이터 동기화.

### **Database**
*   **SQLite (Local) / PostgreSQL (Remote)**: 작업 히스토리 및 설정값 영구 저장.

---

## 🚀 4. 시작하기 (Getting Started)

### **환경 설정 (.env)**
`backend/.env` 파일을 만들고 아래 정보를 입력해야 합니다.
```env
OPENAI_API_KEY=your_openai_key
# 구글 서비스 계정(service_account.json) 파일이 backend 폴더에 필요합니다.
```

### **방법 1: 통합 실행 (Combined Deployment)**
본 프로젝트는 단일 서버에서 프론트/백엔드를 모두 실행할 수 있도록 최적화되어 있습니다.
1.  **프론트엔드 빌드**:
    ```bash
    cd frontend
    npm install
    npm run build
    ```
2.  **서버 실행**:
    ```bash
    cd ../backend
    pip install -r requirements.txt
    python main.py
    ```
3.  **접속**: 브라우저에서 `http://localhost:8000` 접속.

### **방법 2: 개발 모드 실행**
*   **Backend**: `python main.py` (8000 포트)
*   **Frontend**: `npm run dev` (5173 포트)

---

## 📂 5. 프로젝트 구조
```text
super-balance-ai/
├── backend/                # FastAPI 서버 및 AI 로직
│   ├── core/               # DB/Config 설정
│   ├── models/             # DB 스키마
│   ├── routers/            # API 엔드 포인트
│   └── services/           # AI/Google API 핵심 비즈니스 로직
├── frontend/               # React (Vite) 앱
│   └── src/                # UI 컴포넌트 및 상태 관리
└── README.md
```

---

## 📝 6. 작성자 및 문의
*   **Name**: [본인 성함 입력]
*   **Contact**: [본인 이메일 입력]
*   **GitHub**: [본인 깃허브 주소]
