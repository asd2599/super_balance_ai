# [과제 제출용 통합 문서] Super-Balance AI: 게임 밸런싱 대시보드

본 문서는 과제 면접의 필수 제출 항목 5종(과제 문서, 프로토타입 링크, 데모 안내, 화면 설계, 바이브코딩 지시 내용)에 맞춰 작성된 최종 패키지입니다.

---

## 1. 과제 문서 (Project Overview)
- **프로젝트 명**: Super-Balance AI
- **핵심 목표**: AI를 활용한 게임 밸런스 데이터 자동 생성, 수치 모순 탐지(Audit), 영구 히스토리 기록(PostgreSQL) 및 복구(Undo/Redo) 시스템 구축.
- **해결 과제**: 기획자의 휴먼 에러 방지 및 신규 콘텐츠 데이터 생성 시간 단축.
- **핵심 기술 스택**: 
    - **Backend**: FastAPI (Python), SQLAlchemy (ORM), PostgreSQL.
    - **Frontend**: React (Vite), Glassmorphism CSS UI.
    - **External**: Google Sheets API, OpenAI GPT-3.5 API.

---

## 2. 프로토타입 링크 (Prototype Link)
- **Local Dev Server**: `http://localhost:5173`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Google Sheets ID**: `1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss`

---

## 3. 화면 설계 (UI Design Specification)

### [A] Sidebar: 데이터 소스 및 네비게이션
- **설정 영역**: 서비스 계정 이메일(Service Email) 복사 및 스프레드시트 ID 연결 컨트롤.
- **시트 목록**: 연결된 스프레드시트 내의 개별 워크시트를 실시간으로 동기화하여 목록화(Navigation).

### [B] Top Toolbar: 액션 및 히스트리 제어
- **데이터 추출**: JSON / CSV 포맷 원클릭 다운로드.
- **데이터 제어**: PostgreSQL 기반의 Undo(↩️) / Redo(↪️) 엔진 및 상세 작업 로그(📜) 조회 모달.

### [C] Main Area: 데이터 그리드 및 AI 도구
- **시트 뷰어**: 2차원 배열 데이터를 기반으로 한 인터랙티브 테이블 렌더링.
- **AI 도구함**: 
    - **AI 템플릿 생성**: 자연어 입력을 통한 신규 시트 뼈대 및 데이터 일괄 생성.
    - **AI 열/행 생성**: 특정 주제에 맞는 수치 밸런스가 조율된 데이터 자동 추가.
    - **AI 밸런스 검사(Audit)**: 시트 전체 수치를 스캔하여 모순(Anomaly) 탐지 및 리포트 제공.

### [D] Loading UX (Premium Aesthetics): 
- **Glassmorphism Overlay**: 데이터 처리 중 배경 블러(Blur) 효과와 펄싱(Pulsing) 카드를 적용하여 프로덕션 수준의 UX 제공.

---

## 4. 바이브코딩 지시 내용 (Vibe-Coding Instructions)
*초기 구축부터 고도화까지 실제로 AI에게 전달된 단계별 핵심 지시문(프롬프트) 리스트입니다.*

1. **[초기 연동]** "Google Sheets API를 사용해서 스프레드시트에 있는 내용을 출력하고 싶어. Backend에서 `service_account.json`을 참조해서 FastAPI로 정보를 가져오고 Frontend에 출력해줘."
2. **[데이터 조작]** "출력된 시트의 행과 열을 삭제하거나 추가하는 기능을 만들어줘."
3. **[AI 연동]** "열을 추가할 때 제목을 입력받고, `.env`의 OpenAI API Key를 활용해서 시트의 정보에 맞는 적절한 수치 데이터를 AI가 자동으로 채우도록 해줘."
4. **[AI 자동 생성]** "시트 생성 버튼을 만들고, 원하는 시트 제목과 내용을 입력하면 AI가 테이블 뼈대와 초기 데이터를 통째로 생성해 주는 기능을 추가해줘."
5. **[아키텍처 개선]** "기능별로 폴더를 나누어 `main.py`를 리팩토링하고, 실행 취준(Undo) 기능을 구현해줘."
6. **[AI 기반 수정]** "AI 수정 버튼을 만들어서 자연어 프롬프트로 테이블 내부의 셀 내용을 자유롭게 수정할 수 있게 해줘."
7. **[DB 영구 히스토리]** ".env의 DB 정보를 이용해 PostgreSQL에 히스토리 테이블을 생성하고, 작업 이력을 영구적으로 저장하여 시스템 재시작 후에도 Undo/Redo가 가능하게 해줘."
8. **[데이터 익스포트]** "현재 선택된 시트를 JSON과 CSV 파일로 다운로드하는 기능을 추가해줘."
9. **[최적화]** "시트 조회 및 수정 시 발생하는 지연(Latency)을 줄이기 위해 LRU 캐싱과 FastAPI BackgroundTasks를 적용해줘."
10. **[UX 고도화]** "투박한 대기 문구를 제거하고, 글래스모피즘 스타일의 프리미엄 로딩 모달을 도입하여 UI를 세련되게 다듬어줘."

---

## 5. 간단한 데모 안내 (Demo Instruction)
1. **Google Sheets 연결**: 시트 ID를 입력하여 데이터를 실시간으로 동기화합니다.
2. **AI 데이터 생성**: "AI 행 생성" 버튼을 눌러 AI가 현재 맥락에 맞는 수치를 자동으로 채우는 과정을 확인합니다.
3. **이상 탐지 및 검수**: "⚠️ AI 밸런스 검사" 버튼을 눌러 수치 모순이 있는 행을 AI가 찾아내고 팝업으로 리포트하는 기능을 테스트합니다.
4. **히스토리 복구**: 로그 확인 후 `Undo` 버튼을 클릭하여 DB에 기록된 이전 시점으로 데이터가 즉각 롤백되는지 검증합니다.
