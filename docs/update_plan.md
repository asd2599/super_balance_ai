# [AI 데이터 일괄 수정(Modify) 엔진 기획안]

단순 데이터 추가/삭제를 넘어서, 사용자가 자연어(프롬프트)로 지시하면 AI가 맥락을 파악해 현재 표기된 표(테이블) **전체의 데이터를 분석하고 일괄적으로 수정·편집**해주는 기능을 추가합니다.

## User Review Required

> [!WARNING]
> - **[사용 맥락]** 예를 들어 "모든 '가격' 열의 숫자를 10% 올려줘", "직급을 전부 영문으로 번역해줘", 혹은 "'홍길동'의 나이를 25세로 바꿔줘" 처럼 테이블 전체를 통째로 AI에게 읽히고 수정된 결과물을 받아 덮어쓰기(Overwrite) 하는 기능입니다.
> - **[안전성 보장]** 이 행위 역시 **전체 데이터를 덮어버리는 파괴적인 동작**이므로 곧바로 이전 상태로 롤백할 수 있도록 `Undo / Redo 스택`에 새 명령 주기(`UPDATE_SHEET`)를 신규 등록할 것입니다.

## Proposed Changes

### 백엔드 (FastAPI) 구조 변경

#### [MODIFY] backend/services/ai_generator.py
- **신규 함수 `modify_sheet_content(prompt, current_values)` 추가**:
  - 현재 시트의 전체 데이터 배열(`current_values`)과 유저의 조작 요구(`prompt`)를 병합해 전송.
  - "이 2차원 JSON 배열의 틀을 철저히 유지하되, 나의 요구에 맞게 일부 데이터(셀 값)만 치환하거나 갱신하여 돌려다오." 라는 시스템 메세지를 프롬프팅.

#### [MODIFY] backend/routers/sheets_router.py
- **신규 엔드포인트 `POST /api/sheets/{sheetId}/modify`**:
  - 프론트엔드로부터 `prompt` 문자열을 수신.
  - 구글 서버에서 현재 해당 시트의 원본 데이터를 모두 Fetch 해옴.
  - `ai_generator`를 거쳐 수정된 전체 데이터(`modified_data`)를 확보.
  - `values.update` 함수를 통해 기존 범위를 해당 `modified_data` 배열로 통째로 덮어씀.
  - *History Push:* `history_manager`에 액션 타입 `UPDATE_SHEET`을 선언해, **방금 지워진 원본(`oldData`)**과 **방금 그려진 결과물(`newData`)**을 통째로 Payload에 담아서 보관함.

#### [MODIFY] backend/routers/action_router.py
- **`Undo` / `Redo` 연산자 분기점 추가 처리**:
  - `UPDATE_SHEET`에 대한 역연산 분기 추가.
  - `Undo` 시: `payload`의 `oldData`를 꺼내 원본 자리에 동일하게 `values.update` 수행.
  - `Redo` 시: `payload`의 `newData`를 꺼내 원본 자리에 마저 `values.update` 수행.

---

### 프론트엔드 (React) 구조 변경

#### [MODIFY] frontend/src/App.jsx
- **[기능 버튼 추가]** 우측 데이터제어 버튼 그룹 영역('+ AI 행/열 생성' 근처)에 **`[ 📝 AI로 전체 표 수정 ]`** 버튼을 신규 할당.
- **[Prompt 입력창]** 클릭 시 `window.prompt`를 띄워 "테이블 데이터를 어떻게 일괄 변경할까요?" 라는 다이얼로그 제공.
- 백엔드에 요청 전송 후, 앞서 제작했던 **노란색 로딩 바(로딩 중 UI)** 재활용. 수정 완료 시 자동으로 새롭게 데이터 패칭(Refetch) 수행.

## Open Questions
- "AI수정버튼" 작동 범위를 **'현재 화면에 켜져있는 표 전체'** 대상으로 구상 중입니다. 즉 빈 공간을 클릭하고 버튼을 누른 다음 프롬프트를 쓰면, AI가 알아서 알맞은 셀이나 컬럼을 찾아 전체 표를 변환해주게 됩니다. 이렇게 짓는 것이 맞는지 여쭤봅니다.

## Verification Plan
### Manual Verification
1. 임의의 가격 숫자 범주나, 한글 이름 등이 기재된 표를 연다.
2. `[ 📝 AI 표 전체 일괄 수정 ]` 버튼을 누르고 "모든 이름을 영문 발음으로 번역해" 등 프롬프트를 보낸다.
3. 잠시 후 전체 데이터가 일치되게 갱신되는지 확인한다.
4. 즉시 `↩️ 실행 취소(Undo)`를 눌러 갱신 전의 원상복구 상태로 되돌아가는지 강력하게 테스트한다.
