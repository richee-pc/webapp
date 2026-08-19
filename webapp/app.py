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
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GLOBAL_STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

:root {
    --bg-deep: #fff8f1;
    --bg-card: #ffffff;
    --bg-card-hover: #fffdf9;
    --border: rgba(251, 146, 60, 0.22);
    --border-glow: rgba(249, 115, 22, 0.42);
    --accent: #f97316;
    --accent-2: #0ea5e9;
    --accent-3: #10b981;
    --text: #1f2937;
    --text-muted: #6b7280;
    --shadow: 0 12px 32px rgba(249, 115, 22, 0.08);
    --font-display: 'Outfit', sans-serif;
    --font-ui: 'Plus Jakarta Sans', sans-serif;
    --font-body: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-mono: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(ellipse 70% 48% at 8% -8%, rgba(253, 186, 116, 0.42), transparent 58%),
        radial-gradient(ellipse 58% 42% at 96% 0%, rgba(125, 211, 252, 0.38), transparent 52%),
        radial-gradient(ellipse 48% 36% at 50% 108%, rgba(167, 243, 208, 0.28), transparent 55%),
        linear-gradient(180deg, #fff8f1 0%, #f4f9ff 48%, #fff5ee 100%);
    color: var(--text);
    font-family: var(--font-body);
}

.block-container { padding-top: 1.5rem; max-width: 1180px; }

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }

/* Hero */
.hero {
    position: relative;
    padding: 2.15rem 2rem 1.8rem;
    margin-bottom: 1.2rem;
    border-radius: 24px;
    border: 1px solid var(--border);
    background:
        linear-gradient(135deg, rgba(254, 215, 170, 0.38), rgba(186, 230, 253, 0.28)),
        var(--bg-card);
    box-shadow: var(--shadow);
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #fb923c, #f472b6, #38bdf8);
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -50px; right: -10px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(251, 146, 60, 0.22), transparent 70%);
    pointer-events: none;
}
.hero-logo {
    font-family: var(--font-display);
    font-size: clamp(1.55rem, 3.5vw, 2.15rem);
    font-weight: 800;
    letter-spacing: 0.16em;
    margin: 0 0 0.55rem 0;
    line-height: 1;
    background: linear-gradient(100deg, #ea580c 0%, #f97316 38%, #0284c7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-badge {
    display: inline-block;
    font-family: var(--font-ui);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #0369a1;
    background: rgba(14, 165, 233, 0.12);
    border: 1px solid rgba(14, 165, 233, 0.28);
    padding: 0.3rem 0.85rem;
    border-radius: 999px;
    margin-bottom: 0.85rem;
}
.hero-title {
    font-family: var(--font-body);
    font-size: clamp(1.45rem, 3.8vw, 2rem);
    font-weight: 800;
    margin: 0 0 0.5rem 0;
    line-height: 1.35;
    color: var(--text);
    letter-spacing: -0.02em;
}
.hero-accent {
    font-family: var(--font-display);
    font-weight: 800;
    letter-spacing: 0.02em;
    background: linear-gradient(90deg, #ea580c, #db2777);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-family: var(--font-body);
    color: var(--text-muted) !important;
    font-size: 0.97rem;
    font-weight: 500;
    margin: 0;
    line-height: 1.65;
    letter-spacing: -0.01em;
}
.hero-sub em {
    font-style: normal;
    font-family: var(--font-ui);
    font-size: 0.9rem;
    color: #059669;
    font-weight: 700;
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
    padding: 0.9rem 1.15rem;
    border-radius: 18px;
    border: 1px solid var(--border);
    background: var(--bg-card);
    box-shadow: 0 8px 20px rgba(14, 165, 233, 0.06);
}
.stat-label {
    display: block;
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: var(--accent);
    margin-bottom: 0.22rem;
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
    border-radius: 20px;
    padding: 1.2rem 1.3rem;
    margin-bottom: 0.85rem;
    background: var(--bg-card);
    box-shadow: var(--shadow);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}
.card:hover, .idea-card:hover, .gallery-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 16px 36px rgba(249, 115, 22, 0.12);
    transform: translateY(-1px);
}
.card h3, .idea-card h3, .gallery-card h3 {
    font-family: var(--font-body);
    font-weight: 700;
    color: var(--text);
    margin-top: 0;
}
.card p, .card li, .idea-card p, .idea-card li {
    color: #4b5563;
}

.idea-card { position: relative; padding-top: 1.4rem; margin-bottom: 0 !important; }
.idea-list-item { margin-bottom: 0.15rem; }
.idea-list-item + div[data-testid="stVerticalBlock"] .stButton {
    margin-top: -0.35rem !important;
    margin-bottom: 0.55rem !important;
}

/* Streamlit 컨테이너를 투명하게 해서 페이지 배경이 보이게 */
[data-testid="stAppViewContainer"] [data-testid="stMain"] [data-testid="stVerticalBlock"] > div,
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stMarkdownContainer"],
.stElementContainer,
.element-container,
.stMarkdown,
.stButton,
.stButton > div {
    background: transparent !important;
    background-color: transparent !important;
}
[data-testid="stVerticalBlockBorderWrapper"] {
    border: none !important;
    padding: 0 !important;
}
.stTabs [data-baseweb="tab-panel"] [data-testid="stVerticalBlock"] {
    gap: 0.35rem !important;
}

.ai-badge {
    display: inline-block;
    font-family: var(--font-ui);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    color: #047857;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.28);
    padding: 0.24rem 0.7rem;
    border-radius: 999px;
    margin-bottom: 0.65rem;
}
.ai-badge.off {
    color: #6b7280;
    background: rgba(148, 163, 184, 0.12);
    border-color: rgba(148, 163, 184, 0.28);
}
.idea-rank {
    position: absolute;
    top: 0.9rem; right: 1rem;
    font-family: var(--font-ui);
    font-size: 0.78rem;
    font-weight: 800;
    color: var(--accent);
    opacity: 0.85;
}
.idea-title {
    font-family: var(--font-body);
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text);
    margin: 0 0 0.6rem 0;
    letter-spacing: -0.02em;
}
.idea-tag {
    display: inline-block;
    font-family: var(--font-ui);
    font-size: 0.74rem;
    font-weight: 700;
    color: #047857;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.22);
    padding: 0.18rem 0.58rem;
    border-radius: 999px;
    margin-right: 0.35rem;
    margin-bottom: 0.35rem;
}
.idea-tag.vibe {
    color: #0369a1;
    background: rgba(14, 165, 233, 0.12);
    border-color: rgba(14, 165, 233, 0.22);
}
.idea-summary { margin: 0 0 0.75rem 0; color: #374151 !important; font-size: 0.9rem; }
.idea-target { margin: 0 0 0.5rem 0; color: var(--text-muted) !important; font-size: 0.88rem; }
.idea-problem { margin: 0 0 0.75rem 0; color: #4b5563 !important; font-size: 0.92rem; }
.idea-flow { margin: 0 0 0.75rem 0; color: #4b5563 !important; font-size: 0.88rem; line-height: 1.5; }
.idea-rules { margin: 0 0 0.75rem 1.1rem; padding: 0; }
.idea-tags { margin-bottom: 0.75rem; }
.idea-kicker {
    margin: 0 0 0.35rem 0;
    font-family: var(--font-ui);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
}
.idea-kicker.rules { color: #d97706; }
.idea-kicker.flow { color: #db2777; }
.idea-kicker.features { color: #ea580c; }
.idea-kicker.vibe { color: #0284c7; }

.tip {
    border-left: 4px solid var(--accent);
    padding: 0.8rem 1.05rem;
    background: rgba(255, 237, 213, 0.7);
    border-radius: 0 14px 14px 0;
    margin-bottom: 0.85rem;
    color: #4b5563;
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
    display: flex;
    align-items: center;
}
.section-head span {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 999px;
    background: linear-gradient(135deg, #fb923c, #38bdf8);
    margin-right: 0.55rem;
    font-size: 0;
}

.quick-label {
    font-family: var(--font-ui);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 0.45rem;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255, 255, 255, 0.82);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 6px;
    box-shadow: 0 8px 22px rgba(14, 165, 233, 0.06);
}
.stTabs [data-baseweb="tab"] {
    font-family: var(--font-ui);
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.01em;
    color: var(--text-muted);
    border-radius: 12px;
    padding: 0.48rem 0.72rem;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(251, 146, 60, 0.2), rgba(56, 189, 248, 0.18)) !important;
    color: var(--text) !important;
    border: 1px solid rgba(249, 115, 22, 0.28);
}
.stTabs [data-baseweb="tab-panel"] {
    padding-top: 1.1rem;
}

/* Buttons */
.stButton > button {
    background: #ffffff !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    font-family: var(--font-ui) !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
}
.stButton > button:hover {
    border-color: var(--accent) !important;
    color: #c2410c !important;
    background: #fff7ed !important;
    transform: translateY(-1px);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #fb923c, #f43f5e) !important;
    border: none !important;
    color: #ffffff !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 8px 22px rgba(249, 115, 22, 0.28) !important;
}
.stButton > button[kind="primary"]:hover {
    color: #ffffff !important;
    background: linear-gradient(135deg, #f97316, #e11d48) !important;
    box-shadow: 0 12px 28px rgba(249, 115, 22, 0.36) !important;
}
.stButton > button[kind="secondary"] {
    border-radius: 14px !important;
    border-color: var(--border) !important;
}

a[data-testid="stLinkButton"] {
    background: #ffffff !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
    font-family: var(--font-ui) !important;
    font-weight: 700 !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 6px 16px rgba(14, 165, 233, 0.06) !important;
    transition: all 0.15s ease !important;
}
a[data-testid="stLinkButton"]:hover {
    border-color: var(--accent) !important;
    box-shadow: 0 10px 22px rgba(249, 115, 22, 0.14) !important;
    color: #c2410c !important;
    background: #fff7ed !important;
}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
    background: #ffffff !important;
    border-color: #fed7aa !important;
    border-radius: 14px !important;
    color: var(--text) !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.16) !important;
}
.stTextInput label, .stTextArea label, .stSlider label {
    color: var(--text-muted) !important;
    font-family: var(--font-body) !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
}

/* Code blocks */
.stCode, pre {
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
    background: #fffaf5 !important;
}

/* Metrics override hide if used */
div[data-testid="stMetric"] {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 0.75rem 1rem;
}

/* Markdown in flow */
.card h2, .card h3, .card h4 { color: var(--text); }
.card strong { color: #111827; }
.card table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.card th, .card td {
    border: 1px solid #fed7aa;
    padding: 0.55rem 0.75rem;
    color: #4b5563;
    font-size: 0.88rem;
}
.card th { background: rgba(255, 237, 213, 0.8); color: #c2410c; font-weight: 700; }
.card blockquote {
    border-left: 4px solid var(--accent);
    background: #fff7ed;
    color: var(--text);
    padding: 0.7rem 1rem;
    border-radius: 0 12px 12px 0;
}
.card code { background: #fff1e6; color: #c2410c; padding: 0.1rem 0.35rem; border-radius: 6px; }

.gallery-meta { color: var(--text-muted); font-size: 0.88rem; margin: 0.2rem 0; }
.gallery-author { color: #0284c7; font-weight: 700; }
.gallery-time { font-size: 0.75rem; color: #9ca3af; margin: 0.4rem 0 0 0; }

[data-testid="stExpander"] details,
[data-testid="stForm"] {
    background: #ffffff;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 20px rgba(249, 115, 22, 0.05);
}
[data-testid="stExpander"] summary { color: var(--text) !important; }

.stCaption { color: var(--text-muted) !important; }

[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: var(--text) !important;
}
hr { border-color: #fed7aa !important; }

.now-box {
    background: #ffffff;
    border: 1px solid var(--border);
    border-left: 5px solid var(--accent);
    border-radius: 16px;
    padding: 1rem 1.15rem 1.05rem;
    margin-bottom: 1rem;
    box-shadow: var(--shadow);
}
.now-kicker {
    margin: 0 0 0.2rem 0;
    font-family: var(--font-ui);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    color: var(--accent);
}
.now-title {
    margin: 0 0 0.55rem 0;
    font-size: 1.08rem;
    font-weight: 800;
    color: var(--text);
}
.now-line {
    margin: 0 0 0.28rem 0;
    color: #4b5563;
    font-size: 0.92rem;
    line-height: 1.55;
}
.now-next {
    margin: 0.55rem 0 0 0;
    font-weight: 700;
    color: #0369a1;
    font-size: 0.92rem;
}
.guide-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0 0 1rem 0;
}
.guide-item {
    flex: 1;
    min-width: 108px;
    background: #ffffff;
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 0.7rem 0.6rem 0.75rem;
    text-align: center;
    box-shadow: 0 8px 18px rgba(14, 165, 233, 0.05);
}
.guide-item span {
    display: inline-flex;
    width: 24px;
    height: 24px;
    border-radius: 999px;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #fb923c, #f43f5e);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 800;
}
.guide-item b {
    display: block;
    margin-top: 0.35rem;
    font-size: 0.84rem;
    color: var(--text);
}
.guide-item small {
    display: block;
    margin-top: 0.15rem;
    color: var(--text-muted);
    font-size: 0.72rem;
}
.easy-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 0.55rem;
    margin: 0.4rem 0 0.9rem 0;
}
.easy-card {
    background: #fffaf5;
    border: 1px solid #fed7aa;
    border-radius: 14px;
    padding: 0.7rem 0.85rem;
}
.easy-card b { display: block; color: #c2410c; font-size: 0.82rem; margin-bottom: 0.15rem; }
.easy-card span { color: #4b5563; font-size: 0.86rem; line-height: 1.45; }
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
        "idea_input": "",
        "refined_ideas": [],
        "gemini_api_key": "",
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
    typed = str(st.session_state.get("gemini_api_key", "")).strip()
    return typed if typed else None


def has_gemini_api() -> bool:
    return get_active_api_key() is not None


def render_gemini_api_panel() -> None:
    secret_key = get_secret_api_key()
    with st.expander("✨ AI를 더 똑똑하게 쓰기 (선택 · 없어도 수업 가능)", expanded=not secret_key):
        if secret_key:
            st.markdown(
                '<span class="ai-badge">AI MODE · ON (배포 secrets 연동)</span>',
                unsafe_allow_html=True,
            )
            st.caption("선생님이 이미 AI를 연결해 두었어요. 그냥 아래 칸에 아이디어만 적으면 됩니다.")
        else:
            if has_gemini_api():
                st.markdown('<span class="ai-badge">AI MODE · ON</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="ai-badge off">BASIC MODE · API 없음</span>', unsafe_allow_html=True)
                st.caption("이 칸은 비워도 수업을 할 수 있어요. 키를 넣으면 AI가 아이디어를 더 잘 만들어 줍니다.")
            st.session_state.gemini_api_key = st.text_input(
                "Gemini API 키 (선생님 안내가 있을 때만)",
                type="password",
                value=st.session_state.gemini_api_key,
                placeholder="AIza...",
                help="Google AI Studio에서 발급받은 키를 입력하세요.",
            )
            st.caption("선생님이 배포할 때 secrets에 GEMINI_API_KEY를 넣으면 학생들은 입력하지 않아도 됩니다.")


def render_now_box(now: str, why: str, how: str, nxt: str) -> None:
    st.markdown(
        f"""
<div class="now-box">
    <p class="now-kicker">지금 이 탭에서</p>
    <p class="now-title">{now}</p>
    <p class="now-line"><b>왜 하나요?</b> {why}</p>
    <p class="now-line"><b>어떻게 하나요?</b> {how}</p>
    <p class="now-next">다 했으면 → {nxt}</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_class_guide_strip() -> None:
    st.markdown('<p class="quick-label">오늘 수업 순서 · 왼쪽부터 그대로 따라가면 됩니다</p>', unsafe_allow_html=True)
    st.markdown(
        """
<div class="guide-row">
    <div class="guide-item"><span>1</span><b>생각 고르기</b><small>2. 아이디어 탭</small></div>
    <div class="guide-item"><span>2</span><b>부탁문 만들기</b><small>3. 프롬프트 탭</small></div>
    <div class="guide-item"><span>3</span><b>화면 받기</b><small>4. 화면 만들기 탭</small></div>
    <div class="guide-item"><span>4</span><b>가방에 넣기</b><small>5. GitHub 탭</small></div>
    <div class="guide-item"><span>5</span><b>배포 파일</b><small>다시 4번 탭</small></div>
    <div class="guide-item"><span>6</span><b>나머지 올리기</b><small>다시 5번 탭</small></div>
    <div class="guide-item"><span>7</span><b>링크로 공개</b><small>6. 배포 탭</small></div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_idea_list(ideas: List[Dict[str, Any]], key_prefix: str, button_label: str) -> None:
    for i, idea in enumerate(ideas, start=1):
        st.markdown(
            f'<div class="idea-list-item">{render_idea_card_html(idea, i)}</div>',
            unsafe_allow_html=True,
        )
        if st.button(button_label, key=f"{key_prefix}_{i}", use_container_width=True):
            fill_prompt_from_idea(idea)


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


def parse_json_object(raw: str) -> Optional[Dict[str, Any]]:
    text = normalize_json(raw)
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    found = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not found:
        return None

    try:
        obj = json.loads(found.group(0))
        if isinstance(obj, dict):
            return obj
    except Exception:
        return None
    return None


def as_string_list(value: Any, fallback: List[str], limit: int = 5) -> List[str]:
    if isinstance(value, list):
        cleaned = [str(x).strip() for x in value if str(x).strip()]
        if cleaned:
            return cleaned[:limit]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return fallback[:limit]


def normalize_refined_idea(item: Dict[str, Any], idea_text: str) -> Dict[str, Any]:
    seed = idea_text.strip() or "나의 웹앱"
    name = str(item.get("app_name", seed)).strip() or seed

    return {
        "app_name": name,
        "target_user": str(item.get("target_user", f"{name}을(를) 즐기고 싶은 고등학생")),
        "problem": str(item.get("problem", f"'{seed}' 아이디어는 있지만 규칙과 진행 방식이 정리되지 않았다")),
        "concept_summary": str(item.get("concept_summary", f"{name}을(를) 친구들과 함께 즐길 수 있는 웹앱")),
        "game_rules": as_string_list(
            item.get("game_rules"),
            [
                "참가자는 라운드마다 결과를 예측하거나 선택한다",
                "정답/성공 시 점수를 얻고, 실패 시 점수가 줄어든다",
                "정해진 라운드 후 최고 점수가 우승한다",
            ],
        ),
        "game_flow": as_string_list(
            item.get("game_flow"),
            [
                "닉네임 입력",
                "라운드/문제 선택",
                "예측 또는 답 입력",
                "결과 반영 및 점수 계산",
                "랭킹 확인",
            ],
        ),
        "core_features": as_string_list(
            item.get("core_features"),
            ["입력 폼", "점수 자동 계산", "랭킹 보드"],
            limit=3,
        ),
        "fun_ui": as_string_list(
            item.get("fun_ui"),
            ["카드형 UI", "점수 애니메이션", "1위 하이라이트"],
            limit=3,
        ),
        "mini_mission": str(item.get("mini_mission", "친구와 함께 1라운드 플레이")),
    }


def fallback_refine_idea(idea_text: str) -> List[Dict[str, Any]]:
    seed = idea_text.strip() or "나의 웹앱"
    is_game = any(word in seed for word in ["게임", "내기", "배팅", "베팅", "승부", "승률", "퀴즈", "대결", "토너먼트"])

    if is_game:
        rules = [
            f"{seed} 참가자는 경기/라운드마다 결과를 예측한다",
            "예측이 맞으면 점수를 얻고, 틀리면 점수를 잃는다",
            "정해진 라운드 종료 후 최고 점수가 우승한다",
            "동점일 경우 마지막 라운드 점수 또는 제출 시간으로 순위를 정한다",
        ]
        flow = [
            "닉네임 입력 후 방 만들기",
            "경기/라운드 선택",
            "승패·스코어 예측 제출",
            "실제 결과 입력",
            "점수·승률 자동 계산",
            "랭킹 보드 확인",
        ]
        features = ["예측 입력 폼", "점수·승률 자동 계산", "실시간 랭킹 보드"]
        ui = ["경기 카드 UI", "점수 변화 애니메이션", "우승자 하이라이트"]
    else:
        rules = [
            f"{seed} 사용 시 반드시 지켜야 할 핵심 조건 3가지를 화면에 안내한다",
            "사용자 입력이 비어 있으면 진행할 수 없다",
            "결과는 즉시 화면에 반영되고 이전 기록을 확인할 수 있다",
        ]
        flow = [
            "시작 화면에서 목적 확인",
            "필요 정보 입력",
            "실행 버튼 클릭",
            "결과/피드백 확인",
            "기록 저장 또는 공유",
        ]
        features = ["핵심 입력 폼", "결과 생성/표시", "기록 저장"]
        ui = ["카드형 레이아웃", "상태 배지", "결과 하이라이트"]

    idea = normalize_refined_idea(
        {
            "app_name": seed,
            "target_user": f"{seed}을(를) 사용하고 싶은 고등학생",
            "problem": f"'{seed}'는 떠올랐지만 규칙·기능·진행 순서가 아직 정리되지 않았다",
            "concept_summary": f"{seed}을(를) 누구나 쉽게 이해하고 바로 사용할 수 있게 만드는 웹앱",
            "game_rules": rules,
            "game_flow": flow,
            "core_features": features,
            "fun_ui": ui,
            "mini_mission": "친구 2명에게 링크 공유",
        },
        seed,
    )
    return [idea]


def refine_idea(idea_text: str) -> List[Dict[str, Any]]:
    seed = idea_text.strip()
    if not seed:
        return []

    prompt = f"""
너는 고등학생 웹앱 기획 멘토다.

# 학생이 적은 아이디어 (한 줄)
{seed}

# 목표
위 아이디어를 고등학생이 HTML/Streamlit으로 만들 수 있도록 **구체화**하라.
게임/서비스라면 규칙, 진행 방식, 점수/판정 로직까지 명확히 작성한다.

# 필수 규칙
1) 입력 아이디어 "{seed}"의 핵심 의도를 반드시 유지한다.
2) app_name은 입력 아이디어를 기반으로 짧고 명확하게 짓는다.
3) game_rules는 실제로 적용 가능한 규칙 3~5개.
4) game_flow는 사용자가 화면에서 거치는 단계 4~6개.
5) core_features는 웹앱에 꼭 필요한 기능 3개.
6) 고등학생 수준에서 구현 가능한 단순한 범위로 제한한다.

반드시 JSON 객체 하나만 출력하고 다른 텍스트는 금지.
키:
- app_name
- target_user
- problem
- concept_summary
- game_rules (문자열 배열)
- game_flow (문자열 배열)
- core_features (문자열 배열 3개)
- fun_ui (문자열 배열 3개)
- mini_mission
""".strip()

    try:
        raw = call_gemini(prompt, temperature=0.5)
        parsed = parse_json_object(raw)
        if not parsed:
            return fallback_refine_idea(seed)
        return [normalize_refined_idea(parsed, seed)]
    except Exception:
        return fallback_refine_idea(seed)


def call_gemini(prompt: str, temperature: float = 0.8) -> str:
    if genai is None:
        raise ValueError("google-generativeai 라이브러리가 없습니다.")

    api_key = get_active_api_key()
    if not api_key:
        raise ValueError("Gemini API 키가 없습니다.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
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
    lines = [idea["app_name"]]
    if idea.get("concept_summary"):
        lines.append(f"컨셉: {idea['concept_summary']}")
    lines.append(f"문제: {idea['problem']}")
    if idea.get("game_rules"):
        lines.append("규칙: " + " / ".join(idea["game_rules"]))
    if idea.get("game_flow"):
        lines.append("진행 방식: " + " → ".join(idea["game_flow"]))

    st.session_state.selected_idea = "\n".join(lines)
    st.session_state.selected_target = idea["target_user"]

    feature_parts = list(idea.get("core_features", []))
    if idea.get("game_rules"):
        feature_parts.extend(idea["game_rules"][:2])
    if idea.get("game_flow"):
        feature_parts.extend(idea["game_flow"][:2])
    st.session_state.selected_features = ", ".join(feature_parts + idea.get("fun_ui", []))
    st.session_state.selected_design = ", ".join(idea["fun_ui"])
    st.toast("좋아요! 이제 위쪽 「3. 프롬프트」 탭으로 가서 부탁문을 만들어요", icon="✨")


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
## 오늘 수업: 생각을 링크로 만들기

코딩을 몰라도 됩니다. **AI에게 부탁 → 파일을 저장 → 인터넷 가방에 넣기 → 링크로 공개** 순서만 따라가면 친구가 핸드폰으로 내 웹앱을 열 수 있어요.

> **한 줄 흐름:** 아이디어 → 프롬프트(부탁문) → HTML 화면 → GitHub에 올리기 → app.py 만들기 → 나머지 올리기 → Streamlit으로 링크 받기

### 어려운 말, 쉽게 보기

| 어려운 말 | 쉽게 말하면 |
|------|--------|
| 프롬프트 | AI에게 보내는 **부탁 편지** |
| HTML / `index.html` | 화면에 보이는 **웹페이지 파일** |
| `app.py` | Streamlit이 그 웹페이지를 열어주는 **안내 파일** |
| `requirements.txt` | “이 앱을 켜려면 streamlit이 필요해요”라고 적힌 **재료 목록** |
| GitHub | 파일을 넣어 두는 **인터넷 가방** |
| Repository | GitHub에 만든 **내 폴더** |
| Streamlit | 가방 속 파일을 **링크로 바꿔 주는 곳** |
| 배포 | 친구 핸드폰에서도 열리게 **공개하기** |

---

### 1단계: 만들고 싶은 것을 정하기
**어디서?** 위쪽 **「2. 아이디어」** 탭

- **누구를 위한 앱인가?** (예: 시험 준비하는 친구, 동아리 부원)
- **어떤 문제를 풀까?** (예: 공부 계획이 자꾸 밀림)
- **핵심 기능 3가지**를 적는다.
- **원하는 디자인**도 함께 정한다. (예: 파란색·미니멀, 게임 느낌, 카드형 레이아웃)

✅ **이 단계가 끝나면:** 아이디어 + 기능 + 디자인 메모가 준비됨

---

### 2단계: AI에게 보낼 부탁문(프롬프트) 만들기
**어디서?** 위쪽 **「3. 프롬프트」** 탭

- **2. 아이디어** 탭에서 고르거나, 내가 적은 내용이 자동으로 들어온다.
- **기능**뿐 아니라 **디자인/분위기**도 프롬프트에 포함한다.
- 아래 **부탁문 2개**를 준비한다. (C는 이미 HTML이 있을 때만)
  - **A. HTML 생성 프롬프트** → `index.html`(화면 파일) 만들 때 사용
  - **B. Streamlit 배포 프롬프트** → `app.py`(안내 파일) 만들 때 사용

✅ **이 단계가 끝나면:** A·B 프롬프트를 복사해 둠

---

### 3단계: 화면(HTML 웹앱) 만들기
**어디서?** 위쪽 **「4. 화면 만들기」** 탭 · Gemini 사용

1. Gemini에 **A 프롬프트**를 붙여넣는다.
2. 생성된 `index.html` 코드를 복사한다.
3. 컴퓨터에 `index.html`로 저장한 뒤, 브라우저로 열어 **버튼·입력·결과가 잘 되는지** 확인한다.
4. 마음에 들 때까지 Gemini에게 수정을 요청한다. (에러 문구를 그대로 붙여넣기)

✅ **이 단계가 끝나면:** 브라우저에서 잘 동작하는 `index.html` 확보

---

### 4단계: GitHub 가방 만들고 화면 파일 넣기
**어디서?** 위쪽 **「5. GitHub」** 탭 · **웹사이트에서 올리기만 해도 됩니다** (명령어는 선택)

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
   - 웹에서 올릴 때 파일 이름을 `htmls/index.html`로 적으면 폴더가 자동으로 생겨요.
4. GitHub에 **첫 업로드**를 한다. (웹에서 직접 업로드하거나 Git 명령어 사용)

✅ **이 단계가 끝나면:** GitHub에 `htmls/index.html`이 올라가 있음

---

### 5단계: 배포용 안내 파일(app.py) 만들기
**어디서?** 다시 **「4. 화면 만들기」** 탭 · Gemini 사용

1. Gemini에 **B 프롬프트**를 붙여넣는다.
2. 생성된 `app.py`와 `requirements.txt`를 복사한다.
3. `app.py`는 **`htmls/index.html` 파일을 열어 보여주는 역할**을 한다.
4. 로컬에서 `streamlit run app.py`로 미리 확인한다. (선택 · 안 해도 다음 단계 가능)

✅ **이 단계가 끝나면:** `app.py` + `requirements.txt` 준비 완료

---

### 6단계: GitHub 가방에 나머지 파일 넣기
**어디서?** 다시 **「5. GitHub」** 탭

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

✅ **이 단계가 끝나면:** GitHub에 3개 파일(또는 폴더 포함 전체 구조)이 모두 있음

---

### 7단계: Streamlit으로 링크로 공개하고 공유
**어디서?** 위쪽 **「6. 배포」** 탭, 자랑은 **「7. 갤러리」** 탭

1. [share.streamlit.io](https://share.streamlit.io/)에 GitHub 계정으로 로그인한다.
2. **New app** → 저장소 선택 → **Main file path**에 `app.py` 입력 → **Deploy**
3. 배포가 끝나면 `https://xxxx.streamlit.app` 형태의 **공유 링크**가 생긴다.
4. 링크를 친구들에게 보내고, **갤러리 탭**에도 제출한다.

✅ **이 단계가 끝나면:** 친구가 링크로 내 웹앱에 접속 가능

---

### 한눈에 보는 순서 요약

| 순서 | 할 일 | 결과물 | 탭 |
|------|--------|--------|------|
| 1 | 아이디어·디자인 구상 | 기획 메모 | 2. 아이디어 |
| 2 | 프롬프트 2종 생성 | A(HTML), B(app.py) | 3. 프롬프트 |
| 3 | Gemini로 HTML 생성 | `index.html` | 4. 화면 만들기 |
| 4 | GitHub 저장소 + htmls 업로드 | `htmls/index.html` | 5. GitHub |
| 5 | Gemini로 app.py 생성 | `app.py`, `requirements.txt` | 4. 화면 만들기 |
| 6 | GitHub에 전체 업로드 | 완성된 저장소 | 5. GitHub |
| 7 | Streamlit 배포·공유 | 공유 URL | 6. 배포 |
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
    features = "".join(f'<span class="idea-tag">{f}</span>' for f in idea.get("core_features", []))
    ui_tags = "".join(f'<span class="idea-tag vibe">{u}</span>' for u in idea.get("fun_ui", []))

    extra_blocks = ""
    if idea.get("concept_summary"):
        extra_blocks += f'<p class="idea-summary">📌 {idea["concept_summary"]}</p>'

    if idea.get("game_rules"):
        rules = "".join(f"<li>{rule}</li>" for rule in idea["game_rules"])
        extra_blocks += (
            '<p class="idea-kicker rules">규칙</p>'
            f'<ul class="idea-rules">{rules}</ul>'
        )

    if idea.get("game_flow"):
        flow = " → ".join(idea["game_flow"])
        extra_blocks += (
            '<p class="idea-kicker flow">진행</p>'
            f'<p class="idea-flow">{flow}</p>'
        )

    return f"""
<div class="idea-card">
    <span class="idea-rank">#{index:02d}</span>
    <h3 class="idea-title">{idea['app_name']}</h3>
    <p class="idea-target">🎯 {idea['target_user']}</p>
    <p class="idea-problem">💡 {idea['problem']}</p>
    {extra_blocks}
    <p class="idea-kicker features">핵심 기능</p>
    <div class="idea-tags">{features}</div>
    <p class="idea-kicker vibe">분위기</p>
    <div>{ui_tags}</div>
</div>
""".strip()


init_state()

st.markdown(
    """
<div class="hero">
    <p class="hero-logo">LINKFORGE</p>
    <div class="hero-badge">1학년 수업 · 코딩 몰라도 따라갈 수 있어요</div>
    <h1 class="hero-title">오늘 할 일: 생각을 <span class="hero-accent">LINK</span>로 만들기</h1>
    <p class="hero-sub">AI에게 부탁하면 웹앱이 나와요. 아래 탭을 <em>1번부터 7번까지</em> 순서대로 누르면 됩니다.</p>
</div>
""",
    unsafe_allow_html=True,
)

render_class_guide_strip()

st.markdown('<p class="quick-label">수업에서 자주 여는 사이트</p>', unsafe_allow_html=True)
link1, link2, link3 = st.columns(3)
with link1:
    st.link_button("✨ Gemini (AI에게 부탁)", GEMINI_URL, use_container_width=True, help="프롬프트를 붙여넣고 코드를 받아요")
with link2:
    st.link_button("⌨ GitHub (파일 가방)", GITHUB_URL, use_container_width=True, help="만든 파일을 인터넷에 보관해요")
with link3:
    st.link_button("🚀 Streamlit (링크로 공개)", STREAMLIT_URL, use_container_width=True, help="가방 속 파일을 공유 링크로 바꿔요")

st.markdown(
    """
<div class="stat-row">
    <div class="stat-pill"><span class="stat-label">오늘 목표</span><span class="stat-value">친구에게 링크 보내기</span></div>
    <div class="stat-pill"><span class="stat-label">코딩</span><span class="stat-value">몰라도 따라가면 됩니다</span></div>
    <div class="stat-pill"><span class="stat-label">순서</span><span class="stat-value">1번 탭부터 차근차근</span></div>
</div>
""",
    unsafe_allow_html=True,
)


tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "1. 오늘 할 일",
        "2. 아이디어",
        "3. 프롬프트",
        "4. 화면 만들기",
        "5. GitHub",
        "6. 배포",
        "7. 갤러리",
    ]
)

with tab0:
    render_now_box(
        "수업 전체를 한눈에 보기",
        "길을 잃지 않으려고요. 오늘 끝은 ‘내 웹앱 링크를 친구에게 보내는 것’입니다.",
        "아래 설명을 읽고, 준비되면 「2. 아이디어」 탭으로 가면 됩니다.",
        "2. 아이디어 탭에서 만들고 싶은 것을 정해요",
    )
    st.markdown(
        """
<div class="easy-grid">
    <div class="easy-card"><b>Gemini</b><span>AI 친구에게 “이렇게 만들어줘”라고 말하는 곳</span></div>
    <div class="easy-card"><b>GitHub</b><span>만든 파일을 넣어 두는 인터넷 가방</span></div>
    <div class="easy-card"><b>Streamlit</b><span>가방 속 파일을 핸드폰 링크로 바꿔 주는 곳</span></div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(process_flow_markdown())
    st.markdown("---")
    st.markdown('<p class="quick-label">지금 바로 열어둘 사이트</p>', unsafe_allow_html=True)
    t0c1, t0c2, t0c3 = st.columns(3)
    with t0c1:
        st.link_button("Gemini 열기 (3·5단계)", GEMINI_URL, use_container_width=True)
    with t0c2:
        st.link_button("GitHub 열기 (4·6단계)", GITHUB_URL, use_container_width=True)
    with t0c3:
        st.link_button("Streamlit 열기 (7단계)", STREAMLIT_URL, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab1:
    render_now_box(
        "만들고 싶은 앱을 정하기",
        "무엇을 만들지 정해야 AI에게 부탁할 수 있어요.",
        "떠오른 생각을 한 줄로 적거나, 키워드로 추천을 받은 뒤 「이 아이디어 선택」을 눌러요.",
        "3. 프롬프트 탭으로 가서 부탁문을 만들어요",
    )
    render_gemini_api_panel()

    st.markdown('<p class="section-head"><span></span>방법 A. 내 생각을 자세히 풀어주기</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tip">만들고 싶은 것을 <b>한 줄</b>만 적어도 돼요. '
        "예: <i>축구 승률 내기 게임</i> → 규칙·진행 방식·기능까지 펼쳐 줍니다.</div>",
        unsafe_allow_html=True,
    )
    st.session_state.idea_input = st.text_area(
        "만들고 싶은 앱을 한 줄로 적어 보세요",
        value=st.session_state.idea_input,
        height=80,
        placeholder="예: 축구 승률 내기 게임, 급식 메뉴 투표, 수행평가 D-day 카운터",
        help="떠오른 아이디어를 그대로 적으면 구체적인 기획안으로 바꿔줘요.",
    )

    if st.button("🔍 이 생각을 자세히 풀어주기", type="primary", use_container_width=True):
        if not st.session_state.idea_input.strip():
            st.error("만들고 싶은 앱을 한 줄로 적어 주세요. 예: 급식 메뉴 투표")
        else:
            with st.spinner("생각을 구체적으로 만드는 중..."):
                st.session_state.refined_ideas = refine_idea(st.session_state.idea_input)

    if st.session_state.refined_ideas:
        st.markdown('<div class="tip">마음에 드는 카드를 고르면 <b>3. 프롬프트</b> 탭에 내용이 자동으로 들어갑니다.</div>', unsafe_allow_html=True)
        render_idea_list(st.session_state.refined_ideas, "refined_pick", "✅ 이걸로 만들기")

    st.divider()
    st.markdown('<p class="section-head"><span></span>방법 B. 키워드로 아이디어 추천받기</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tip">생각이 안 나면 <b>좋아하는 것</b>만 적어도 됩니다. 예: 축구, 급식, 시험, 게임</div>',
        unsafe_allow_html=True,
    )
    st.session_state.topic_input = st.text_input(
        "좋아하는 것 / 주제 키워드",
        value=st.session_state.topic_input,
        placeholder="예: 축구, 밴드, 게임, 진로, 시험 공부",
        help="입력한 키워드와 직접 연관된 웹앱 아이디어를 추천해요.",
    )

    count = st.slider("몇 개를 추천받을까요?", 3, 10, 5)
    if st.button("🔥 아이디어 추천받기", type="primary", use_container_width=True):
        with st.spinner("아이디어를 고르는 중..."):
            st.session_state.ideas = generate_ideas(st.session_state.topic_input, count)

    if st.session_state.ideas:
        st.markdown('<div class="tip">카드를 읽고, 하고 싶은 것을 고른 뒤 <b>이걸로 만들기</b>를 누르세요.</div>', unsafe_allow_html=True)
        render_idea_list(st.session_state.ideas, "pick", "✅ 이걸로 만들기")

with tab2:
    render_now_box(
        "AI에게 보낼 부탁문(프롬프트) 만들기",
        "AI는 우리 생각을 모릅니다. 무엇을 만들지 편지로 알려줘야 화면을 만들어 줘요.",
        "칸이 비어 있으면 2번 탭에서 아이디어를 먼저 고르세요. 채워져 있으면 아래 주황 버튼만 누르면 됩니다.",
        "나온 A 부탁문을 복사하고 「4. 화면 만들기」 탭으로 가요",
    )
    st.markdown('<p class="section-head"><span></span>부탁문 만들기</p>', unsafe_allow_html=True)
    st.markdown(
        '<div class="tip"><b>프롬프트</b> = AI에게 보내는 부탁 편지예요. '
        "A는 화면용, B는 인터넷에 올리는 용, C는 이미 화면이 있을 때만 씁니다.</div>",
        unsafe_allow_html=True,
    )
    st.link_button("✨ Gemini 열기 (복붙할 창)", GEMINI_URL, help="프롬프트 복사 후 붙여넣기")
    app_idea = st.text_area("아이디어 설명 (무엇을 만들까요?)", value=st.session_state.selected_idea, height=90)
    target_user = st.text_input("누가 쓰나요?", value=st.session_state.selected_target)
    required_features = st.text_area("꼭 들어갔으면 하는 기능", value=st.session_state.selected_features, height=90)
    design_style = st.text_area(
        "원하는 디자인/분위기",
        value=st.session_state.selected_design,
        height=70,
        placeholder="예: 파란색·미니멀, 게임 느낌, 둥근 버튼, 카드형 레이아웃, 모바일 친화적",
        help="색감, 분위기, 레이아웃 스타일을 적으면 HTML·app.py 프롬프트에 함께 반영됩니다.",
    )

    if st.button("🛠 AI에게 보낼 부탁문 3개 만들기", type="primary", use_container_width=True):
        if not app_idea.strip() or not required_features.strip():
            st.error("아이디어 설명과 꼭 필요한 기능을 적어 주세요. 2번 탭에서 고르면 자동으로 채워집니다.")
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
        st.markdown("### A. 화면(HTML) 만들어 달라는 부탁문 · 3단계에서 사용")
        st.caption("이걸 복사해서 Gemini에 붙여넣으면 `index.html` 화면 파일이 나와요.")
        st.code(pack["html_prompt"], language="text")
        st.download_button("HTML 프롬프트 다운로드", data=pack["html_prompt"], file_name="prompt_html.txt", mime="text/plain")
        st.link_button("Gemini에서 HTML 만들기", GEMINI_URL, key="gemini_html")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### B. 링크로 올려 달라는 부탁문(app.py) · 5단계에서 사용")
        st.caption("화면이 완성된 다음에 사용해요. Streamlit이 읽어 줄 `app.py`를 만듭니다.")
        st.code(pack["streamlit_prompt"], language="text")
        st.download_button("app.py 프롬프트 다운로드", data=pack["streamlit_prompt"], file_name="prompt_app_py.txt", mime="text/plain")
        st.link_button("Gemini에서 app.py 만들기", GEMINI_URL, key="gemini_app")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### C. 이미 만든 HTML을 app.py로 바꾸는 부탁문 · 화면이 이미 있을 때만")
        st.caption("A로 화면을 이미 만들었다면, 그 파일을 배포용으로 바꿔 달라고 할 때 씁니다.")
        st.code(pack["convert_prompt"], language="text")
        st.download_button("변환 프롬프트 다운로드", data=pack["convert_prompt"], file_name="prompt_convert.txt", mime="text/plain")
        st.link_button("Gemini에서 변환하기", GEMINI_URL, key="gemini_convert")
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    render_now_box(
        "AI가 준 코드를 파일로 저장하기",
        "부탁문만으로는 앱이 안 열려요. 답을 파일로 저장해야 화면에 보입니다.",
        "먼저 A로 화면(`index.html`)을 만들고, 그게 잘 되면 나중에 B로 `app.py`를 만들어요.",
        "화면 파일이 준비되면 「5. GitHub」 탭에서 가방에 넣어요",
    )
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 먼저 하기 · 3단계: 화면(HTML) 만들기")
    st.markdown("**HTML / `index.html`** 은 화면에 보이는 웹페이지 파일입니다. 메모장에 저장해도 됩니다.")
    st.markdown("1. **3. 프롬프트** 탭에서 **A 부탁문**을 복사해 Gemini에 붙여넣는다.")
    st.link_button("✨ Gemini 열기", GEMINI_URL, key="tab3_gemini_html")
    st.markdown("2. 나온 코드에서 `index.html` 부분을 복사해 파일로 저장한다.")
    st.markdown("3. 그 파일을 더블클릭(또는 브라우저로 열기)해서 버튼·입력·결과가 잘 되는지 확인한다.")
    st.markdown("4. 이상하면 에러 문구나 원하는 변경을 Gemini에 그대로 붙여 넣고 다시 받는다.")
    st.markdown("")
    st.markdown("### 화면이 된 다음 · 5단계: app.py 만들기")
    st.markdown("**`app.py`** 는 Streamlit이 `htmls/index.html`을 열어 보여주는 **안내 파일**입니다. 화면 자체를 새로 그리는 파일이 아니에요.")
    st.markdown("1. **3. 프롬프트** 탭에서 **B 부탁문**을 복사해 Gemini에 붙여넣는다.")
    st.link_button("✨ Gemini 열기", GEMINI_URL, key="tab3_gemini_app")
    st.markdown("2. `app.py`는 `htmls/index.html`을 읽어 보여주는 **배포용 껍데기** 역할이다.")
    st.markdown("3. `requirements.txt`도 함께 생성되므로 같이 저장한다. (재료 목록 파일)")
    st.markdown("")
    st.markdown('<div class="tip">팁: HTML을 먼저 완성한 뒤 app.py를 만드는 순서가 가장 쉽습니다. 출력 형식(```html, ```python)을 프롬프트에 명시하면 코드 품질이 올라갑니다.</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    render_now_box(
        "만든 파일을 GitHub 가방에 넣기",
        "내 컴퓨터에만 있으면 친구 핸드폰에서 안 열려요. 인터넷 가방에 넣어야 Streamlit이 가져갈 수 있습니다.",
        "코딩 명령어는 안 써도 됩니다. 웹사이트에서 파일만 올리면 돼요. 먼저 화면 파일, 나중에 app.py를 올립니다.",
        "파일이 다 올라가면 「6. 배포」 탭에서 링크로 바꿔요",
    )
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 4·6단계: GitHub에 파일 올리기")
    st.link_button("🐙 GitHub 열기", GITHUB_URL, use_container_width=False)
    st.markdown("**GitHub** = 파일을 넣어 두는 인터넷 가방입니다. **최종 폴더 모양**을 먼저 맞춘 뒤 업로드하세요.")
    st.code(
        """내-웹앱/
├── app.py
├── requirements.txt
└── htmls/
    └── index.html""",
        language="text",
    )
    st.markdown("#### 방법 1) 웹사이트에서 올리기 · 수업에서 이 방법을 권장해요")
    st.markdown("1. GitHub → **New repository** → 저장소 이름 입력(예: `my-webapp`) → **Create**")
    st.markdown("2. **Add file → Upload files**")
    st.markdown("3. **4단계:** `index.html`을 올리되, 이름을 `htmls/index.html`로 적으면 폴더가 자동으로 생깁니다.")
    st.markdown("4. **6단계:** 같은 방식으로 `app.py`, `requirements.txt`를 **맨 위 폴더**에 추가 업로드합니다.")
    st.markdown("")
    st.markdown("#### 방법 2) Git 명령어로 업로드 · 알고 싶은 사람만")
    st.caption("명령어가 어렵다면 방법 1만 해도 충분합니다.")
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
    render_now_box(
        "가방 속 파일을 친구 링크로 바꾸기",
        "GitHub은 보관함이고, Streamlit이 “이 앱을 인터넷에서 열어줘” 버튼을 눌러 주는 곳입니다.",
        "GitHub 계정으로 로그인한 뒤 New app → 내 저장소 → Main file path에 app.py → Deploy.",
        "링크가 나오면 「7. 갤러리」에 올려 자랑해요",
    )
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 7단계: Streamlit Community Cloud로 배포하기")
    st.markdown("**배포** = 친구 핸드폰에서도 열리게 공개하는 것입니다. 끝나면 `https://xxxx.streamlit.app` 링크가 나와요.")
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
    render_now_box(
        "완성 링크를 교실 갤러리에 올리기",
        "친구 작품을 서로 열어 보면 수업이 더 재미있어요. 먼저 올린 사람이 오늘의 주인공입니다.",
        "이름, 제목, 한 줄 설명, Streamlit 링크를 적고 등록 버튼을 누르세요.",
        "여기가 마지막 단계예요. 수고했어요!",
    )
    st.markdown('<p class="section-head"><span></span>친구들 작품 갤러리</p>', unsafe_allow_html=True)
    st.markdown('<div class="tip">배포가 끝난 Streamlit 링크를 올리면 반 전체가 볼 수 있어요. 먼저 올린 사람이 주인공 🏆</div>', unsafe_allow_html=True)

    with st.form("share_form", clear_on_submit=True):
        name = st.text_input("내 이름")
        title = st.text_input("작품 제목")
        description = st.text_input("한 줄로 소개")
        url = st.text_input("친구에게 보낼 링크", placeholder="https://...streamlit.app")
        submit = st.form_submit_button("📤 갤러리에 올리기", use_container_width=True)

    if submit:
        if not name.strip() or not title.strip() or not description.strip() or not url.strip():
            st.error("빈칸을 모두 채워 주세요.")
        elif not is_valid_http_url(url):
            st.error("링크는 http:// 또는 https:// 로 시작해야 해요. Streamlit에서 받은 주소를 그대로 붙여넣으면 됩니다.")
        else:
            try:
                add_shared_row(name, title, description, url)
                st.success("올렸어요! 아래에서 친구 작품도 열어 보세요.")
            except Exception as exc:
                st.error(str(exc))

    rows = load_shared_rows()
    st.caption(f"지금 갤러리에 {len(rows)}개 작품이 있어요")

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
    <p class="gallery-time">{row['submitted_at']}</p>
</div>
""",
                unsafe_allow_html=True,
            )
            st.link_button("▶ 이 앱 열어보기", row["url"], key=f"play_{idx}", use_container_width=True)

st.caption(f"업데이트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
