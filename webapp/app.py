import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import streamlit as st


st.set_page_config(
    page_title="학생용 AI 웹앱 메이커",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.main-title {
    font-size: 2.1rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
}
.sub-title {
    color: #6b7280;
    margin-bottom: 1rem;
}
.block {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    background: linear-gradient(145deg, #ffffff, #f8fafc);
}
.badge {
    display: inline-block;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    font-size: 0.8rem;
    border: 1px solid #d1d5db;
    margin-right: 0.3rem;
    margin-bottom: 0.25rem;
    color: #374151;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def init_state() -> None:
    if "api_key_sidebar" not in st.session_state:
        st.session_state.api_key_sidebar = ""
    if "ideas" not in st.session_state:
        st.session_state.ideas = []
    if "prompt_pack" not in st.session_state:
        st.session_state.prompt_pack = {}
    if "last_error" not in st.session_state:
        st.session_state.last_error = ""


def get_secret_key() -> Optional[str]:
    try:
        key = st.secrets["GEMINI_API_KEY"]
        if isinstance(key, str) and key.strip():
            return key.strip()
    except Exception:
        return None
    return None


def get_active_key() -> Optional[str]:
    secret = get_secret_key()
    if secret:
        return secret
    manual = st.session_state.api_key_sidebar.strip()
    return manual if manual else None


def normalize_json(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```json\\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\\s*", "", text)
    text = re.sub(r"\\s*```$", "", text)
    return text.strip()


def parse_array(raw: str) -> Optional[List[Dict[str, Any]]]:
    text = normalize_json(raw)
    try:
        loaded = json.loads(text)
        if isinstance(loaded, list):
            return loaded
    except Exception:
        pass

    found = re.search(r"\\[\\s*{.*}\\s*]", text, flags=re.DOTALL)
    if not found:
        return None

    try:
        loaded = json.loads(found.group(0))
        if isinstance(loaded, list):
            return loaded
    except Exception:
        return None
    return None


def call_gemini(prompt: str, temperature: float = 0.8) -> str:
    api_key = get_active_key()
    if not api_key:
        raise ValueError("Gemini API 키가 없어 AI 생성 기능을 실행할 수 없습니다.")

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


def fallback_ideas(topic: str, count: int) -> List[Dict[str, Any]]:
    base = [
        {
            "app_name": "공부 루틴 코치",
            "target_user": "시험 준비 중인 학생",
            "problem": "계획은 세우지만 실천이 어렵다",
            "core_features": ["하루 목표 생성", "집중 타이머", "성취 리포트"],
            "fun_ui": ["이모지 리액션", "진행도 바", "연속 달성 배지"],
            "mini_mission": "3일 챌린지 모드 추가",
        },
        {
            "app_name": "진로 탐색 인터뷰봇",
            "target_user": "진로 고민 학생",
            "problem": "직업 정보를 찾기 어렵다",
            "core_features": ["관심사 인터뷰", "직업 추천", "학습 로드맵"],
            "fun_ui": ["카드 뒤집기", "탭 탐색", "결과 저장"],
            "mini_mission": "친구와 결과 비교 기능",
        },
        {
            "app_name": "학교생활 고민 해결소",
            "target_user": "일상 고민이 있는 학생",
            "problem": "고민을 말할 곳이 없다",
            "core_features": ["고민 분류", "해결 아이디어", "실천 체크리스트"],
            "fun_ui": ["감정 선택 버튼", "컬럼 레이아웃", "명언 팝업"],
            "mini_mission": "응원 메시지 랜덤 뽑기",
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
너는 학생 프로젝트 멘토다.
주제: {topic}
관심사: {interests}
난이도: {level}
개수: {count}

반드시 JSON 배열만 출력한다.
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
        parsed = parse_array(raw)
        if not parsed:
            return fallback_ideas(topic, count)

        clean: List[Dict[str, Any]] = []
        for item in parsed[:count]:
            core = item.get("core_features", [])
            ui = item.get("fun_ui", [])
            if not isinstance(core, list):
                core = [str(core)]
            if not isinstance(ui, list):
                ui = [str(ui)]

            clean.append(
                {
                    "app_name": str(item.get("app_name", "학생 맞춤 앱")),
                    "target_user": str(item.get("target_user", "학생")),
                    "problem": str(item.get("problem", "문제 정의 필요")),
                    "core_features": [str(x) for x in core[:3]] if core else ["기능1", "기능2", "기능3"],
                    "fun_ui": [str(x) for x in ui[:3]] if ui else ["사이드바", "버튼", "결과 카드"],
                    "mini_mission": str(item.get("mini_mission", "미션 1개 추가")),
                }
            )

        if len(clean) < count:
            clean.extend(fallback_ideas(topic, count - len(clean)))
        return clean[:count]
    except Exception:
        return fallback_ideas(topic, count)


def build_prompt_pack(app_idea: str, target_user: str, required_features: str, tone: str) -> Dict[str, str]:
    streamlit_prompt = f"""
너는 세계 최고 수준의 Streamlit 개발 멘토다.
아래 조건으로 초보 학생이 바로 실행 가능한 단일 app.py 전체 코드를 작성해줘.

[아이디어]
{app_idea}

[타겟 사용자]
{target_user}

[반드시 포함할 기능]
{required_features}

[톤]
{tone}

요구사항:
- 코드 전체를 한 번에 제시
- st.secrets[\"GEMINI_API_KEY\"] 우선 사용, 없으면 사이드바 입력
- 사이드바, 컬럼, 탭, 버튼, 진행도 UI 활용
- 예외 처리 포함
- requirements.txt 내용도 마지막에 제시
""".strip()

    html_prompt = f"""
너는 학생용 웹앱 UI 디자이너다.
아래 아이디어를 바탕으로 단일 HTML 파일(index.html) 코드를 작성해줘.

아이디어: {app_idea}
타겟 사용자: {target_user}
필수 기능: {required_features}

요구사항:
- HTML/CSS/JS 한 파일
- 모바일 반응형
- 재미 요소(애니메이션, 상태 배지, 카드) 포함
- 한국어 UI
""".strip()

    convert_prompt = f"""
아래 HTML 아이디어를 Streamlit app.py로 재구성해줘.
기능적 동등성을 유지하고, 학생이 수정하기 쉬운 구조로 만들어줘.

아이디어: {app_idea}
필수 기능: {required_features}

반드시 포함:
- 함수 분리
- 세션 상태
- 버튼/입력 검증
- 친절한 한국어 주석
""".strip()

    return {
        "streamlit_prompt": streamlit_prompt,
        "html_prompt": html_prompt,
        "convert_prompt": convert_prompt,
    }


def process_steps_markdown() -> str:
    return "\n".join(
        [
            "## Gemini + GitHub + Streamlit 웹앱 제작 전체 흐름",
            "",
            "1. 주제 정하기: 학생이 좋아하는 키워드 1개 선택",
            "2. Gemini로 아이디어 구체화: 문제/타겟/핵심 기능 3개 확정",
            "3. Gemini로 코드 생성: HTML 또는 app.py 프롬프트 실행",
            "4. 로컬 실행 및 수정: streamlit run app.py",
            "5. GitHub 업로드: repo 생성 후 add/commit/push",
            "6. Streamlit Community Cloud 배포: repo 연결 + Secrets 설정",
            "7. 발표/피드백: 개선 포인트 반영해 v2 배포",
            "",
            "### 수업 꿀팁",
            "- 기능 욕심보다 '한 가지 문제를 잘 해결'하는 앱이 더 좋음",
            "- 매 차시 끝에 5분 회고: 오늘 막힌 점 1개 + 해결한 점 1개",
            "- 커밋 메시지는 feat/fix/docs 규칙으로 깔끔하게",
        ]
    )


init_state()

st.markdown('<div class="main-title">🧠 학생용 AI 웹앱 메이커</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Gemini + GitHub + Streamlit으로 아이디어부터 배포까지 한 번에 진행하는 수업용 도우미 앱</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🔐 API 설정")
    secret_key = get_secret_key()
    if secret_key:
        st.success("st.secrets에서 GEMINI_API_KEY를 찾았습니다.")
    else:
        st.session_state.api_key_sidebar = st.text_input(
            "Gemini API 키",
            type="password",
            value=st.session_state.api_key_sidebar,
            placeholder="AIza...",
            help="키가 없어도 기본 예시 모드로 동작합니다.",
        )

    st.markdown("---")
    st.subheader("🎛️ 수업 설정")
    level = st.selectbox("난이도", ["입문", "기초", "중급"], index=0)
    class_mode = st.selectbox("진행 방식", ["자유 탐구형", "미션 챌린지형", "멘토링형"], index=1)
    team_style = st.radio("팀 구성", ["개인", "2인", "3인"], index=1)

    st.markdown("---")
    if st.button("🧹 결과 초기화", use_container_width=True):
        st.session_state.ideas = []
        st.session_state.prompt_pack = {}
        st.session_state.last_error = ""
        st.toast("생성 결과를 초기화했습니다.", icon="🧼")

k1, k2, k3 = st.columns(3)
with k1:
    st.metric("추천 수업 흐름", "설명 → 제작 → 배포")
with k2:
    st.metric("권장 커밋 수", "차시당 2회+")
with k3:
    st.metric("현재 진행 모드", class_mode)

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(
    [
        "0. 제작 과정 설명(먼저)",
        "1. 웹앱 아이디어 추천",
        "2. 프롬프트 생성 도우미",
        "3. HTML + app.py 생성법",
        "4. GitHub 업로드 방법",
        "5. Streamlit 배포 방법",
    ]
)

with tab0:
    st.subheader("수업 전체 흐름")
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown(process_steps_markdown())
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 차시별 미션")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("- **1차시**: 주제 고르기 + UI 뼈대 만들기")
        st.markdown("- **2차시**: Gemini 연동 + 핵심 기능 구현")
    with c2:
        st.markdown("- **3차시**: GitHub 정리 + README 작성")
        st.markdown("- **4차시**: 배포 + 발표 + 피드백 반영")

    st.download_button(
        "📥 수업 흐름 가이드 다운로드(.md)",
        data=process_steps_markdown(),
        file_name="student_webapp_course_flow.md",
        mime="text/markdown",
        use_container_width=True,
    )

with tab1:
    st.subheader("웹앱 아이디어 추천")
    topic = st.text_input("주제/키워드", value="학교 생활", placeholder="예: 영화 추천, 진로 탐색, 공부 습관")
    interests = st.text_input("학생 관심사", value="게임, 음악, 친구, 진로", placeholder="콤마로 입력")
    count = st.slider("아이디어 개수", 3, 10, 5)

    if st.button("✨ 아이디어 생성", type="primary", use_container_width=True):
        with st.spinner("학생용 아이디어를 생성하고 있습니다..."):
            st.session_state.ideas = generate_ideas(topic, interests, level, count)
            st.balloons()

    if st.session_state.ideas:
        for idx, item in enumerate(st.session_state.ideas, start=1):
            st.markdown('<div class="block">', unsafe_allow_html=True)
            st.markdown(f"### {idx}. {item['app_name']}")
            st.markdown(f"- **타겟**: {item['target_user']}")
            st.markdown(f"- **해결 문제**: {item['problem']}")
            st.markdown("- **핵심 기능**")
            for feature in item["core_features"]:
                st.markdown(f"  - {feature}")
            st.markdown("- **재미 UI 요소**")
            for ui in item["fun_ui"]:
                st.markdown(f"  - {ui}")
            st.markdown(f"- **미니 미션**: {item['mini_mission']}")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("주제를 입력하고 아이디어를 생성해보세요.")

with tab2:
    st.subheader("학생 아이디어를 실제 앱으로 바꾸는 프롬프트 도우미")
    app_idea = st.text_area(
        "학생 아이디어 설명",
        value="학생들의 시험 스트레스를 줄여주는 AI 응원+학습 루틴 추천 앱",
        height=90,
    )
    target_user = st.text_input("타겟 사용자", value="고등학생")
    required_features = st.text_area(
        "반드시 넣을 기능",
        value="감정 선택, 루틴 추천, 체크리스트, 결과 저장, 재미 요소(배지)",
        height=90,
    )
    tone = st.selectbox("프롬프트 스타일", ["친절하고 쉬운", "실전형", "창의적이고 재미있는"], index=0)

    if st.button("🛠️ 프롬프트 3종 생성", type="primary", use_container_width=True):
        st.session_state.prompt_pack = build_prompt_pack(app_idea, target_user, required_features, tone)

    if st.session_state.prompt_pack:
        st.markdown('<div class="block">', unsafe_allow_html=True)
        st.markdown("### A) Streamlit app.py 생성 프롬프트")
        st.text_area(
            "streamlit_prompt",
            value=st.session_state.prompt_pack["streamlit_prompt"],
            height=220,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="block">', unsafe_allow_html=True)
        st.markdown("### B) HTML 단일 파일 생성 프롬프트")
        st.text_area(
            "html_prompt",
            value=st.session_state.prompt_pack["html_prompt"],
            height=180,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="block">', unsafe_allow_html=True)
        st.markdown("### C) HTML → app.py 변환 프롬프트")
        st.text_area(
            "convert_prompt",
            value=st.session_state.prompt_pack["convert_prompt"],
            height=180,
            label_visibility="collapsed",
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("아이디어를 입력하고 프롬프트 3종을 생성해보세요.")

with tab3:
    st.subheader("Gemini로 HTML 코드와 app.py 코드 생성하는 법")
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown("### 1) HTML 먼저 만들기")
    st.markdown("- Gemini에게 '단일 HTML 파일'을 요청")
    st.markdown("- 핵심: 타겟 사용자, 기능 3개, UI 스타일, 반응형 조건 명시")
    st.code(
        """[예시 프롬프트]\n학생용 할 일 관리 웹앱을 HTML/CSS/JS 단일 파일로 만들어줘.\n기능: 할 일 추가, 우선순위, 완료 체크, 달성률 표시\n조건: 모바일 반응형, 귀여운 디자인, 한국어 UI""",
        language="text",
    )

    st.markdown("### 2) app.py 생성 또는 변환")
    st.markdown("- HTML 결과를 바탕으로 Streamlit 버전 app.py 생성")
    st.markdown("- `st.secrets` 기반 API 키 처리와 예외처리 포함 요청")
    st.code(
        """[예시 프롬프트]\n아래 HTML 아이디어를 Streamlit app.py로 변환해줘.\n반드시 탭, 사이드바, 세션상태, 오류처리를 넣고\n초보 학생도 이해할 수 있게 한국어 주석을 달아줘.""",
        language="text",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.subheader("GitHub에 코드 업로드하는 방법")
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown("### 순서")
    st.markdown("1. GitHub에서 새 저장소 생성")
    st.markdown("2. 로컬 폴더에서 아래 명령 실행")
    st.code(
        """git init\ngit add .\ngit commit -m "feat: first student webapp"\ngit branch -M main\ngit remote add origin https://github.com/사용자명/저장소명.git\ngit push -u origin main""",
        language="bash",
    )
    st.markdown("3. 수정할 때마다 `add -> commit -> push` 반복")
    st.markdown("4. README에 실행법/스크린샷/배포링크 기록")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 커밋 메시지 추천")
    st.markdown("<span class='badge'>feat: 기능 추가</span><span class='badge'>fix: 버그 수정</span><span class='badge'>docs: 문서 수정</span>", unsafe_allow_html=True)

with tab5:
    st.subheader("GitHub 폴더를 Streamlit으로 배포하는 방법")
    st.markdown('<div class="block">', unsafe_allow_html=True)
    st.markdown("### Streamlit Community Cloud 배포 단계")
    st.markdown("1. [share.streamlit.io](https://share.streamlit.io/) 로그인")
    st.markdown("2. `New app` 클릭")
    st.markdown("3. Repository: 본인 GitHub 저장소 선택")
    st.markdown("4. Branch: `main`")
    st.markdown("5. Main file path: `app.py` 또는 `webapp/app.py`")
    st.markdown("6. Advanced settings > Secrets에 API 키 등록")
    st.code('GEMINI_API_KEY = "여기에_본인_API_키"', language="toml")
    st.markdown("7. Deploy 클릭 후 URL 공유")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 배포 전 점검 체크")
    d1 = st.checkbox("requirements.txt에 필요한 패키지 작성 완료")
    d2 = st.checkbox("main file path 확인 완료")
    d3 = st.checkbox("Secrets에 API 키 입력 완료")
    d4 = st.checkbox("배포 후 직접 기능 테스트 완료")

    done = sum([d1, d2, d3, d4])
    ratio = done / 4
    st.progress(ratio)
    st.caption(f"배포 준비도: {done}/4 ({int(ratio * 100)}%)")

    if ratio == 1.0:
        st.success("배포 준비 완료! 지금 바로 Deploy 해도 좋습니다.")

st.caption(f"현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 팀 구성: {team_style}")
