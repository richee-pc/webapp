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
    page_title="LINKFORGE — AI 웹앱 메이커",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GLOBAL_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=JetBrains+Mono:wght@500;600;700&family=Orbitron:wght@700;800;900&display=swap');
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

:root {
    --bg-deep: #06080f;
    --bg-card: rgba(14, 20, 36, 0.88);
    --bg-card-hover: rgba(18, 28, 50, 0.95);
    --border: rgba(56, 189, 248, 0.18);
    --border-glow: rgba(34, 211, 238, 0.45);
    --accent: #22d3ee;
    --accent-2: #818cf8;
    --accent-3: #34d399;
    --text: #e8edf5;
    --text-muted: #8b9cb3;
    --font-display: 'Orbitron', sans-serif;
    --font-ui: 'Chakra Petch', sans-serif;
    --font-body: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

.stApp {
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(34, 211, 238, 0.14), transparent),
        radial-gradient(ellipse 50% 40% at 100% 0%, rgba(129, 140, 248, 0.1), transparent),
        linear-gradient(180deg, #06080f 0%, #0b1020 45%, #080c16 100%);
    color: var(--text);
    font-family: var(--font-body);
}

.block-container { padding-top: 1.5rem; max-width: 1180px; }

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

/* Hero */
.hero {
    position: relative;
    padding: 2.1rem 2rem 1.75rem;
    margin-bottom: 1.2rem;
    border-radius: 20px;
    border: 1px solid var(--border);
    background:
        linear-gradient(135deg, rgba(34, 211, 238, 0.08), rgba(129, 140, 248, 0.06)),
        var(--bg-card);
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--accent), var(--accent-2), transparent);
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -40px; right: -20px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(34, 211, 238, 0.07), transparent 70%);
    pointer-events: none;
}
.hero-logo {
    font-family: var(--font-display);
    font-size: clamp(1.55rem, 3.5vw, 2.1rem);
    font-weight: 900;
    letter-spacing: 0.22em;
    margin: 0 0 0.55rem 0;
    line-height: 1;
    background: linear-gradient(100deg, #67e8f9 0%, #22d3ee 40%, #a5b4fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 40px rgba(34, 211, 238, 0.15);
}
.hero-badge {
    display: inline-block;
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    color: var(--accent-2);
    background: rgba(129, 140, 248, 0.08);
    border: 1px solid rgba(129, 140, 248, 0.28);
    padding: 0.28rem 0.8rem;
    border-radius: 6px;
    margin-bottom: 0.85rem;
}
.hero-title {
    font-family: var(--font-body);
    font-size: clamp(1.45rem, 3.8vw, 2rem);
    font-weight: 800;
    margin: 0 0 0.5rem 0;
    line-height: 1.35;
    color: #f1f5f9;
    letter-spacing: -0.02em;
}
.hero-accent {
    font-family: var(--font-display);
    font-weight: 800;
    letter-spacing: 0.04em;
    background: linear-gradient(90deg, #22d3ee, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-family: var(--font-body);
    color: var(--text-muted);
    font-size: 0.95rem;
    font-weight: 400;
    margin: 0;
    line-height: 1.6;
    letter-spacing: -0.01em;
}
.hero-sub em {
    font-style: normal;
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: #6ee7b7;
    font-weight: 600;
}

/* Stats */
.stat-row {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
}
.stat-pill {
    flex: 1;
    min-width: 140px;
    padding: 0.85rem 1.1rem;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: var(--bg-card);
}
.stat-label {
    display: block;
    font-family: var(--font-ui);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    color: var(--accent);
    margin-bottom: 0.2rem;
}
.stat-value {
    font-family: var(--font-body);
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
}

/* Cards */
.card, .idea-card, .gallery-card {
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.15rem 1.25rem;
    margin-bottom: 0.85rem;
    background: var(--bg-card);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.card:hover, .idea-card:hover, .gallery-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 0 24px rgba(34, 211, 238, 0.08);
}
.card h3, .idea-card h3, .gallery-card h3 {
    font-family: var(--font-body);
    font-weight: 700;
    color: var(--text);
    margin-top: 0;
}
.card p, .card li, .idea-card p, .idea-card li {
    color: #b6c4d8;
}

.idea-card { position: relative; padding-top: 1.4rem; }
.idea-rank {
    position: absolute;
    top: 0.9rem; right: 1rem;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--accent-2);
    opacity: 0.85;
}
.idea-title {
    font-family: var(--font-body);
    font-size: 1.12rem;
    font-weight: 700;
    color: var(--text);
    margin: 0 0 0.6rem 0;
    letter-spacing: -0.02em;
}
.idea-tag {
    display: inline-block;
    font-family: var(--font-ui);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--accent-3);
    background: rgba(52, 211, 153, 0.1);
    border: 1px solid rgba(52, 211, 153, 0.25);
    padding: 0.15rem 0.55rem;
    border-radius: 6px;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
}

.tip {
    border-left: 3px solid var(--accent);
    padding: 0.75rem 1rem;
    background: rgba(34, 211, 238, 0.06);
    border-radius: 0 12px 12px 0;
    margin-bottom: 0.85rem;
    color: #b8c9de;
    font-size: 0.92rem;
    line-height: 1.55;
}

.section-head {
    font-family: var(--font-body);
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--text);
    margin: 0.2rem 0 0.85rem 0;
    letter-spacing: -0.02em;
}
.section-head span {
    font-family: var(--font-mono);
    font-weight: 600;
    color: var(--accent);
    margin-right: 0.45rem;
    font-size: 1rem;
}

.quick-label {
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    color: var(--text-muted);
    margin-bottom: 0.45rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(8, 12, 22, 0.6);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 6px;
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-ui);
    font-weight: 600;
    font-size: 0.84rem;
    letter-spacing: 0.04em;
    color: var(--text-muted);
    border-radius: 10px;
    padding: 0.45rem 0.7rem;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.18), rgba(129, 140, 248, 0.15)) !important;
    color: var(--text) !important;
    border: 1px solid rgba(34, 211, 238, 0.25);
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.1rem;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0891b2, #6366f1) !important;
    border: none !important;
    font-family: var(--font-ui) !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(34, 211, 238, 0.25) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 28px rgba(34, 211, 238, 0.35) !important;
}
.stButton > button[kind="secondary"] {
    border-radius: 12px !important;
    border-color: var(--border) !important;
}

a[data-testid="stLinkButton"] {
    background: rgba(14, 20, 36, 0.9) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
    font-family: var(--font-ui) !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    transition: all 0.15s ease !important;
}
a[data-testid="stLinkButton"]:hover {
    border-color: var(--border-glow) !important;
    box-shadow: 0 0 16px rgba(34, 211, 238, 0.15) !important;
    color: var(--accent) !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
    background: rgba(10, 14, 26, 0.9) !important;
    border-color: var(--border) !important;
    border-radius: 12px !important;
    color: var(--text) !important;
}
.stTextInput label, .stTextArea label, .stSlider label {
    color: var(--text-muted) !important;
    font-family: var(--font-body) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* Code blocks */
.stCode, pre {
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
}

/* Metrics override hide if used */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.75rem 1rem;
}

/* Markdown in flow */
.card h2, .card h3, .card h4 { color: var(--text); }
.card strong { color: #c8d6ea; }
.card table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.card th, .card td {
    border: 1px solid var(--border);
    padding: 0.55rem 0.75rem;
    color: #b6c4d8;
    font-size: 0.88rem;
}
.card th { background: rgba(34, 211, 238, 0.08); color: var(--accent); font-weight: 700; }

.gallery-meta { color: var(--text-muted); font-size: 0.88rem; margin: 0.2rem 0; }
.gallery-author { color: var(--accent-2); font-weight: 600; }

.stCaption { color: var(--text-muted) !important; }
</style>
"""

st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)

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


def normalize_topic(topic: str) -> str:
    cleaned = topic.strip()
    return cleaned if cleaned else "학교 생활"


def build_topic_idea_templates(topic: str) -> List[Dict[str, Any]]:
    t = normalize_topic(topic)
    return [
        {
            "app_name": f"{t} 루틴 트래커",
            "target_user": f"{t}을(를) 꾸준히 하고 싶은 학생",
            "problem": f"{t} 관련 계획은 세우지만 실행과 기록이 잘 안 된다",
            "core_features": [f"{t} 일지 작성", "목표 달성률 차트", "주간 리포트"],
            "fun_ui": ["레벨업 배지", "달성 스트릭", "진행도 바"],
            "mini_mission": f"7일 {t} 챌린지",
        },
        {
            "app_name": f"{t} 꿀팁 & 정보 허브",
            "target_user": f"{t}에 관심 있는 학생",
            "problem": f"{t}에 대한 유용한 정보를 한곳에서 찾기 어렵다",
            "core_features": [f"{t} 핵심 정보 카드", "키워드 검색", "즐겨찾기 저장"],
            "fun_ui": ["카드형 레이아웃", "태그 필터", "랭킹 뱃지"],
            "mini_mission": f"친구에게 {t} 꿀팁 공유",
        },
        {
            "app_name": f"{t} 퀴즈 챌린지",
            "target_user": f"{t}을(를) 재미있게 익히고 싶은 학생",
            "problem": f"{t} 관련 지식을 암기만 하고 재미있게 학습하기 어렵다",
            "core_features": [f"{t} 퀴즈 출제", "점수·랭킹 기록", "오답 노트"],
            "fun_ui": ["타이머 바", "콤보 점수", "결과 애니메이션"],
            "mini_mission": f"{t} 만점 도전",
        },
        {
            "app_name": f"{t} 고민 상담소",
            "target_user": f"{t} 때문에 고민이 있는 학생",
            "problem": f"{t}과(와) 관련된 고민을 정리하고 해결책을 찾기 어렵다",
            "core_features": ["고민 유형 선택", f"{t} 맞춤 해결 팁", "실천 체크리스트"],
            "fun_ui": ["감정 버튼", "응원 카드", "완료 체크"],
            "mini_mission": f"{t} 고민 1개 해결하기",
        },
        {
            "app_name": f"{t} 팀 · 크루 매칭",
            "target_user": f"{t}을(를) 함께할 친구를 찾는 학생",
            "problem": f"{t}에 같이할 사람을 찾고 일정을 맞추기 어렵다",
            "core_features": ["관심 태그 등록", "팀원 모집 게시", "일정 투표"],
            "fun_ui": ["프로필 카드", "매칭 점수", "채팅 링크 버튼"],
            "mini_mission": f"{t} 팀 1개 만들기",
        },
        {
            "app_name": f"{t} 목표 달성 보드",
            "target_user": f"{t}에서 성과를 내고 싶은 학생",
            "problem": f"{t} 목표는 있지만 진행 상황을 한눈에 보기 어렵다",
            "core_features": ["목표 설정", "단계별 체크", "성취 통계"],
            "fun_ui": ["대시보드", "메달 컬렉션", "그래프 차트"],
            "mini_mission": f"{t} 목표 3단계 클리어",
        },
        {
            "app_name": f"{t} 아이디어 메이커",
            "target_user": f"{t} 분야에서 새 시도를 하고 싶은 학생",
            "problem": f"{t}와(과) 관련된 새로운 아이디어를 구체화하기 어렵다",
            "core_features": ["아이디어 입력", "기능 추천", "실행 플랜 생성"],
            "fun_ui": ["랜덤 카드", "스와이프 선택", "결과 요약"],
            "mini_mission": f"{t} 아이디어 1개 구체화",
        },
        {
            "app_name": f"{t} 기록 아카이브",
            "target_user": f"{t} 활동을 모아두고 싶은 학생",
            "problem": f"{t} 관련 순간과 기록이 흩어져서 정리가 안 된다",
            "core_features": ["사진·메모 업로드", "날짜별 타임라인", "태그 분류"],
            "fun_ui": ["갤러리 뷰", "필터 탭", "하이라이트 배지"],
            "mini_mission": f"{t} 기록 5개 모으기",
        },
    ]


def fallback_ideas(topic: str, count: int) -> List[Dict[str, Any]]:
    templates = build_topic_idea_templates(topic)
    out: List[Dict[str, Any]] = []
    for i in range(count):
        out.append(templates[i % len(templates)].copy())
    return out


def idea_mentions_topic(idea: Dict[str, Any], topic: str) -> bool:
    t = normalize_topic(topic)
    if t == "학교 생활":
        return True
    blob = " ".join(
        [
            str(idea.get("app_name", "")),
            str(idea.get("target_user", "")),
            str(idea.get("problem", "")),
            " ".join(idea.get("core_features", [])),
            " ".join(idea.get("fun_ui", [])),
            str(idea.get("mini_mission", "")),
        ]
    )
    return t in blob


def generate_ideas(topic: str, count: int) -> List[Dict[str, Any]]:
    t = normalize_topic(topic)
    prompt = f"""
너는 고등학생 웹앱 프로젝트 아이디어 코치다.

# 입력
- 주제 키워드: {t}
- 생성 개수: {count}

# 필수 규칙 (반드시 지킬 것)
1) 모든 아이디어는 주제 키워드 "{t}"와 직접적으로 연관되어야 한다.
2) app_name, problem, core_features 안에 주제 "{t}"가 자연스럽게 드러나야 한다.
3) 주제와 무관한 일반 앱(시험, 진로, 힐링 등)은 절대 제안하지 마라.
4) 고등학생이 Streamlit/HTML로 만들 수 있는 수준의 단순한 웹앱 아이디어로 제한한다.
5) 서로 다른 관점의 아이디어를 제안한다. (기록, 정보, 퀴즈, 팀, 목표 등)

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
        raw = call_gemini(prompt, temperature=0.55)
        parsed = parse_json_array(raw)
        if not parsed:
            return fallback_ideas(t, count)

        cleaned: List[Dict[str, Any]] = []
        for item in parsed[:count]:
            core = item.get("core_features", [])
            ui = item.get("fun_ui", [])
            if not isinstance(core, list):
                core = [str(core)]
            if not isinstance(ui, list):
                ui = [str(ui)]

            idea = {
                "app_name": str(item.get("app_name", f"{t} 웹앱")),
                "target_user": str(item.get("target_user", "학생")),
                "problem": str(item.get("problem", f"{t} 관련 문제")),
                "core_features": [str(x) for x in core[:3]] if core else [f"{t} 기능1", f"{t} 기능2", f"{t} 기능3"],
                "fun_ui": [str(x) for x in ui[:3]] if ui else ["카드 UI", "버튼", "결과 화면"],
                "mini_mission": str(item.get("mini_mission", f"{t} 미션")),
            }
            if idea_mentions_topic(idea, t):
                cleaned.append(idea)

        if len(cleaned) < count:
            extras = fallback_ideas(t, count - len(cleaned))
            cleaned.extend(extras)

        return cleaned[:count]
    except Exception:
        return fallback_ideas(t, count)


def fill_prompt_from_idea(idea: Dict[str, Any]) -> None:
    st.session_state.selected_idea = idea["app_name"] + "\n문제: " + idea["problem"]
    st.session_state.selected_target = idea["target_user"]
    st.session_state.selected_features = ", ".join(idea["core_features"] + idea["fun_ui"])
    st.session_state.selected_design = ", ".join(idea["fun_ui"])
    st.toast("아이디어 적용 완료! 프롬프트 탭으로 가보세요", icon="⚡")


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
4. 링크를 친구들에게 보내고, **갤러리 탭**에도 제출한다.

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


def render_idea_card_html(idea: Dict[str, Any], index: int) -> str:
    features = "".join(f'<span class="idea-tag">{f}</span>' for f in idea["core_features"])
    ui_tags = "".join(f'<span class="idea-tag">{u}</span>' for u in idea["fun_ui"])
    return f"""
<div class="idea-card">
    <span class="idea-rank">#{index:02d}</span>
    <h3 class="idea-title">{idea['app_name']}</h3>
    <p style="margin:0 0 0.5rem 0;color:#8b9cb3;font-size:0.88rem;">🎯 {idea['target_user']}</p>
    <p style="margin:0 0 0.75rem 0;color:#b6c4d8;font-size:0.92rem;">💡 {idea['problem']}</p>
    <p style="margin:0 0 0.35rem 0;font-family:'Chakra Petch',sans-serif;font-size:0.75rem;font-weight:600;color:#22d3ee;letter-spacing:0.1em;">CORE FEATURES</p>
    <div style="margin-bottom:0.75rem;">{features}</div>
    <p style="margin:0 0 0.35rem 0;font-family:'Chakra Petch',sans-serif;font-size:0.75rem;font-weight:600;color:#818cf8;letter-spacing:0.1em;">UI VIBE</p>
    <div>{ui_tags}</div>
</div>
""".strip()


init_state()

st.markdown(
    """
<div class="hero">
    <p class="hero-logo">LINKFORGE</p>
    <div class="hero-badge">IDEA → BUILD → SHIP</div>
    <h1 class="hero-title">생각난 순간, <span class="hero-accent">LINK</span>로 배포</h1>
    <p class="hero-sub">프롬프트 한 방이면 웹앱 완성. GitHub에 올리고 친구한테 <em>링크 던지기</em>까지 — 7스텝 클리어.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown('<p class="quick-label">FAST TRACK</p>', unsafe_allow_html=True)
link1, link2, link3 = st.columns(3)
with link1:
    st.link_button("⚡ Gemini", GEMINI_URL, use_container_width=True, help="프롬프트 붙여넣고 코드 생성")
with link2:
    st.link_button("⌨ GitHub", GITHUB_URL, use_container_width=True, help="저장소 만들고 파일 업로드")
with link3:
    st.link_button("🚀 Streamlit", STREAMLIT_URL, use_container_width=True, help="배포하고 공유 링크 받기")

st.markdown(
    """
<div class="stat-row">
    <div class="stat-pill"><span class="stat-label">PIPELINE</span><span class="stat-value">7스텝 클리어</span></div>
    <div class="stat-pill"><span class="stat-label">AUTO PROMPT</span><span class="stat-value">3종 즉시 생성</span></div>
    <div class="stat-pill"><span class="stat-label">SHOWCASE</span><span class="stat-value">작품 링크 공유</span></div>
</div>
""",
    unsafe_allow_html=True,
)


tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "📋 로드맵",
        "💡 아이디어",
        "📝 프롬프트",
        "⚙️ 코드 생성",
        "⌨ GitHub",
        "🚀 배포",
        "🎮 갤러리",
    ]
)

with tab0:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(process_flow_markdown())
    st.markdown("---")
    st.markdown('<p class="quick-label">FAST TRACK</p>', unsafe_allow_html=True)
    t0c1, t0c2, t0c3 = st.columns(3)
    with t0c1:
        st.link_button("Gemini (3·5단계)", GEMINI_URL, use_container_width=True)
    with t0c2:
        st.link_button("GitHub (4·6단계)", GITHUB_URL, use_container_width=True)
    with t0c3:
        st.link_button("Streamlit (7단계)", STREAMLIT_URL, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab1:
    st.markdown('<p class="section-head"><span>//</span>아이디어 추천</p>', unsafe_allow_html=True)
    st.session_state.topic_input = st.text_input(
        "주제 키워드",
        value=st.session_state.topic_input,
        placeholder="예: 축구, 밴드, 게임, 진로, 시험 공부",
        help="입력한 키워드와 직접 연관된 웹앱 아이디어를 추천해요.",
    )

    count = st.slider("추천 개수", 3, 10, 5)
    if st.button("🔥 아이디어 뽑기", type="primary", use_container_width=True):
        st.session_state.ideas = generate_ideas(st.session_state.topic_input, count)

    if st.session_state.ideas:
        st.markdown('<div class="tip">마음에 드는 카드에서 <b>이 아이디어 선택</b> → 프롬프트 탭에 자동 입력</div>', unsafe_allow_html=True)
        for i, idea in enumerate(st.session_state.ideas, start=1):
            st.markdown(render_idea_card_html(idea, i), unsafe_allow_html=True)
            if st.button("✅ 이 아이디어 선택", key=f"pick_{i}", use_container_width=True):
                fill_prompt_from_idea(idea)

with tab2:
    st.markdown('<p class="section-head"><span>//</span>프롬프트 생성</p>', unsafe_allow_html=True)
    st.link_button("⚡ Gemini 열기", GEMINI_URL, help="프롬프트 복사 후 붙여넣기")
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

    if st.button("🛠 프롬프트 3종 생성", type="primary", use_container_width=True):
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
    st.markdown('<p class="section-head"><span>//</span>친구들 작품 갤러리</p>', unsafe_allow_html=True)
    st.markdown('<div class="tip">배포 완료한 Streamlit 링크를 올리면 전체가 볼 수 있어요. 먼저 올린 사람이 주인공 🏆</div>', unsafe_allow_html=True)

    with st.form("share_form", clear_on_submit=True):
        name = st.text_input("이름")
        title = st.text_input("웹앱 제목")
        description = st.text_input("한 줄 설명")
        url = st.text_input("스트림릿 링크", placeholder="https://...streamlit.app")
        submit = st.form_submit_button("📤 갤러리에 등록", use_container_width=True)

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
        st.info("아직 등록된 작품이 없어요. 첫 번째 주인공이 되어 보세요!")
    else:
        for idx, row in enumerate(rows, start=1):
            st.markdown(
                f"""
<div class="gallery-card">
    <span class="idea-rank">#{idx:02d}</span>
    <h3 style="font-family:'Pretendard',sans-serif;font-weight:700;margin:0 0 0.5rem 0;">{row['title']}</h3>
    <p class="gallery-meta">by <span class="gallery-author">{row['name']}</span></p>
    <p class="gallery-meta">{row['description']}</p>
    <p style="font-size:0.75rem;color:#6b7f96;margin:0.4rem 0 0 0;">{row['submitted_at']}</p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.link_button("▶ 플레이", row["url"], key=f"play_{idx}", use_container_width=True)

st.caption(f"업데이트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
