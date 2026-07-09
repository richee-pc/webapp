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
    initial_sidebar_state="collapsed",
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

GEMINI_URL = "https://gemini.google.com/"
GITHUB_URL = "https://github.com/"
STREAMLIT_URL = "https://share.streamlit.io/"


def init_state() -> None:
    defaults = {
        "ideas": [],
        "selected_idea": "",
        "selected_target": "학생",
        "selected_features": "",
        "selected_design": "",
        "prompt_pack": {},
        "topic_input": "학교 생활",
        "interest_input": "게임, 음악, 친구, 진로",
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
    return get_secret_api_key()


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


def generate_ideas(topic: str, interests: str, count: int) -> List[Dict[str, Any]]:
    prompt = f"""
너는 학생 프로젝트 아이디어 코치야.
주제 키워드: {topic}
관심사: {interests}
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
    st.session_state.selected_design = ", ".join(idea["fun_ui"])
    st.toast("선택한 아이디어가 프롬프트 도우미에 반영됐어요!", icon="✅")


def build_prompt_pack(
    app_idea: str,
    target_user: str,
    required_features: str,
    design_style: str,
) -> Dict[str, str]:
    design_section = design_style.strip() or "밝고 친근한 학생용 UI, 카드형 레이아웃, 모바일 반응형"

    html_prompt = f"""
# 역할
너는 학생 프로젝트를 완성도 높게 구현하는 시니어 프론트엔드 개발자다.

# 목표
아래 아이디어를 바탕으로, 브라우저에서 바로 실행 가능한 완성형 `index.html` 단일 파일을 생성하라.

# 프로젝트 정보
- 아이디어: {app_idea}
- 타겟 사용자: {target_user}
- 필수 기능: {required_features}
- 원하는 디자인/분위기: {design_section}

# 반드시 지킬 구현 요구사항
1) HTML/CSS/JavaScript를 한 파일에 모두 포함한다.
2) 한국어 UI 텍스트를 사용한다.
3) 모바일 반응형을 지원한다.
4) 위 "원하는 디자인/분위기"를 색상, 폰트, 레이아웃, 버튼 스타일에 반영한다.
5) 아래 UI 요소를 반드시 포함한다:
   - 상단 타이틀 섹션
   - 입력 폼
   - 실행 버튼
   - 결과 카드 영역
   - 상태 배지 또는 진행도 표시
6) 빈 입력/오류 상황에서 사용자에게 친절한 경고 메시지를 보여준다.
7) 주석을 통해 초보 학생도 구조를 이해할 수 있게 작성한다.
8) 코드 외 설명은 출력하지 말고, 오직 완성된 코드만 출력한다.

# 출력 형식
- ```html 코드블록 하나로만 출력
""".strip()

    streamlit_prompt = f"""
# 역할
너는 Streamlit 배포 전문가다.

# 목표
`htmls/index.html` 파일을 Streamlit 앱에서 열어 보여주는 배포용 `app.py`와 `requirements.txt`를 생성하라.

# 프로젝트 정보
- 아이디어: {app_idea}
- 타겟 사용자: {target_user}
- 필수 기능: {required_features}
- 원하는 디자인/분위기: {design_section}

# 저장소 폴더 구조 (반드시 이 구조를 전제로 작성)
```
내-웹앱/
├── app.py
├── requirements.txt
└── htmls/
    └── index.html
```

# 필수 구현 조건
1) `app.py`는 `htmls/index.html` 파일을 읽어 `st.components.v1.html()` 또는 동등한 방식으로 전체 화면에 렌더링한다.
2) `index.html` 경로는 `Path(__file__).resolve().parent / "htmls" / "index.html"`처럼 상대 경로로 찾는다.
3) 파일이 없을 때는 한국어로 친절한 안내 메시지를 보여준다.
4) 페이지 제목과 간단한 소개 문구를 한국어로 표시한다.
5) `requirements.txt`에는 `streamlit`만 포함한다.
6) 코드 생략 없이 전체 파일을 출력한다.

# 출력 형식
- 먼저 ```python 코드블록(app.py 전체)
- 다음 ```txt 코드블록(requirements.txt)
""".strip()

    convert_prompt = f"""
# 역할
너는 HTML 웹앱을 Streamlit 배포용 래퍼로 변환하는 전문가다.

# 목표
이미 만든 `htmls/index.html`을 Streamlit Community Cloud에서 열 수 있는 `app.py`로 변환하라.

# 변환 대상 정보
- 아이디어: {app_idea}
- 타겟 사용자: {target_user}
- 필수 기능: {required_features}
- 원하는 디자인/분위기: {design_section}

# 변환 규칙
1) HTML 내용은 그대로 두고, `app.py`가 `htmls/index.html`을 읽어 보여주게 한다.
2) `st.components.v1.html(..., height=..., scrolling=True)`로 넓은 화면에 표시한다.
3) 파일 경로는 `Path(__file__).resolve().parent / "htmls" / "index.html"`을 사용한다.
4) 오류 메시지는 한국어로 친절하게 제공한다.
5) 코드 생략 없이 전체 `app.py`와 `requirements.txt`를 출력한다.

# 출력 형식
- 먼저 ```python 코드블록(app.py 전체)
- 다음 ```txt 코드블록(requirements.txt)
""".strip()

    return {
        "html_prompt": html_prompt,
        "streamlit_prompt": streamlit_prompt,
        "convert_prompt": convert_prompt,
    }


def process_flow_markdown() -> str:
    return """
## 학생용 웹앱 제작·배포 로드맵

> **핵심 흐름:** 아이디어 → 프롬프트 → HTML 제작 → GitHub 업로드 → app.py 생성 → 전체 업로드 → Streamlit 배포·공유

---

### 1단계: 기획 — 아이디어 구상
- **누구를 위한 앱인가?** (예: 시험 준비하는 친구, 동아리 부원)
- **어떤 문제를 풀까?** (예: 공부 계획이 자꾸 밀림)
- **핵심 기능 3가지**를 적는다.
- **원하는 디자인**도 함께 정한다. (예: 파란색·미니멀, 게임 느낌, 카드형 레이아웃)

✅ **완료 기준:** 아이디어 + 기능 + 디자인 메모가 준비됨

---

### 2단계: 프롬프트 만들기
- **1번 탭**에서 아이디어를 추천받거나, 직접 적은 내용을 **2번 탭**에 입력한다.
- **기능**뿐 아니라 **디자인/분위기**도 프롬프트에 포함한다.
- 아래 **2종 프롬프트**를 준비한다.
  - **A. HTML 생성 프롬프트** → `index.html` 만들 때 사용
  - **B. Streamlit 배포 프롬프트** → `app.py` 만들 때 사용

✅ **완료 기준:** A·B 프롬프트를 복사해 둠

---

### 3단계: HTML 웹앱 만들기
1. Gemini에 **A 프롬프트**를 붙여넣는다.
2. 생성된 `index.html` 코드를 복사한다.
3. 컴퓨터에 `index.html`로 저장한 뒤, 브라우저로 열어 **UI·기능**을 확인한다.
4. 마음에 들 때까지 Gemini에게 수정을 요청한다. (에러 문구를 그대로 붙여넣기)

✅ **완료 기준:** 브라우저에서 잘 동작하는 `index.html` 확보

---

### 4단계: GitHub 저장소 준비
1. [GitHub](https://github.com)에서 **새 저장소(Repository)** 를 만든다.
2. 아래 **폴더 구조**를 미리 계획한다.

```
내-웹앱/
├── app.py              ← 5단계에서 추가
├── requirements.txt    ← 5단계에서 추가
└── htmls/
    └── index.html      ← 3단계 결과
```

3. `htmls` 폴더를 만들고, 그 안에 `index.html`을 넣는다.
4. GitHub에 **첫 업로드**를 한다. (웹에서 직접 업로드하거나 Git 명령어 사용)

✅ **완료 기준:** GitHub에 `htmls/index.html`이 올라가 있음

---

### 5단계: Streamlit 배포용 app.py 만들기
1. Gemini에 **B 프롬프트**를 붙여넣는다.
2. 생성된 `app.py`와 `requirements.txt`를 복사한다.
3. `app.py`는 **`htmls/index.html` 파일을 열어 보여주는 역할**을 한다.
4. 로컬에서 `streamlit run app.py`로 미리 확인한다. (선택)

✅ **완료 기준:** `app.py` + `requirements.txt` 준비 완료

---

### 6단계: GitHub에 전체 파일 업로드
1. 저장소 루트에 `app.py`, `requirements.txt`를 추가한다.
2. 최종 구조가 아래와 같은지 확인한다.

```
내-웹앱/
├── app.py
├── requirements.txt
└── htmls/
    └── index.html
```

3. 변경 사항을 GitHub에 **다시 업로드(커밋·푸시)** 한다.

✅ **완료 기준:** GitHub에 3개 파일(또는 폴더 포함 전체 구조)이 모두 있음

---

### 7단계: Streamlit으로 배포하고 공유
1. [share.streamlit.io](https://share.streamlit.io/)에 GitHub 계정으로 로그인한다.
2. **New app** → 저장소 선택 → **Main file path**에 `app.py` 입력 → **Deploy**
3. 배포가 끝나면 `https://xxxx.streamlit.app` 형태의 **공유 링크**가 생긴다.
4. 링크를 친구들에게 보내고, **6번 탭(친구들 링크 접속하기)** 에도 제출한다.

✅ **완료 기준:** 친구가 링크로 내 웹앱에 접속 가능

---

### 한눈에 보는 순서 요약

| 순서 | 할 일 | 결과물 |
|------|--------|--------|
| 1 | 아이디어·디자인 구상 | 기획 메모 |
| 2 | 프롬프트 2종 생성 | A(HTML), B(app.py) |
| 3 | Gemini로 HTML 생성 | `index.html` |
| 4 | GitHub 저장소 + htmls 업로드 | `htmls/index.html` |
| 5 | Gemini로 app.py 생성 | `app.py`, `requirements.txt` |
| 6 | GitHub에 전체 업로드 | 완성된 저장소 |
| 7 | Streamlit 배포·공유 | 공유 URL |
""".strip()


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

link1, link2, link3 = st.columns(3)
with link1:
    st.link_button("✨ Gemini 열기", GEMINI_URL, use_container_width=True, help="프롬프트를 붙여넣어 코드를 생성해요")
with link2:
    st.link_button("🐙 GitHub 열기", GITHUB_URL, use_container_width=True, help="저장소를 만들고 파일을 업로드해요")
with link3:
    st.link_button("🚀 Streamlit 배포 열기", STREAMLIT_URL, use_container_width=True, help="웹앱을 배포하고 공유 링크를 받아요")

k1, k2 = st.columns(2)
with k1:
    st.metric("핵심 기능", "모두 포함")
with k2:
    st.metric("공유 탭", "즉시 사용 가능")


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
    st.markdown("---")
    st.markdown("**바로가기**")
    t0c1, t0c2, t0c3 = st.columns(3)
    with t0c1:
        st.link_button("Gemini (3·5단계)", GEMINI_URL, use_container_width=True)
    with t0c2:
        st.link_button("GitHub (4·6단계)", GITHUB_URL, use_container_width=True)
    with t0c3:
        st.link_button("Streamlit (7단계)", STREAMLIT_URL, use_container_width=True)
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
    st.link_button("✨ Gemini에서 코드 생성하기", GEMINI_URL, help="프롬프트를 복사한 뒤 Gemini에 붙여넣으세요")
    app_idea = st.text_area("아이디어 설명", value=st.session_state.selected_idea, height=90)
    target_user = st.text_input("타겟 사용자", value=st.session_state.selected_target)
    required_features = st.text_area("필수 기능", value=st.session_state.selected_features, height=90)
    design_style = st.text_area(
        "원하는 디자인/분위기",
        value=st.session_state.selected_design,
        height=70,
        placeholder="예: 파란색·미니멀, 게임 느낌, 둥근 버튼, 카드형 레이아웃, 모바일 친화적",
        help="색감, 분위기, 레이아웃 스타일을 적으면 HTML·app.py 프롬프트에 함께 반영됩니다.",
    )

    if st.button("프롬프트 3종 만들기", type="primary", use_container_width=True):
        if not app_idea.strip() or not required_features.strip():
            st.error("아이디어 설명과 필수 기능을 입력해 주세요.")
        else:
            st.session_state.selected_design = design_style
            st.session_state.prompt_pack = build_prompt_pack(
                app_idea.strip(),
                target_user.strip() or "학생",
                required_features.strip(),
                design_style.strip(),
            )

    if st.session_state.prompt_pack:
        pack = st.session_state.prompt_pack

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### A. HTML 코드 생성 프롬프트 (3단계에서 사용)")
        st.code(pack["html_prompt"], language="text")
        st.download_button("HTML 프롬프트 다운로드", data=pack["html_prompt"], file_name="prompt_html.txt", mime="text/plain")
        st.link_button("Gemini에서 HTML 만들기", GEMINI_URL, key="gemini_html")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### B. Streamlit 배포용 app.py 생성 프롬프트 (5단계에서 사용)")
        st.code(pack["streamlit_prompt"], language="text")
        st.download_button("app.py 프롬프트 다운로드", data=pack["streamlit_prompt"], file_name="prompt_app_py.txt", mime="text/plain")
        st.link_button("Gemini에서 app.py 만들기", GEMINI_URL, key="gemini_app")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### C. HTML → app.py 변환 프롬프트 (이미 만든 HTML이 있을 때)")
        st.code(pack["convert_prompt"], language="text")
        st.download_button("변환 프롬프트 다운로드", data=pack["convert_prompt"], file_name="prompt_convert.txt", mime="text/plain")
        st.link_button("Gemini에서 변환하기", GEMINI_URL, key="gemini_convert")
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 3단계: HTML 만들기")
    st.markdown("1. **2번 탭**에서 **A 프롬프트**를 복사해 Gemini에 붙여넣는다.")
    st.link_button("✨ Gemini 열기", GEMINI_URL, key="tab3_gemini_html")
    st.markdown("2. 생성된 `index.html` 코드를 복사해 파일로 저장한다.")
    st.markdown("3. 브라우저에서 열어 버튼·입력·결과 화면이 잘 되는지 확인한다.")
    st.markdown("4. 수정이 필요하면 에러 문구나 원하는 변경 사항을 Gemini에 그대로 전달한다.")
    st.markdown("")
    st.markdown("### 5단계: app.py 만들기")
    st.markdown("1. **2번 탭**에서 **B 프롬프트**를 복사해 Gemini에 붙여넣는다.")
    st.link_button("✨ Gemini 열기", GEMINI_URL, key="tab3_gemini_app")
    st.markdown("2. `app.py`는 `htmls/index.html`을 읽어 보여주는 **배포용 껍데기** 역할이다.")
    st.markdown("3. `requirements.txt`도 함께 생성되므로 같이 저장한다.")
    st.markdown("")
    st.markdown('<div class="tip">팁: HTML을 먼저 완성한 뒤 app.py를 만드는 순서가 가장 쉽습니다. 출력 형식(```html, ```python)을 프롬프트에 명시하면 코드 품질이 올라갑니다.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 4·6단계: GitHub 업로드")
    st.link_button("🐙 GitHub 열기", GITHUB_URL, use_container_width=False)
    st.markdown("**최종 폴더 구조**를 먼저 맞춘 뒤 업로드하세요.")
    st.code(
        """내-웹앱/
├── app.py
├── requirements.txt
└── htmls/
    └── index.html""",
        language="text",
    )
    st.markdown("#### 방법 1) GitHub 웹사이트에서 직접 업로드")
    st.markdown("1. GitHub → New repository → 저장소 이름 입력 → Create")
    st.markdown("2. **Add file → Upload files** 로 `htmls/index.html` 업로드 (4단계)")
    st.markdown("3. `app.py`, `requirements.txt` 추가 업로드 (6단계)")
    st.markdown("")
    st.markdown("#### 방법 2) Git 명령어로 업로드")
    st.code(
        """git init
mkdir -p htmls
# htmls/index.html, app.py, requirements.txt 준비 후
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
    st.markdown("### 7단계: Streamlit Community Cloud 배포")
    st.link_button("🚀 Streamlit 배포 사이트 열기", STREAMLIT_URL, use_container_width=False)
    st.markdown("1. GitHub 계정으로 로그인")
    st.markdown("2. **New app** 클릭")
    st.markdown("3. **Repository** 에 내 저장소 선택")
    st.markdown("4. **Main file path** 에 `app.py` 입력")
    st.markdown("5. **Deploy** 클릭 → 몇 분 후 `https://xxxx.streamlit.app` 링크 생성")
    st.markdown("")
    st.markdown('<div class="tip">배포가 실패하면 GitHub에 app.py 경로와 htmls/index.html 위치가 맞는지, requirements.txt에 streamlit이 있는지 확인하세요.</div>', unsafe_allow_html=True)
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
