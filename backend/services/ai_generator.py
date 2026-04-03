import json
from core.config import openai_client

def generate_rows(headers: list, current_values: list, num_rows: int = 1) -> list:
    """기존 데이터를 기반으로 가장 알맞은 N줄의 새로운 데이터들을 일괄 생성합니다."""
    context_str = json.dumps(current_values, ensure_ascii=False)
    prompt = (f"아래 시트 데이터의 맥락을 분석하여, 다음으로 이어질 가장 적절한 {num_rows}줄의 새로운 행 데이터들을 구성해줘.\n"
              f"반드시 JSON 2차원 배열 형식(각 행의 길이는 {len(headers)})으로만 응답해야 해. 마크다운이나 다른 설명은 절대 넣지마.\n"
              f"예시: [[\"값1\", \"값2\"], [\"값3\", \"값4\"]]\n\n"
              f"현존하는 데이터:\n{context_str}")
    
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    ai_reply = completion.choices[0].message.content.strip()
    
    if "```" in ai_reply:
        ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
            
    try:
        new_rows = json.loads(ai_reply)
        if not isinstance(new_rows, list) or (new_rows and not isinstance(new_rows[0], list)):
            new_rows = [new_rows] if isinstance(new_rows, list) else [[]]
    except json.JSONDecodeError:
        new_rows = [[""] * len(headers) for _ in range(num_rows)]

    # 길이 패딩 (num_rows 갯수 및 헤더 길이에 맞게)
    if len(new_rows) != num_rows:
        if len(new_rows) < num_rows:
            new_rows.extend([[""] * len(headers)] * (num_rows - len(new_rows)))
        else:
            new_rows = new_rows[:num_rows]
            
    for row in new_rows:
        if not isinstance(row, list):
            row = []
        if len(row) != len(headers):
            row.extend([""] * max(0, len(headers) - len(row)))
            row[:] = row[:len(headers)]
            
    return new_rows

def generate_column_values(new_column_name: str, num_data_rows: int, current_values: list) -> list:
    """새로운 열 이름에 어울리는 데이터 리스트를 생성합니다."""
    context_str = json.dumps(current_values, ensure_ascii=False)
    prompt = (f"아래 표에 '{new_column_name}' 라는 새로운 열(Column) 특성이 추가되려 해.\n"
              f"각 행의 기존 데이터를 바탕으로 '{new_column_name}'에 들어갈 가장 알맞은 단일 데이터 항목을 각각 유추해줘.\n"
              f"반드시 길이가 딱 {num_data_rows}인 JSON 배열 형태로만 대답해야 해. 마크다운 기호(```)나 부가설명 절대 금지.\n"
              f"예시: [\"값1\", \"값2\", ...]\n\n"
              f"현존하는 데이터:\n{context_str}")
    
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    ai_reply = completion.choices[0].message.content.strip()
    
    if "```" in ai_reply:
        ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
    
    try:
        new_col_data = json.loads(ai_reply)
        if not isinstance(new_col_data, list):
            new_col_data = [] 
    except json.JSONDecodeError:
        new_col_data = []

    if len(new_col_data) != num_data_rows:
        new_col_data = new_col_data[:num_data_rows] + [""] * max(0, num_data_rows - len(new_col_data))
    return new_col_data

def generate_new_sheet(prompt_text: str, all_sheets_context: dict = None) -> list:
    """프롬프트를 바탕으로 제목과 초기 테이블 데이터를 반환합니다. 주변 시트들의 맥락을 함께 참고합니다."""
    # 전체 스프레드시트의 요약 정보를 컨텍스트로 생성
    context_all = ""
    if all_sheets_context:
        context_all = "--- [참고: 전체 스프레드시트 시트 목록 및 데이터 요약] ---\n"
        for s_name, s_data in all_sheets_context.items():
            # 참조용 시트의 헤더와 데이터를 AI가 온전히 파악할 수 있도록 전체(All rows) 전달
            sample = s_data if s_data else []
            context_all += f"시트명: [{s_name}]\n데이터 전체: {json.dumps(sample, ensure_ascii=False)}\n\n"

    prompt = (f"당신은 구글 스프레드시트 템플릿 생성기(AI)입니다.\n"
              f"사용자는 다음과 같은 형태의 템플릿 표 생성을 요청했습니다: '{prompt_text}'\n\n"
              f"{context_all}"
              f"이 목적에 가장 최적화된 테이블 헤더 목록과, 해당 헤더 포맷에 맞는 **10줄 이상의 풍부한 초기 샘플 데이터** 생성을 요구합니다.\n"
              f"특히 다른 시트들의 정보를 참고하여 명칭 규칙(Naming Convention)이나 데이터 간의 연계성(예: 아이템 시트가 있다면 해당 아이템 ID 참조)을 갖도록 하십시오.\n"
              f"단, 반드시 아래와 정확히 똑같은 형태의 JSON 만 반환하세요. 마크다운(`) 등 다른 텍스트는 절대 금지.\n"
              f"{{\"headers\": [\"분류\", \"날짜\"], \"initial_data\": [[\"예시1\", \"2024-01-01\"], [\"예시2\", \"2024-01-02\"]]}}")
    
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    ai_reply = completion.choices[0].message.content.strip()
    
    if "```" in ai_reply:
        ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
    
    ai_data = json.loads(ai_reply)
    headers = ai_data.get("headers", ["설정 오류"])
    initial_data = ai_data.get("initial_data", [])
    
    sheet_data = [headers] + initial_data
    target_col_index = len(headers)
    for row in sheet_data[1:]:
        row.extend([""] * max(0, target_col_index - len(row)))
        row[:] = row[:target_col_index]
        
    return sheet_data

def modify_sheet_content(prompt_text: str, current_values: list, all_sheets_context: dict = None, target_sheet_name: str = "") -> list:
    """사용자 프롬프트에 따라 전체 시트 데이터를 일괄 수정해 반환합니다. 주변 시트들의 맥락을 함께 참고합니다."""
    # 전체 스프레드시트의 요약 정보를 컨텍스트로 생성
    context_all = ""
    if all_sheets_context:
        context_all = "--- [참조: 전체 스프레드시트 시트 목록 및 데이터 요약] ---\n"
        for s_name, s_data in all_sheets_context.items():
            if s_name == target_sheet_name: continue # 현재 시트는 중복 방지
            # 참조용 시트의 데이터를 AI가 온전히 파악할 수 있도록 전체(All rows) 전달
            sample = s_data if s_data else []
            context_all += f"시트명: [{s_name}]\n데이터 전체: {json.dumps(sample, ensure_ascii=False)}\n\n"

    context_str = json.dumps(current_values, ensure_ascii=False)
    prompt = (f"당신은 게임 데이터 분석가이자 스프레드시트 수정 엔진입니다.\n"
              f"사용자는 현재 [{target_sheet_name}] 표의 데이터를 바탕으로 다음과 같이 일괄 수정을 지시했습니다: '{prompt_text}'\n\n"
              f"{context_all}"
              f"--- [현재 수정 대상 시트: {target_sheet_name}] ---\n"
              f"기존의 데이터 2차원 배열 크기나 헤더, 행의 개수가 최대한 유지된 상태에서 명령에 맞게 데이터들만 갱신된 새로운 2차원 배열을 만들어 주세요.\n"
              f"특히 다른 시트들의 데이터를 참고하여 수치적 정합성이나 명칭 통일성(Naming Convention)을 유지하십시오.\n"
              f"반드시 다음과 같은 순수한 JSON 2차원 배열 포맷만 대답해야 합니다. 마크다운(`) 등 다른 텍스트 절대 금지.\n"
              f"현재 표 데이터:\n{context_str}")
    
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )
    ai_reply = completion.choices[0].message.content.strip()
    
    if "```" in ai_reply:
        ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
    
    try:
        modified_data = json.loads(ai_reply)
        if not isinstance(modified_data, list):
            modified_data = current_values
    except json.JSONDecodeError:
        modified_data = current_values
    
    return modified_data


def summarize_action_with_ai(action_type: str, payload: dict) -> str:
    """작업 로그용 페이로드를 읽고 어떠한 변경사항인지 사람이 읽기 쉬운 1문장으로 요약합니다."""
    # 페이로드가 너무 클 수 있으므로 적절히 덤프
    payload_str = json.dumps(payload, ensure_ascii=False)
    if len(payload_str) > 1500:
        payload_str = payload_str[:1500] + "...(이하 생략)"
        
    prompt = (
        f"당신은 게임 데이터 분석가의 비서입니다. 방금 시스템에서 '{action_type}' 명칭을 가진 작업(이벤트)이 발생했습니다.\n"
        f"작업 세부 내용(JSON): {payload_str}\n\n"
        f"이 데이터를 분석해서, 사용자가 알기 쉽게 '어떤 테이블(시트명)에 어떤 핵심 데이터가 추가/수정/삭제 되었는지' 구체적이고 명료한 한국어 1문장으로 요약해 주세요. (가급적 50자 이내)\n"
        f"- 반드시 포함할 요소: '테이블(시트) 이름', '핵심 데이터 명칭이나 수치', '발생한 행위(추가됨, 삭제됨, 변환됨 등)'\n"
        f"- 예시 1: 'ItemTable' 테이블에 'ITEM_007(플레이트 메일)' 데이터가 새롭게 추가되었습니다.\n"
        f"- 예시 2: 'MonsterStats' 테이블의 3번째 행(오크 전사) 데이터가 삭제되었습니다.\n"
        f"- 예시 3: 'StageBalance' 테이블 전체 데이터의 공격력/체력 수치가 20% 상향되도록 일괄 변환(수정)되었습니다."
    )
    
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=80,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI Logging Error: {e}")
        return f"{action_type} 작업 수행됨 (요약 실패)"

def audit_balance_anomalies(current_values: list, all_sheets_data: dict = None, target_sheet_name: str = "") -> dict:
    """테이블 전체를 스캔하여 구조적 밸런스 오류나 기획 미스(Anomaly)를 찾아냅니다. 다른 시트들도 함께 분석합니다."""
    if not current_values or len(current_values) <= 1:
        return {"issues": [], "status": "no_data"}
    
    # 전역 밸런스 컨텍스트 구성
    context_all = ""
    if all_sheets_data:
        context_all = "\n--- [전체 스프레드시트 참고 데이터] ---\n"
        for s_name, s_data in all_sheets_data.items():
            if s_name == target_sheet_name: continue
            # 참조용 데이터 전송량을 완전히 개방하여 시트의 모든 맥락 파악이 가능하게 함
            sample = s_data if s_data else []
            context_all += f"시트 [{s_name}]: {json.dumps(sample, ensure_ascii=False)}\n"

    context_str = json.dumps(current_values, ensure_ascii=False)
    prompt = (
        f"당신은 최고 수준의 게임 밸런스 디자이너입니다. 제공된 데이터를 분석하여 시스템적 모순을 찾아내야 합니다.\n"
        f"현재 분석 대상 시트는 [{target_sheet_name}] 입니다.\n"
        f"{context_all}\n"
        f"--- [분석 대상 시트 데이터: {target_sheet_name}] ---\n"
        f"{context_str}\n\n"
        f"위 데이터를 바탕으로, [{target_sheet_name}] 내의 데이터가 다른 시트의 수치와 비교했을 때 부자연스럽거나(예: 보상 대비 아이템 가격이 비정상임), "
        f"자체적인 밸런스 붕괴 요소가 있는 행을 최대 3개 찾아 보고해 주세요.\n"
        f"반드시 다음과 같은 순수한 JSON 객체 형식만 대답해야 합니다. 마크다운(`) 등 다른 텍스트는 절대 금지합니다.\n"
        f"{{\n"
        f"  \"issues\": [\n"
        f"    {{\"row_index\": 3, \"issue\": \"현재 시트의 [검] 가격이 'Rewards' 시트의 골드 획득량 대비 너무 비싸서 초반 진행이 불가능합니다.\"}}\n"
        f"  ],\n"
        f"  \"status\": \"detected\"\n"
        f"}}"
    )
    
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        ai_reply = completion.choices[0].message.content.strip()
        
        if "```" in ai_reply:
            ai_reply = ai_reply.replace("```json", "").replace("```", "").strip()
            
        result = json.loads(ai_reply)
        return result
    except Exception as e:
        print(f"Audit Error: {e}")
        return {"issues": [{"row_index": -1, "issue": f"AI 분석 중 오류가 발생했습니다: {str(e)}"}], "status": "error"}
