import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import streamlit as st


st.set_page_config(
    page_title="AI 웹앱 수업 메이커",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.title {
    font-size: 2.1rem;
    font-weight: 800;
    margin-bottom: 0.25rem;
}
.subtitle {
    color: #6b7280;
    margin-bottom: 1.1rem;
}
.card {
    padding: 1rem;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    margin-bottom: 0.8rem;
}
.kpi {
    font-size: 1rem;
    color: #374151;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_state() -> None:
    if "api_key_sidebar" not in st.session_state:
        st.session_state.api_key_sidebar = ""
    if "class_plan" not in st.session_state:
        st.session_state.class_plan = []
    if "student_ideas" not in st.session_state:
        st.session_state.student_ideas = []
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
    manual_key = st.session_state.api_key_sidebar.strip()
    return manual_key if manual_key else None


def normalize_json_text(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```json\\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\\s*", "", text)
    text = re.sub(r"\\s*```$", "", text)
    return text.strip()


def parse_json_array(raw: str) -> Optional[List[Dict[str, Any]]]:
    text = normalize_json_text(raw)
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return obj
    except Exception:
        pass

    match = re.search(r"\\[\\s*{.*}\\s*]", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        obj = json.loads(match.group(0))
        if isinstance(obj, list):
            return obj
    except Exception:
        return None
    return None


def call_gemini(prompt: str, temperature: float = 0.7) -> str:
    api_key = get_active_api_key()
    if not api_key:
        raise ValueError("API 키가 없어 Gemini 호출을 진행할 수 없습니다.")

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
        raise ValueError("Gemini 응답이 비어 있습니다. 잠시 후 다시 시도해 주세요.")

    return text


def fallback_class_plan(theme: str) -> List[Dict[str, str]]:
    return [
        {
            "session": "1차시",
            "goal": "환경 구축 + 앱 뼈대 완성",
            "activities": "Python 가상환경, Streamlit 기본 UI(사이드바/컬럼/버튼) 만들기, 개인 주제 1차 선정",
            "deliverable": "실행되는 기본 app.py",
            "fun_point": "아이스브레이킹: 5분 랜덤 아이디어 피칭",
        },
        {
            "session": "2차시",
            "goal": "Gemini API 연동 + 프롬프트 설계",
            "activities": "st.secrets 설정, 입력 폼 구성, JSON 출력 파싱, 오류 처리 강화",
            "deliverable": "AI 응답이 앱 UI에 표시되는 버전",
            "fun_point": "프롬프트 배틀: 같은 주제로 가장 창의적 결과 뽑기",
        },
        {
            "session": "3차시",
            "goal": "GitHub 협업 + 기능 고도화",
            "activities": "repo 생성, 커밋 메시지 규칙, 기능 1개 추가(시각화/즐겨찾기/다운로드)",
            "deliverable": "README 포함 공개 저장소",
            "fun_point": "짝 코드리뷰: 서로의 앱 장점 3개 찾기",
        },
        {
            "session": "4차시",
            "goal": "Streamlit Cloud 배포 + 발표",
            "activities": "Cloud 연결, Secrets 등록, 배포 URL 공유, 데모 발표",
            "deliverable": "배포 완료 URL + 발표 자료",
            "fun_point": f"테마 '{theme}' 기반 미니 해커톤 발표회",
        },
    ]


def fallback_student_ideas(topic: str, count: int) -> List[Dict[str, Any]]:
    base = [
        {
            "app_name": "아이디어 스파크",
            "one_line": "하루 고민을 입력하면 AI가 해결 루트를 제안하는 코치 앱",
            "core_features": ["감정 분석", "행동 플랜 생성", "격려 멘트 카드"],
            "ui_points": ["이모지 반응", "진행도 바", "결과 카드"],
            "github_mission": "README에 사용 시나리오 GIF 넣기",
            "deploy_tip": "Secrets에 GEMINI_API_KEY 등록",
        },
        {
            "app_name": "나만의 퀴즈 메이커",
            "one_line": "주제 입력 시 개인 맞춤 퀴즈를 자동 생성하는 학습 앱",
            "core_features": ["난이도 선택", "즉시 채점", "오답 리포트"],
            "ui_points": ["탭 분리", "점수 배지", "재도전 버튼"],
            "github_mission": "Issues로 개선 아이디어 3개 작성",
            "deploy_tip": "첫 화면에 사용법 3줄 배치",
        },
        {
            "app_name": "취향 여행 코디",
            "one_line": "기분과 예산을 입력하면 여행 코스를 추천하는 플래너",
            "core_features": ["조건 입력 폼", "추천 일정", "준비물 체크"],
            "ui_points": ["2열 레이아웃", "체크박스", "하이라이트 카드"],
            "github_mission": "커밋 메시지에 feat/fix/docs 규칙 적용",
            "deploy_tip": "배포 후 모바일 화면 점검",
        },
    ]
    results: List[Dict[str, Any]] = []
    for idx in range(count):
        item = base[idx % len(base)].copy()
        item["app_name"] = f"{item['app_name']} - {topic} {idx + 1}"
        results.append(item)
    return results


def generate_class_plan(theme: str, level: str, students: int, session_minutes: int, style: str) -> List[Dict[str, Any]]:
    prompt = f"""
너는 한국 고등학교/대학생 대상 AI 프로젝트 수업 코치다.
주제는 '{theme}' 이고, 난이도는 '{level}', 학습자 수는 {students}명, 차시당 {session_minutes}분이다.
진행 스타일은 '{style}'이다.

정확히 4개 원소를 가진 JSON 배열만 출력해라. 설명문 금지.
각 원소는 다음 키를 가져야 한다:
- session (예: 1차시)
- goal
- activities
- deliverable
- fun_point
""".strip()

    try:
        raw = call_gemini(prompt, temperature=0.65)
        parsed = parse_json_array(raw)
        if not parsed or len(parsed) < 4:
            return fallback_class_plan(theme)

        safe_list: List[Dict[str, Any]] = []
        for i in range(4):
            item = parsed[i] if i < len(parsed) else {}
            safe_list.append(
                {
                    "session": str(item.get("session", f"{i + 1}차시")),
                    "goal": str(item.get("goal", "학습 목표 설정")),
                    "activities": str(item.get("activities", "핵심 활동 진행")),
                    "deliverable": str(item.get("deliverable", "결과물 정리")),
                    "fun_point": str(item.get("fun_point", "흥미 요소 추가")),
                }
            )
        return safe_list
    except Exception:
        return fallback_class_plan(theme)


def generate_student_ideas(topic: str, level: str, count: int) -> List[Dict[str, Any]]:
    prompt = f"""
너는 웹앱 아이디어 멘토다.
주제 키워드 '{topic}', 난이도 '{level}' 기준으로 학생 프로젝트 아이디어를 {count}개 제안해라.

반드시 JSON 배열만 출력.
각 원소 키:
- app_name
- one_line
- core_features (문자열 배열 3개)
- ui_points (문자열 배열 3개)
- github_mission
- deploy_tip
""".strip()

    try:
        raw = call_gemini(prompt, temperature=0.8)
        parsed = parse_json_array(raw)
        if not parsed:
            return fallback_student_ideas(topic, count)

        safe_ideas: List[Dict[str, Any]] = []
        for item in parsed[:count]:
            core = item.get("core_features", [])
            ui_points = item.get("ui_points", [])
            if not isinstance(core, list):
                core = [str(core)]
            if not isinstance(ui_points, list):
                ui_points = [str(ui_points)]

            safe_ideas.append(
                {
                    "app_name": str(item.get("app_name", "프로젝트 아이디어")),
                    "one_line": str(item.get("one_line", "학생 맞춤 웹앱 아이디어입니다.")),
                    "core_features": [str(x) for x in core[:3]] if core else ["핵심 기능 1", "핵심 기능 2", "핵심 기능 3"],
                    "ui_points": [str(x) for x in ui_points[:3]] if ui_points else ["사이드바", "컬럼", "버튼 상호작용"],
                    "github_mission": str(item.get("github_mission", "커밋 메시지 규칙 적용")),
                    "deploy_tip": str(item.get("deploy_tip", "Secrets 설정 확인")),
                }
            )

        if len(safe_ideas) < count:
            safe_ideas.extend(fallback_student_ideas(topic, count - len(safe_ideas)))
        return safe_ideas[:count]
    except Exception:
        return fallback_student_ideas(topic, count)


def export_plan_markdown(plan: List[Dict[str, Any]]) -> str:
    lines = [
        "# 4차시 수업 운영안",
        "",
        f"생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for row in plan:
        lines.append(f"## {row['session']}")
        lines.append(f"- 목표: {row['goal']}")
        lines.append(f"- 활동: {row['activities']}")
        lines.append(f"- 산출물: {row['deliverable']}")
        lines.append(f"- 흥미 요소: {row['fun_point']}")
        lines.append("")
    return "\n".join(lines)


init_state()

st.markdown('<div class="title">🚀 AI 웹앱 수업 메이커 (Gemini + GitHub + Streamlit)</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">학생들이 각자 원하는 웹앱을 4차시 안에 완성하도록 수업 흐름과 프로젝트 아이디어를 자동 설계합니다.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔐 API 설정")
    secret_key = get_secret_api_key()
    if secret_key:
        st.success("st.secrets에서 GEMINI_API_KEY를 찾았습니다.")
    else:
        st.session_state.api_key_sidebar = st.text_input(
            "Gemini API 키",
            type="password",
            value=st.session_state.api_key_sidebar,
            placeholder="AIza...",
            help="없어도 앱은 예시 모드로 동작합니다.",
        )

    st.markdown("---")
    st.subheader("🎛️ 수업 공통 옵션")
    level = st.selectbox("학습 난이도", ["입문", "기초", "중급"], index=0)
    students = st.slider("학생 수", 5, 40, 24)
    session_minutes = st.slider("차시당 시간(분)", 30, 100, 50, 5)
    style = st.selectbox("진행 스타일", ["자유 탐구형", "미션 챌린지형", "멘토링 중심형"], index=0)

    st.markdown("---")
    if st.button("🧹 결과 초기화", use_container_width=True):
        st.session_state.class_plan = []
        st.session_state.student_ideas = []
        st.session_state.last_error = ""
        st.toast("결과를 초기화했습니다.", icon="🧼")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("수업 차시", "4회")
with col2:
    st.metric("권장 팀 구성", "2~3인")
with col3:
    st.metric("핵심 스택", "Gemini+GitHub+Streamlit")

main_tab, idea_tab, tracker_tab = st.tabs(["🧭 4차시 수업 설계", "💡 학생 아이디어 생성", "✅ GitHub/배포 체크리스트"])

with main_tab:
    st.subheader("수업 운영안 자동 생성")
    theme = st.text_input("수업 전체 테마", value="학생 맞춤 AI 웹앱 제작", placeholder="예: 진로 탐색, 생활 문제 해결, 학습 도우미")

    if st.button("4차시 운영안 만들기", type="primary", use_container_width=True):
        with st.spinner("수업 운영안을 구성하고 있습니다..."):
            plan = generate_class_plan(theme, level, students, session_minutes, style)
            st.session_state.class_plan = plan
            st.session_state.last_error = ""

    if st.session_state.class_plan:
        for row in st.session_state.class_plan:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {row['session']} - {row['goal']}")
            st.markdown(f"- **핵심 활동**: {row['activities']}")
            st.markdown(f"- **산출물**: {row['deliverable']}")
            st.markdown(f"- **흥미 요소**: {row['fun_point']}")
            st.markdown("</div>", unsafe_allow_html=True)

        md_text = export_plan_markdown(st.session_state.class_plan)
        st.download_button(
            "📥 운영안 Markdown 다운로드",
            data=md_text,
            file_name="class_plan_4_sessions.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.info("테마를 입력하고 '4차시 운영안 만들기'를 눌러주세요.")

with idea_tab:
    st.subheader("학생별 프로젝트 아이디어 뽑기")
    topic = st.text_input("키워드/주제", value="영화 추천", placeholder="예: 고민 상담소, 영단어 암기장, 진로 탐색")
    idea_count = st.slider("생성 개수", 3, 10, 5)

    if st.button("아이디어 생성", type="primary", use_container_width=True):
        with st.spinner("학생용 프로젝트 아이디어를 생성하는 중입니다..."):
            ideas = generate_student_ideas(topic, level, idea_count)
            st.session_state.student_ideas = ideas
            st.balloons()

    if st.session_state.student_ideas:
        for idx, item in enumerate(st.session_state.student_ideas, start=1):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {idx}. {item['app_name']}")
            st.markdown(f"**한 줄 설명**: {item['one_line']}")
            st.markdown("**핵심 기능 3가지**")
            for feature in item["core_features"]:
                st.markdown(f"- {feature}")
            st.markdown("**UI 포인트 3가지**")
            for point in item["ui_points"]:
                st.markdown(f"- {point}")
            st.markdown(f"**GitHub 미션**: {item['github_mission']}")
            st.markdown(f"**배포 팁**: {item['deploy_tip']}")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("키워드를 입력하고 '아이디어 생성'을 눌러주세요.")

with tracker_tab:
    st.subheader("수업 운영 체크리스트")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### GitHub 체크")
        st.checkbox("학생별 저장소 생성 완료", key="g1")
        st.checkbox("커밋 메시지 규칙(feat/fix/docs) 설명 완료", key="g2")
        st.checkbox("README에 실행 방법 작성 완료", key="g3")
        st.checkbox("최종 코드 push 완료", key="g4")

    with c2:
        st.markdown("### Streamlit 배포 체크")
        st.checkbox("Streamlit Community Cloud 연결", key="d1")
        st.checkbox("Main file path 설정(webapp/app.py 또는 app.py)", key="d2")
        st.checkbox("Secrets에 GEMINI_API_KEY 등록", key="d3")
        st.checkbox("배포 URL 공유 및 발표 완료", key="d4")

    progress_items = [
        st.session_state.get("g1", False),
        st.session_state.get("g2", False),
        st.session_state.get("g3", False),
        st.session_state.get("g4", False),
        st.session_state.get("d1", False),
        st.session_state.get("d2", False),
        st.session_state.get("d3", False),
        st.session_state.get("d4", False),
    ]
    done = sum(1 for x in progress_items if x)
    ratio = done / len(progress_items)

    st.markdown("### 진행도")
    st.progress(ratio)
    st.caption(f"완료 {done}/8 | {int(ratio * 100)}% 진행")

st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
