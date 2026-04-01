# Google Sheets API 연동 구현 계획

주어진 스프레드시트(ID: 1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss)의 데이터를 읽어와 사용자에게 보여주는 기능을 구현합니다. 백엔드에서는 FastAPI와 `service_account.json`을 사용해 인증하고 데이터를 제공하며, 프론트엔드에서는 이를 가져와 화면에 출력합니다.

## User Review Required

> [!IMPORTANT]
> - 프론트엔드의 스타일링 관련해서 구체적으로 선호하는 디자인이나 라이브러리(예: TailwindCSS, Material-UI 등)가 있으신가요? 
> - Google 스프레드시트에서 가져올 구체적인 워크시트(탭) 이름이나 범위(Range)가 정해져 있나요? (기본적으로는 첫 번째 시트의 전체 데이터를 가져오도록 구성하겠습니다.)

## Proposed Changes

---

### Backend (FastAPI)

FastAPI 서버를 초기 설정하고 Google API를 연동합니다.

#### [NEW] backend/requirements.txt
필요 라이브러리 목록 작성 (fastapi, uvicorn, google-api-python-client 혹은 gspread, pydantic 등).

#### [NEW] backend/main.py
FastAPI 애플리케이션 초기화 및 엔드포인트 라우팅 구현. CORS 미들웨어를 추가하여 프론트엔드의 접근을 허용합니다.

#### [NEW] backend/services/google_sheets.py
`service_account.json` 자격 증명을 통해 Google Sheets API와 통신하고, 스프레드시트 데이터를 읽어오는 비즈니스 로직을 구현합니다.

---

### Frontend

React (Vite) 환경에서 백엔드 API를 호출하여 화면에 데이터를 렌더링합니다.

#### [NEW] frontend/src/services/api.js
백엔드의 `/api/sheets` 엔드포인트를 호출하는 fetch 혹은 axios 로직을 추가합니다.

#### [MODIFY] frontend/src/App.jsx (또는 신규 컴포넌트)
가져온 스프레드시트 데이터를 React 상태(state)에 저장하고, 테이블 형태로 화면에 출력하는 로직과 UI를 구현합니다.

## Open Questions

> [!WARNING]
> - `service_account.json`에 해당하는 Google Cloud 서비스 계정에 해당 스프레드시트(1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss)에 대한 **읽기 권한(공유)** 이 부여되어 있어야 합니다. 권한이 추가되어 있는지 확인 부탁드립니다.

## Verification Plan

### Automated Tests
- 없음

### Manual Verification
- 백엔드: FastAPI Swagger U(`http://localhost:8000/docs`)에서 `/api/sheets` 엔드포인트 정상 작동 테스트.
- 프론트엔드: 브라우저에서 서버에서 전달한 시트 내용이 정상적으로 테이블 형식으로 렌더링되는지 확인.
