import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import google.generativeai as genai


st.set_page_config(
    page_title="MoodFlix AI - 감정 기반 영화 추천소",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.main-title {
    font-size: 2.0rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}
.sub-title {
    color: #6b7280;
    margin-bottom: 1.2rem;
}
.card {
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    background: linear-gradient(145deg, #ffffff, #f9fafb);
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    margin-bottom: 0.8rem;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_session_state() -> None:
    if "recommendations" not in st.session_state:
        st.session_state.recommendations: List[Dict[str, Any]] = []
    if "favorites" not in st.session_state:
        st.session_state.favorites: List[Dict[str, Any]] = []
    if "last_query" not in st.session_state:
        st.session_state.last_query: Dict[str, Any] = {}
    if "api_key_from_sidebar" not in st.session_state:
        st.session_state.api_key_from_sidebar = ""
    if "last_error" not in st.session_state:
        st.session_state.last_error = ""


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
    sidebar_key = st.session_state.api_key_from_sidebar.strip()
    return sidebar_key if sidebar_key else None


def clean_model_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^```json\\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\\s*", "", cleaned)
    cleaned = re.sub(r"\\s*```$", "", cleaned)
    return cleaned.strip()


def extract_json_array(text: str) -> Optional[List[Dict[str, Any]]]:
    cleaned = clean_model_text(text)
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except Exception:
        pass

    match = re.search(r"\\[\\s*{.*}\\s*]", cleaned, flags=re.DOTALL)
    if not match:
        return None

    candidate = match.group(0)
    try:
        data = json.loads(candidate)
        if isinstance(data, list):
            return data
    except Exception:
        return None
    return None


def validate_recommendation_item(item: Dict[str, Any]) -> Dict[str, Any]:
    title = str(item.get("title", "제목 정보 없음")).strip() or "제목 정보 없음"
    year = str(item.get("year", "미상")).strip() or "미상"

    genres = item.get("genres", [])
    if not isinstance(genres, list):
        genres = [str(genres)]
    genres = [str(g).strip() for g in genres if str(g).strip()]
    if not genres:
        genres = ["장르 미상"]

    reason = str(item.get("reason", "추천 이유 정보가 없습니다.")).strip() or "추천 이유 정보가 없습니다."

    mood_match_score = item.get("mood_match_score", 70)
    try:
        mood_match_score = int(mood_match_score)
    except Exception:
        mood_match_score = 70
    mood_match_score = max(0, min(100, mood_match_score))

    watch_time = str(item.get("watch_time", "약 100분")).strip() or "약 100분"
    age_rating = str(item.get("age_rating", "전체관람가")).strip() or "전체관람가"

    quote = str(item.get("quote", "오늘의 감정에 어울리는 이야기를 만나보세요.")).strip()
    if not quote:
        quote = "오늘의 감정에 어울리는 이야기를 만나보세요."

    return {
        "title": title,
        "year": year,
        "genres": genres,
        "reason": reason,
        "mood_match_score": mood_match_score,
        "watch_time": watch_time,
        "age_rating": age_rating,
        "quote": quote,
    }


def build_prompt(user_input: Dict[str, Any]) -> str:
    mood = user_input["mood"]
    mood_intensity = user_input["mood_intensity"]
    preferred_genres = ", ".join(user_input["preferred_genres"]) if user_input["preferred_genres"] else "상관없음"
    watch_time = user_input["watch_time"]
    avoid_elements = user_input["avoid_elements"] if user_input["avoid_elements"].strip() else "없음"
    language_pref = user_input["language_pref"]
    count = user_input["count"]

    return f"""
너는 영화 큐레이터야. 아래 사용자 조건을 반영해 영화 추천을 만들어.
반드시 JSON 배열만 출력하고 코드블록은 절대 포함하지 마.

[사용자 조건]
- 현재 기분: {mood}
- 감정 강도(1~10): {mood_intensity}
- 선호 장르: {preferred_genres}
- 시청 가능 시간: {watch_time}
- 피하고 싶은 요소: {avoid_elements}
- 언어 선호: {language_pref}
- 추천 개수: {count}개

[출력 형식]
아래 키를 가진 JSON 배열:
[
  {{
    "title": "영화 제목",
    "year": "개봉연도",
    "genres": ["장르1", "장르2"],
    "reason": "왜 이 사용자에게 맞는지 2~3문장",
    "mood_match_score": 0~100 정수,
    "watch_time": "예: 120분",
    "age_rating": "예: 12세 관람가",
    "quote": "영화 감성을 살리는 짧은 한 줄"
  }}
]
""".strip()


def call_gemini(api_key: str, prompt: str, temperature: float) -> List[Dict[str, Any]]:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    response = model.generate_content(
        prompt,
        generation_config={
            "temperature": temperature,
            "top_p": 0.95,
            "max_output_tokens": 2048,
        },
    )

    text = ""
    if hasattr(response, "text") and response.text:
        text = response.text
    else:
        if hasattr(response, "candidates") and response.candidates:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text or ""

    if not text.strip():
        raise ValueError("Gemini 응답이 비어 있습니다. 잠시 후 다시 시도해 주세요.")

    parsed = extract_json_array(text)
    if not parsed:
        raise ValueError("응답 파싱에 실패했습니다. 다시 시도하면 정상 동작할 수 있습니다.")

    validated = [validate_recommendation_item(item) for item in parsed if isinstance(item, dict)]
    if not validated:
        raise ValueError("유효한 추천 데이터가 없습니다.")

    return validated


def add_to_favorites(item: Dict[str, Any]) -> None:
    titles = [fav["title"] for fav in st.session_state.favorites]
    if item["title"] not in titles:
        st.session_state.favorites.append(item)
        st.toast(f"'{item['title']}' 찜 목록에 추가됨!", icon="⭐")
    else:
        st.toast(f"'{item['title']}'은(는) 이미 찜 목록에 있어요.", icon="✅")


def render_recommendation_cards(items: List[Dict[str, Any]]) -> None:
    if not items:
        st.info("아직 추천 결과가 없습니다. 왼쪽 조건을 입력하고 추천을 받아보세요.")
        return

    for idx, item in enumerate(items, start=1):
        genre_text = ", ".join(item["genres"])
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 2])

        with col_a:
            st.markdown(f"### {idx}. {item['title']} ({item['year']})")
            st.caption(f"🎭 장르: {genre_text} | ⏱️ 러닝타임: {item['watch_time']} | 🔞 등급: {item['age_rating']}")
            st.markdown(f"**추천 이유**  \\n{item['reason']}")
            st.markdown(f"> _{item['quote']}_")

        with col_b:
            st.metric("감정 매칭 점수", f"{item['mood_match_score']}점")
            st.progress(item["mood_match_score"] / 100.0)
            if st.button("⭐ 찜하기", key=f"fav_btn_{idx}_{item['title']}", use_container_width=True):
                add_to_favorites(item)

        st.markdown("</div>", unsafe_allow_html=True)


def render_favorites(items: List[Dict[str, Any]]) -> None:
    if not items:
        st.warning("찜 목록이 비어 있습니다. 추천 결과에서 '찜하기'를 눌러보세요.")
        return

    st.success(f"총 {len(items)}개의 영화를 찜했어요!")
    for idx, item in enumerate(items, start=1):
        st.markdown(f"**{idx}. {item['title']} ({item['year']})**")
        st.caption(f"장르: {', '.join(item['genres'])} | 시간: {item['watch_time']} | 등급: {item['age_rating']}")
        st.markdown(f"- 추천 이유: {item['reason']}")
        st.markdown(f"- 한 줄 감성: _{item['quote']}_")


init_session_state()

st.markdown('<div class="main-title">🎬 MoodFlix AI - 감정 기반 영화 추천소</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">오늘의 기분을 고르면 Gemini가 맞춤 영화를 추천해드립니다.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    st.markdown("Gemini API 키는 `st.secrets` 또는 아래 입력창으로 설정할 수 있습니다.")

    secret_key = get_secret_api_key()
    if secret_key:
        st.success("`st.secrets`에서 API 키를 감지했습니다.")
    else:
        st.session_state.api_key_from_sidebar = st.text_input(
            "Gemini API 키 입력",
            type="password",
            value=st.session_state.api_key_from_sidebar,
            placeholder="AIza... 형태의 키",
        )

    temperature = st.slider("창의성(temperature)", 0.0, 1.0, 0.7, 0.1)
    if st.button("🧹 결과 초기화", use_container_width=True):
        st.session_state.recommendations = []
        st.session_state.last_query = {}
        st.session_state.last_error = ""
        st.toast("추천 결과를 초기화했습니다.", icon="🧼")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("📝 추천 조건 입력")
    with st.form("recommend_form", clear_on_submit=False):
        mood = st.selectbox("오늘 기분은 어떤가요?", ["설렘", "우울함", "스트레스", "평온함", "집중하고 싶음", "웃고 싶음", "감동 받고 싶음"], index=0)
        mood_intensity = st.slider("감정 강도", 1, 10, 6)
        preferred_genres = st.multiselect("선호 장르", ["드라마", "코미디", "스릴러", "SF", "로맨스", "애니메이션", "판타지", "다큐멘터리", "액션"], default=["드라마", "코미디"])
        watch_time = st.selectbox("시청 가능 시간", ["60분 이내", "90분 이내", "120분 이내", "150분 이내", "시간 상관없음"], index=2)
        language_pref = st.radio("언어 선호", ["한국어/자막 포함", "영어권", "아시아권", "상관없음"])
        avoid_elements = st.text_area("피하고 싶은 요소(선택)", value="", placeholder="예: 잔인한 장면, 너무 무거운 결말", height=90)
        count = st.slider("추천 개수", 3, 8, 5)
        submit = st.form_submit_button("🚀 맞춤 추천 받기", use_container_width=True)

    if submit:
        active_key = get_active_api_key()
        if not active_key:
            st.error("API 키가 없습니다. `st.secrets` 또는 사이드바 입력창에 키를 설정해 주세요.")
        else:
            user_input = {
                "mood": mood,
                "mood_intensity": mood_intensity,
                "preferred_genres": preferred_genres,
                "watch_time": watch_time,
                "avoid_elements": avoid_elements,
                "language_pref": language_pref,
                "count": count,
            }
            st.session_state.last_query = user_input
            with st.spinner("Gemini가 취향을 분석하는 중입니다..."):
                try:
                    results = call_gemini(active_key, build_prompt(user_input), temperature)
                    st.session_state.recommendations = results
                    st.session_state.last_error = ""
                    st.balloons()
                except Exception as exc:
                    st.session_state.last_error = str(exc)
                    st.session_state.recommendations = []

with col_right:
    tab1, tab2, tab3 = st.tabs(["🎯 추천 결과", "⭐ 찜 목록", "📘 사용 가이드"])

    with tab1:
        if st.session_state.last_query:
            q = st.session_state.last_query
            st.caption(f"최근 요청: 기분={q['mood']} | 강도={q['mood_intensity']} | 시간={q['watch_time']} | 추천개수={q['count']}")
        if st.session_state.last_error:
            st.error(f"오류: {st.session_state.last_error}")
        render_recommendation_cards(st.session_state.recommendations)

    with tab2:
        render_favorites(st.session_state.favorites)
        if st.session_state.favorites and st.button("🗑️ 찜 목록 비우기"):
            st.session_state.favorites = []
            st.toast("찜 목록을 비웠습니다.", icon="🧺")

    with tab3:
        st.markdown("### 빠른 사용법")
        st.markdown("1) 왼쪽에서 기분/장르/시간을 입력합니다.")
        st.markdown("2) `맞춤 추천 받기` 버튼을 누릅니다.")
        st.markdown("3) 마음에 드는 영화를 `찜하기`로 저장합니다.")
        st.markdown("4) 배포 시에는 API 키를 Secrets로 관리합니다.")
        st.code('GEMINI_API_KEY = "여기에_본인_API_키"', language="toml")
        st.caption(f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
