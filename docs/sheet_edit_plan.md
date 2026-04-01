# Google Sheets API 연동 구현 계획

주어진 스프레드시트(ID: 1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss)의 데이터를 읽어와 사용자에게 보여주는 기능을 구현합니다. 백엔드에서는 FastAPI와 `service_account.json`을 사용해 인증하고 데이터를 제공하며, 프론트엔드에서는 이를 가져와 화면에 출력합니다.

## User Review Required

> [!WARNING]
> - 기존 사용 중이던 Google 인증 권한(`SCOPES`)이 **읽기 전용**(`spreadsheet.readonly`)에서 **읽기/쓰기 권한**(`spreadsheets`)으로 변경되어야 합니다.
> - 행과 열 추가/삭제 기능은 시트 내부의 원본 데이터를 조작하며, 헤더(첫 번째 줄)의 데이터 무결성에 영향을 줄 수 있으니 헤더는 삭제 불가 처리하는 방향을 추천합니다. 동의하시나요?
> - 행 추가 시 기본적으로 비어있는 데이터(빈칸)를 끝에 혹은 지시한 위치에 덧붙이는 형태가 됩니다. 괜찮으신가요?

## Proposed Changes

---

### Backend (FastAPI)

FastAPI 서버를 초기 설정하고 Google API를 연동합니다.

#### [NEW] backend/requirements.txt
필요 라이브러리 목록 작성 (fastapi, uvicorn, google-api-python-client 혹은 gspread, pydantic 등).

#### [MODIFY] backend/main.py
기존 엔드포인트를 개편하고 삽입/삭제용 라우터를 추가합니다.
- `GET /api/sheets`: 메타데이터에 각 시트의 고유 `sheetId` 정보 포함 (API 갱신 필수)
- `GET /api/sheets/{sheet_name}`: 데이터 패치
- **[NEW]** `POST /api/sheets/{sheetId}/rows`: 특정 시트의 제일 마지막에 1개 행 삽입
- **[NEW]** `DELETE /api/sheets/{sheetId}/rows/{row_index}`: 특정 인덱스의 행 삭제
- **[NEW]** `POST /api/sheets/{sheetId}/columns`: 제일 우측에 1개 열 삽입
- **[NEW]** `DELETE /api/sheets/{sheetId}/columns/{col_index}`: 특정 인덱스의 열 삭제

*주의사항: `service_account`의 Scopes를 쓰기 권한으로 수정합니다.*

#### [NEW] backend/services/google_sheets.py
`service_account.json` 자격 증명을 통해 Google Sheets API와 통신하고, 스프레드시트 데이터를 읽어오는 비즈니스 로직을 구현합니다.

---

### Frontend

React (Vite) 환경에서 백엔드 API를 호출하여 화면에 데이터를 렌더링합니다.

#### [NEW] frontend/src/services/api.js
백엔드의 `/api/sheets` 엔드포인트를 호출하는 fetch 혹은 axios 로직을 추가합니다.

#### [MODIFY] frontend/src/App.jsx
테이블 UI를 개편하여 제어 버튼을 추가합니다.
- **행 제어**: 테이블 우측 최상단에 '+ 행 추가' 버튼 및 각 행 맨 우측에 '🗑 행 삭제' 단추 추가
- **열 제어**: 테이블 상단 헤더 영역 우측에 '+ 열 추가' 버튼 및 각 열명칭 우측에 '🗑 열 삭제' 아이콘 추가
- 추가 및 삭제 버튼 클릭 시 `sheetId`를 기반으로 백엔드 엔드포인트를 호출하며 로딩 피드백을 주고 UI를 재패치(refetch) 합니다.

## Open Questions

> [!WARNING]
> - `service_account.json`에 해당하는 Google Cloud 서비스 계정에 해당 스프레드시트(1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss)에 대한 **읽기 권한(공유)** 이 부여되어 있어야 합니다. 권한이 추가되어 있는지 확인 부탁드립니다.

## Verification Plan

### Automated Tests
- 없음

### Manual Verification
- 백엔드: FastAPI Swagger U(`http://localhost:8000/docs`)에서 `/api/sheets` 엔드포인트 정상 작동 테스트.
- 프론트엔드: 브라우저에서 서버에서 전달한 시트 내용이 정상적으로 테이블 형식으로 렌더링되는지 확인.
