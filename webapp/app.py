import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    import gspread
except Exception:
    gspread = None


st.set_page_config(
    page_title="학생용 AI 웹앱 메이커",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.main-title { font-size: 2.1rem; font-weight: 800; margin-bottom: 0.25rem; }
.sub-title { color: #6b7280; margin-bottom: 1rem; }
.card {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    background: linear-gradient(145deg, #ffffff, #f8fafc);
}
.tip {
    border-left: 4px solid #60a5fa;
    padding: 0.6rem 0.8rem;
    background: #eff6ff;
    border-radius: 8px;
    margin-bottom: 0.7rem;
}
</style>
""",
    unsafe_allow_html=True,
)

LOCAL_BOARD_FILE = Path(__file__).resolve().parent / "shared_links.json"


def init_state() -> None:
    defaults = {
        "api_key_sidebar": "",
        "ideas": [],
        "selected_idea": "",
        "selected_target": "학생",
        "selected_features": "",
        "prompt_pack": {},
        "topic_input": "학교 생활",
        "interest_input": "게임, 음악, 친구, 진로",
        "level": "입문",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_secret_api_key() -> Optional[str]:
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if isinstance(key, str) and key.strip():
            return key.strip()
    except Exception:
        return None
    return None


def get_active_api_key() -> Optional[str]:
    secret_key = get_secret_api_key()
    if secret_key:
        return secret_key
    typed = st.session_state.api_key_sidebar.strip()
    return typed if typed else None


def normalize_json(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```json\\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\\s*", "", text)
    text = re.sub(r"\\s*```$", "", text)
    return text.strip()


def parse_json_array(raw: str) -> Optional[List[Dict[str, Any]]]:
    text = normalize_json(raw)
    try:
        arr = json.loads(text)
        if isinstance(arr, list):
            return arr
    except Exception:
        pass

    found = re.search(r"\[\s*{.*}\s*]", text, flags=re.DOTALL)
    if not found:
        return None

    try:
        arr = json.loads(found.group(0))
        if isinstance(arr, list):
            return arr
    except Exception:
        return None
    return None


def call_gemini(prompt: str, temperature: float = 0.8) -> str:
    if genai is None:
        raise ValueError("google-generativeai 라이브러리가 없습니다.")

    api_key = get_active_api_key()
    if not api_key:
        raise ValueError("Gemini API 키가 없습니다.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "top_p": 0.95,
            "max_output_tokens": 4096,
        },
    )

    text = ""
    if hasattr(response, "text") and response.text:
        text = response.text
    elif hasattr(response, "candidates") and response.candidates:
        parts = response.candidates[0].content.parts
        if parts and hasattr(parts[0], "text"):
            text = parts[0].text or ""

    if not text.strip():
        raise ValueError("Gemini 응답이 비어 있습니다.")
    return text


def fallback_ideas(topic: str, count: int) -> List[Dict[str, Any]]:
    base = [
        {
            "app_name": "시험 루틴 레벨업",
            "target_user": "시험 준비 학생",
            "problem": "계획은 있지만 꾸준히 실천하기 어렵다",
            "core_features": ["오늘 할 일 자동 추천", "집중 타이머", "달성률 시각화"],
            "fun_ui": ["레벨 배지", "이모지 피드백", "진행도 바"],
            "mini_mission": "7일 연속 달성 챌린지",
        },
        {
            "app_name": "진로 궁금해 AI",
            "target_user": "진로 고민 학생",
            "problem": "나에게 맞는 진로 정보를 찾기 어렵다",
            "core_features": ["관심사 질문", "진로 추천", "실천 로드맵"],
            "fun_ui": ["카드형 결과", "탭 탐색", "진로 매칭 점수"],
            "mini_mission": "친구와 진로 결과 비교",
        },
        {
            "app_name": "학교생활 고민 힐링소",
            "target_user": "일상 고민이 있는 학생",
            "problem": "고민을 정리하고 행동으로 옮기기 어렵다",
            "core_features": ["고민 분류", "해결 아이디어", "실천 체크리스트"],
            "fun_ui": ["감정 버튼", "응원 카드", "체크 애니메이션"],
            "mini_mission": "응원 문장 뽑기 기능",
        },
    ]

    out: List[Dict[str, Any]] = []
    for i in range(count):
        item = base[i % len(base)].copy()
        item["app_name"] = f"{item['app_name']} - {topic} {i + 1}"
        out.append(item)
    return out


def generate_ideas(topic: str, interests: str, level: str, count: int) -> List[Dict[str, Any]]:
    prompt = f"""
너는 학생 프로젝트 아이디어 코치야.
주제 키워드: {topic}
관심사: {interests}
난이도: {level}
개수: {count}

반드시 JSON 배열만 출력하고 다른 텍스트는 금지.
각 원소 키:
- app_name
- target_user
- problem
- core_features (문자열 배열 3개)
- fun_ui (문자열 배열 3개)
- mini_mission
""".strip()

    try:
        raw = call_gemini(prompt, temperature=0.85)
        parsed = parse_json_array(raw)
        if not parsed:
            return fallback_ideas(topic, count)

        cleaned: List[Dict[str, Any]] = []
        for item in parsed[:count]:
            core = item.get("core_features", [])
            ui = item.get("fun_ui", [])
            if not isinstance(core, list):
                core = [str(core)]
            if not isinstance(ui, list):
                ui = [str(ui)]

            cleaned.append(
                {
                    "app_name": str(item.get("app_name", "학생 맞춤 웹앱")),
                    "target_user": str(item.get("target_user", "학생")),
                    "problem": str(item.get("problem", "문제 정의 필요")),
                    "core_features": [str(x) for x in core[:3]] if core else ["기능1", "기능2", "기능3"],
                    "fun_ui": [str(x) for x in ui[:3]] if ui else ["사이드바", "버튼", "결과 카드"],
                    "mini_mission": str(item.get("mini_mission", "작은 미션 하나 추가")),
                }
            )

        if len(cleaned) < count:
            cleaned.extend(fallback_ideas(topic, count - len(cleaned)))
        return cleaned[:count]
    except Exception:
        return fallback_ideas(topic, count)


def fill_prompt_from_idea(idea: Dict[str, Any]) -> None:
    st.session_state.selected_idea = idea["app_name"] + "\n문제: " + idea["problem"]
    st.session_state.selected_target = idea["target_user"]
    st.session_state.selected_features = ", ".join(idea["core_features"] + idea["fun_ui"])
    st.toast("선택한 아이디어가 프롬프트 도우미에 반영됐어요!", icon="✅")


def build_prompt_pack(app_idea: str, target_user: str, required_features: str, level: str) -> Dict[str, str]:
    html_prompt = f"""
# 역할
너는 학생 프로젝트를 완성도 높게 구현하는 시니어 프론트엔드 개발자다.

# 목표
아래 아이디어를 바탕으로, 브라우저에서 바로 실행 가능한 완성형 `index.html` 단일 파일을 생성하라.

# 프로젝트 정보
- 아이디어: {app_idea}
- 타겟 사용자: {target_user}
- 난이도: {level}
- 필수 기능: {required_features}

# 반드시 지킬 구현 요구사항
1) HTML/CSS/JavaScript를 한 파일에 모두 포함한다.
2) 한국어 UI 텍스트를 사용한다.
3) 모바일 반응형을 지원한다.
4) 아래 UI 요소를 반드시 포함한다:
   - 상단 타이틀 섹션
   - 입력 폼
   - 실행 버튼
   - 결과 카드 영역
   - 상태 배지 또는 진행도 표시
5) 빈 입력/오류 상황에서 사용자에게 친절한 경고 메시지를 보여준다.
6) 주석을 통해 초보 학생도 구조를 이해할 수 있게 작성한다.
7) 코드 외 설명은 출력하지 말고, 오직 완성된 코드만 출력한다.

# 출력 형식
- ```html 코드블록 하나로만 출력
""".strip()

    streamlit_prompt = f"""
# 역할
너는 Streamlit + Gemini API 앱 제작 멘토다.

# 목표
아래 아이디어를 복사 즉시 실행 가능한 단일 `app.py` 파일로 완성하라.

# 프로젝트 정보
- 아이디어: {app_idea}
- 타겟 사용자: {target_user}
- 난이도: {level}
- 필수 기능: {required_features}

# 필수 구현 조건
1) `st.secrets["GEMINI_API_KEY"]`를 우선 사용하고, 없으면 사이드바 입력으로 대체.
2) 사이드바, 탭, 컬럼, 버튼, 진행도/메트릭 UI를 포함.
3) 입력 검증과 예외 처리를 포함.
4) 세션 상태(`st.session_state`)를 사용해 결과를 유지.
5) 학생이 보기 쉽게 한국어 주석을 적절히 추가.
6) 실행 가능한 완성 코드만 출력(중간 생략 금지).
7) 코드 뒤에 `requirements.txt` 내용도 함께 출력.

# 출력 형식
- 먼저 ```python 코드블록(app.py 전체)
- 다음 ```txt 코드블록(requirements.txt)
""".strip()

    convert_prompt = f"""
# 역할
너는 HTML 웹앱을 Streamlit으로 구조 변환하는 전문가다.

# 목표
내가 가진 HTML 기반 아이디어를 기능적으로 동일한 Streamlit `app.py`로 변환하라.

# 변환 대상 정보
- 아이디어: {app_idea}
- 타겟 사용자: {target_user}
- 필수 기능: {required_features}

# 변환 규칙
1) UI 의미를 유지하되 Streamlit 컴포넌트로 재구성.
2) 함수 단위로 분리해서 가독성 확보.
3) 세션 상태로 사용자 입력/결과 유지.
4) 오류 메시지는 한국어로 친절하게 제공.
5) 코드 생략 없이 전체 `app.py`를 출력.

# 출력 형식
- ```python 코드블록 하나만 출력
""".strip()

    return {
        "html_prompt": html_prompt,
        "streamlit_prompt": streamlit_prompt,
        "convert_prompt": convert_prompt,
    }


def process_flow_markdown() -> str:
    return "\n".join(
        [
            "## 학생용 웹앱 제작 순서",
            "",
            "1. 아이디어 추천 탭에서 주제 기반 아이디어를 뽑는다.",
            "2. 마음에 드는 아이디어를 선택해 프롬프트 도우미로 자동 입력한다.",
            "3. HTML 프롬프트 또는 Streamlit 프롬프트를 복사해 Gemini에 붙여넣는다.",
            "4. 생성된 코드를 로컬에서 실행해 UI와 기능을 확인한다.",
            "5. GitHub에 업로드한다.",
            "6. Streamlit Community Cloud로 배포한다.",
            "7. 공유 탭에서 링크를 제출하고 친구들 작품을 둘러본다.",
        ]
    )


def is_valid_http_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", url.strip()))


# -------- 공유 보드 저장소 (자동 선택) --------
def _can_use_google_sheets() -> bool:
    if gspread is None:
        return False
    try:
        if "GOOGLE_SHEETS_SPREADSHEET_ID" not in st.secrets:
            return False
        if "GOOGLE_SERVICE_ACCOUNT" not in st.secrets:
            return False
    except Exception:
        return False
    return True


def _get_google_rows() -> List[Dict[str, str]]:
    spreadsheet_id = st.secrets["GOOGLE_SHEETS_SPREADSHEET_ID"]
    service_account_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    client = gspread.service_account_from_dict(service_account_info)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        ws = spreadsheet.worksheet("shared_links")
    except Exception:
        ws = spreadsheet.add_worksheet(title="shared_links", rows=500, cols=8)
        ws.append_row(["name", "title", "description", "url", "submitted_at"])

    records = ws.get_all_records()
    rows: List[Dict[str, str]] = []
    for r in records:
        rows.append(
            {
                "name": str(r.get("name", "")),
                "title": str(r.get("title", "")),
                "description": str(r.get("description", "")),
                "url": str(r.get("url", "")),
                "submitted_at": str(r.get("submitted_at", "")),
            }
        )
    rows.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    return rows


def _append_google_row(name: str, title: str, description: str, url: str) -> None:
    spreadsheet_id = st.secrets["GOOGLE_SHEETS_SPREADSHEET_ID"]
    service_account_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    client = gspread.service_account_from_dict(service_account_info)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        ws = spreadsheet.worksheet("shared_links")
    except Exception:
        ws = spreadsheet.add_worksheet(title="shared_links", rows=500, cols=8)
        ws.append_row(["name", "title", "description", "url", "submitted_at"])

    current = ws.get_all_records()
    if any(str(item.get("url", "")).strip() == url.strip() for item in current):
        raise ValueError("이미 제출된 링크예요. 다른 링크를 입력해 주세요.")

    ws.append_row([
        name.strip(),
        title.strip(),
        description.strip(),
        url.strip(),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ])


def _load_local_rows() -> List[Dict[str, str]]:
    if not LOCAL_BOARD_FILE.exists():
        return []
    try:
        data = json.loads(LOCAL_BOARD_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
    except Exception:
        return []

    rows: List[Dict[str, str]] = []
    for r in data:
        if not isinstance(r, dict):
            continue
        rows.append(
            {
                "name": str(r.get("name", "")),
                "title": str(r.get("title", "")),
                "description": str(r.get("description", "")),
                "url": str(r.get("url", "")),
                "submitted_at": str(r.get("submitted_at", "")),
            }
        )
    rows.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    return rows


def _append_local_row(name: str, title: str, description: str, url: str) -> None:
    rows = _load_local_rows()
    if any(item.get("url", "").strip() == url.strip() for item in rows):
        raise ValueError("이미 제출된 링크예요. 다른 링크를 입력해 주세요.")

    rows.insert(
        0,
        {
            "name": name.strip(),
            "title": title.strip(),
            "description": description.strip(),
            "url": url.strip(),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    LOCAL_BOARD_FILE.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def load_shared_rows() -> List[Dict[str, str]]:
    if _can_use_google_sheets():
        try:
            return _get_google_rows()
        except Exception:
            return _load_local_rows()
    return _load_local_rows()


def add_shared_row(name: str, title: str, description: str, url: str) -> None:
    if _can_use_google_sheets():
        try:
            _append_google_row(name, title, description, url)
            return
        except Exception:
            pass
    _append_local_row(name, title, description, url)


init_state()

st.markdown('<div class="main-title">✨ 학생용 AI 웹앱 메이커</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">핵심 기능 전체 + 공유 탭은 설정 없이 바로 동작해요.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Gemini API 설정")
    secret_key = get_secret_api_key()
    if secret_key:
        st.success("secrets에서 API 키를 찾았어요.")
    else:
        st.session_state.api_key_sidebar = st.text_input(
            "Gemini API 키(선택)",
            type="password",
            value=st.session_state.api_key_sidebar,
            placeholder="AIza...",
            help="키가 없어도 기본 아이디어/프롬프트 기능은 동작해요.",
        )

    st.markdown("---")
    st.session_state.level = st.selectbox("난이도", ["입문", "기초", "중급"], index=0)


k1, k2, k3 = st.columns(3)
with k1:
    st.metric("핵심 기능", "모두 포함")
with k2:
    st.metric("공유 탭", "즉시 사용 가능")
with k3:
    st.metric("현재 난이도", st.session_state.level)


tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "0. 제작 과정 설명",
        "1. 웹앱 아이디어 추천",
        "2. 프롬프트 생성 도우미",
        "3. HTML/app.py 생성법",
        "4. GitHub 업로드 방법",
        "5. Streamlit 배포 방법",
        "6. 친구들 링크 접속하기",
    ]
)

with tab0:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(process_flow_markdown())
    st.markdown("</div>", unsafe_allow_html=True)

with tab1:
    st.subheader("웹앱 아이디어 추천")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.topic_input = st.text_input("주제/키워드", value=st.session_state.topic_input)
    with c2:
        st.session_state.interest_input = st.text_input("관심사", value=st.session_state.interest_input)

    count = st.slider("추천 개수", 3, 10, 5)
    if st.button("아이디어 생성", type="primary", use_container_width=True):
        st.session_state.ideas = generate_ideas(
            st.session_state.topic_input,
            st.session_state.interest_input,
            st.session_state.level,
            count,
        )

    if st.session_state.ideas:
        st.markdown('<div class="tip">마음에 드는 아이디어에서 <b>이 아이디어 선택</b>을 누르면 2번 탭에 자동 입력됩니다.</div>', unsafe_allow_html=True)
        for i, idea in enumerate(st.session_state.ideas, start=1):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {i}. {idea['app_name']}")
            st.markdown(f"- 타겟: {idea['target_user']}")
            st.markdown(f"- 문제: {idea['problem']}")
            st.markdown("- 핵심 기능")
            for f in idea["core_features"]:
                st.markdown(f"  - {f}")
            st.markdown("- 재미 UI")
            for u in idea["fun_ui"]:
                st.markdown(f"  - {u}")
            if st.button("이 아이디어 선택", key=f"pick_{i}", use_container_width=True):
                fill_prompt_from_idea(idea)
            st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.subheader("프롬프트 생성 도우미")
    app_idea = st.text_area("아이디어 설명", value=st.session_state.selected_idea, height=90)
    target_user = st.text_input("타겟 사용자", value=st.session_state.selected_target)
    required_features = st.text_area("필수 기능", value=st.session_state.selected_features, height=90)

    if st.button("프롬프트 3종 만들기", type="primary", use_container_width=True):
        if not app_idea.strip() or not required_features.strip():
            st.error("아이디어 설명과 필수 기능을 입력해 주세요.")
        else:
            st.session_state.prompt_pack = build_prompt_pack(
                app_idea.strip(),
                target_user.strip() or "학생",
                required_features.strip(),
                st.session_state.level,
            )

    if st.session_state.prompt_pack:
        pack = st.session_state.prompt_pack

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### A. HTML 코드 생성 프롬프트")
        st.code(pack["html_prompt"], language="text")
        st.download_button("HTML 프롬프트 다운로드", data=pack["html_prompt"], file_name="prompt_html.txt", mime="text/plain")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### B. Streamlit app.py 생성 프롬프트")
        st.code(pack["streamlit_prompt"], language="text")
        st.download_button("app.py 프롬프트 다운로드", data=pack["streamlit_prompt"], file_name="prompt_app_py.txt", mime="text/plain")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### C. HTML → app.py 변환 프롬프트")
        st.code(pack["convert_prompt"], language="text")
        st.download_button("변환 프롬프트 다운로드", data=pack["convert_prompt"], file_name="prompt_convert.txt", mime="text/plain")
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("- 먼저 HTML 버전을 만들고, 그다음 app.py 변환을 추천해요.")
    st.markdown("- 출력 형식을 꼭 지정하면 코드 품질이 올라가요.")
    st.markdown("- 에러가 나면 에러 문구 그대로 Gemini에 붙여넣어 수정 요청하세요.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.code(
        """git init
git add .
git commit -m "feat: my webapp"
git branch -M main
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main""",
        language="bash",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with tab5:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("1) [share.streamlit.io](https://share.streamlit.io/) 로그인")
    st.markdown("2) New app 클릭")
    st.markdown("3) Repository 선택")
    st.markdown("4) Main file path 설정")
    st.markdown("5) Deploy 클릭")
    st.markdown("</div>", unsafe_allow_html=True)

with tab6:
    st.subheader("친구들 링크 접속하기")
    st.markdown('<div class="tip">기본 모드(설정 없음): 앱 내부 파일에 자동 저장되어 즉시 동작합니다. Google Sheets가 설정되어 있으면 자동으로 시트에 저장됩니다.</div>', unsafe_allow_html=True)

    with st.form("share_form", clear_on_submit=True):
        name = st.text_input("이름")
        title = st.text_input("웹앱 제목")
        description = st.text_input("한 줄 설명")
        url = st.text_input("스트림릿 링크", placeholder="https://...streamlit.app")
        submit = st.form_submit_button("제출")

    if submit:
        if not name.strip() or not title.strip() or not description.strip() or not url.strip():
            st.error("모든 항목을 입력해 주세요.")
        elif not is_valid_http_url(url):
            st.error("링크는 http:// 또는 https:// 로 시작해야 해요.")
        else:
            try:
                add_shared_row(name, title, description, url)
                st.success("제출 완료! 아래 목록에서 친구들과 공유해 보세요.")
            except Exception as exc:
                st.error(str(exc))

    rows = load_shared_rows()
    st.caption(f"총 {len(rows)}개 작품")

    if not rows:
        st.info("아직 제출된 작품이 없어요.")
    else:
        for idx, row in enumerate(rows, start=1):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c_left, c_right = st.columns([4, 1])
            with c_left:
                st.markdown(f"### {idx}. {row['title']}")
                st.markdown(f"- 제출자: **{row['name']}**")
                st.markdown(f"- 설명: {row['description']}")
                st.caption(f"제출 시각: {row['submitted_at']}")
            with c_right:
                st.link_button("바로 접속", row["url"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"업데이트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
