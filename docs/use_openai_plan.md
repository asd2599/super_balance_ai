# Google Sheets API 연동 구현 계획

주어진 스프레드시트(ID: 1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss)의 데이터를 읽어와 사용자에게 보여주는 기능을 구현합니다. 백엔드에서는 FastAPI와 `service_account.json`을 사용해 인증하고 데이터를 제공하며, 프론트엔드에서는 이를 가져와 화면에 출력합니다.

## User Review Required

> [!WARNING]
> - OpenAI 연동으로 인해 응답(Response)까지 대기 시간이 5~15초 지연될 수 있습니다. UI 로딩 표시에 신경 쓰겠습니다.
> - 열 추가 시 **열의 제목(Header)**을 사용자가 직접 입력받도록 브라우저의 `prompt` 창 혹은 별도의 입력 필드를 띄우려 합니다. 괜찮으신가요?
> - OpenAI에서 반환한 결과가 간혹 시트 데이터와 약간 형식이 다를(환각, Hallucination) 가능성이 있습니다. 추가된 후 사용자가 직관적으로 수정/제거할 수 있는 환경이므로, 생성 시도를 우선적으로 적용토록 하겠습니다.

## Proposed Changes

---

### Backend (FastAPI)

FastAPI 서버를 초기 설정하고 Google API를 연동합니다.

#### [NEW] backend/requirements.txt
필요 라이브러리 목록 작성 (fastapi, uvicorn, google-api-python-client 혹은 gspread, pydantic 등).

#### [MODIFY] backend/requirements.txt
- `openai`, `python-dotenv` 라이브러리를 추가하여 .env에서 `OPENAI_API_KEY` 환경변수를 불러와 파이썬 내에서 활용합니다.

#### [MODIFY] backend/main.py
기존 엔드포인트를 개편하고 삽입/삭제용 라우터를 추가합니다.
- `GET /api/sheets`: 메타데이터에 각 시트의 고유 `sheetId` 정보 포함 (API 갱신 필수)
- `GET /api/sheets/{sheet_name}`: 데이터 패치
- **[MODIFY]** `POST /api/sheets/{sheetId}/rows`: 
  - (AI 로직) 현재 시트의 데이터 목록과 헤더를 읽어와 OpenAI API에 컨텍스트로 전달하고, "기존 데이터의 흐름과 맥락에 맞는 1줄의 새로운 데이터를 유추해달라" 요청합니다.
  - (시트 적용) 생성된 JSON 행 데이터를 Google Sheets 하단 막줄에 `values.append` 형태로 삽입합니다.
- **[MODIFY]** `POST /api/sheets/{sheetId}/columns`: 
  - 프론트엔드에서 전달받은 `new_column_name`을 기반으로 OpenAI API에 기존 행 데이터들(+헤더들)과 함께 컨텍스트로 제공합니다.
  - "이 데이터에 `{new_column_name}`이라는 속성값이 추가되었을 때 들어갈 항목들을 유추해석해 배열로 반환해달라" 요청합니다.
  - 빈 열을 삽입 후, 해당 위치 범위 내에 OpenAI가 내뱉은 결과를 `values.update`로 병합 기입합니다.
- `DELETE /api/sheets/{sheetId}/rows/{row_index}`: 특정 인덱스의 행 삭제
- `DELETE /api/sheets/{sheetId}/columns/{col_index}`: 특정 인덱스의 열 삭제

*주의사항: `service_account`의 Scopes를 쓰기 권한으로 수정합니다.*

#### [NEW] backend/services/google_sheets.py
`service_account.json` 자격 증명을 통해 Google Sheets API와 통신하고, 스프레드시트 데이터를 읽어오는 비즈니스 로직을 구현합니다.

---

### Frontend

React (Vite) 환경에서 백엔드 API를 호출하여 화면에 데이터를 렌더링합니다.

#### [NEW] frontend/src/services/api.js
백엔드의 `/api/sheets` 엔드포인트를 호출하는 fetch 혹은 axios 로직을 추가합니다.

#### [MODIFY] frontend/src/App.jsx
테이블 UI를 개편하여 제어 버튼 및 제목 입력 로직을 추가합니다.
- **행 제어**: 테이블 우측 최상단에 '+ AI 행 생성' 버튼 및 각 행 맨 우측에 '🗑 행 삭제' 단추 추가
- **열 제어**: 테이블 상단 헤더 영역 우측에 '+ AI 열 생성' 버튼 및 각 열명칭 우측에 '🗑 열 삭제' 아이콘 추가
- 열 추가(AI 열 생성) 버튼 클릭 시, 자바스크립트 `prompt()` 창을 띄워 사용자에게 새로 추가할 열의 '제목(이름)'을 입력받게 한 뒤 파라미터(`body` 등)로 백엔드에 전송합니다. 
- 대기 시간이 길어지므로 로딩 시 "AI가 시트 문맥을 분석하여 내용을 채워넣는 중입니다..." 같은 친화적 UI를 보여줍니다.

## Open Questions

> [!WARNING]
> - `service_account.json`에 해당하는 Google Cloud 서비스 계정에 해당 스프레드시트(1gVBHcmkSASco3rDXxjTGXfaMjiWRjYtavBDVP6o41ss)에 대한 **읽기 권한(공유)** 이 부여되어 있어야 합니다. 권한이 추가되어 있는지 확인 부탁드립니다.

## Verification Plan

### Automated Tests
- 없음

### Manual Verification
- 백엔드: FastAPI Swagger U(`http://localhost:8000/docs`)에서 `/api/sheets` 엔드포인트 정상 작동 테스트.
- 프론트엔드: 브라우저에서 서버에서 전달한 시트 내용이 정상적으로 테이블 형식으로 렌더링되는지 확인.
