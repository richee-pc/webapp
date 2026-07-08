import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import streamlit as st


st.set_page_config(
    page_title="학생용 AI 웹앱 스타터",
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

LINK_BOARD_PATH = Path(__file__).resolve().parent / "shared_links.json"


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
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


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
    typed = st.session_state.api_key_sidebar.strip()
    return typed if typed else None


def normalize_json(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```json\\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\\s*", "", text)
    text = re.sub(r"\\s*```$", "", text)
    return text.strip()


def parse_array(raw: str) -> Optional[List[Dict[str, Any]]]:
    text = normalize_json(raw)
    try:
        arr = json.loads(text)
        if isinstance(arr, list):
            return arr
    except Exception:
        pass

    found = re.search(r"\\[\\s*{.*}\\s*]", text, flags=re.DOTALL)
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
    api_key = get_active_key()
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
        parsed = parse_array(raw)
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
            "",
            "### 빠른 실행 명령",
            "```bash",
            "pip install -r requirements.txt",
            "streamlit run app.py",
            "```",
        ]
    )


def build_presentation_markdown(
    app_name: str,
    one_line: str,
    features: List[str],
    github_url: str,
    deploy_url: str,
    challenge: str,
    improvement: str,
) -> str:
    feature_lines = [f"- {f.strip()}" for f in features if f.strip()]
    if not feature_lines:
        feature_lines = ["- 핵심 기능을 1개 이상 작성해 주세요."]

    return "\n".join(
        [
            f"# {app_name or '내 웹앱 프로젝트'}",
            "",
            "## 한 줄 소개",
            one_line or "한 줄 소개를 작성해 주세요.",
            "",
            "## 핵심 기능",
            *feature_lines,
            "",
            "## 프로젝트 링크",
            f"- GitHub: {github_url or '링크를 입력해 주세요.'}",
            f"- 배포 URL: {deploy_url or '링크를 입력해 주세요.'}",
            "",
            "## 만들면서 어려웠던 점",
            challenge or "어려웠던 점을 작성해 주세요.",
            "",
            "## 다음 버전에서 개선할 점",
            improvement or "개선할 점을 작성해 주세요.",
            "",
            f"_작성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        ]
    )


def build_presentation_script(
    app_name: str,
    one_line: str,
    features: List[str],
    deploy_url: str,
) -> str:
    clean_features = [f.strip() for f in features if f.strip()]
    top_features = clean_features[:3] if clean_features else ["핵심 기능"]

    return (
        f"안녕하세요. 저희가 만든 앱은 '{app_name or '내 웹앱'}' 입니다. "
        f"이 앱은 {one_line or '학생이 직접 문제를 해결하도록 돕는 웹앱'} 를 목표로 만들었습니다. "
        f"특히 {', '.join(top_features)} 기능을 구현했습니다. "
        f"배포 주소는 {deploy_url or '배포 주소 입력 예정'} 이고, 발표 후 피드백을 반영해 더 개선하겠습니다."
    )


def is_valid_http_url(url: str) -> bool:
    return bool(re.match(r"^https?://[^\s]+$", url.strip()))


def load_shared_links() -> List[Dict[str, str]]:
    if not LINK_BOARD_PATH.exists():
        return []
    try:
        content = json.loads(LINK_BOARD_PATH.read_text(encoding="utf-8"))
        if isinstance(content, list):
            safe_rows = []
            for row in content:
                if not isinstance(row, dict):
                    continue
                safe_rows.append(
                    {
                        "student": str(row.get("student", "익명")),
                        "app_name": str(row.get("app_name", "이름 없는 앱")),
                        "url": str(row.get("url", "")),
                        "memo": str(row.get("memo", "")),
                        "submitted_at": str(row.get("submitted_at", "")),
                    }
                )
            return safe_rows
    except Exception:
        return []
    return []


def save_shared_links(rows: List[Dict[str, str]]) -> None:
    LINK_BOARD_PATH.write_text(
        json.dumps(rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def add_shared_link(student: str, app_name: str, url: str, memo: str) -> None:
    rows = load_shared_links()
    clean_url = url.strip()

    # 같은 URL 중복 제출 방지
    if any(r.get("url", "").strip() == clean_url for r in rows):
        raise ValueError("이미 제출된 링크입니다. 다른 링크를 입력해 주세요.")

    rows.insert(
        0,
        {
            "student": student.strip(),
            "app_name": app_name.strip(),
            "url": clean_url,
            "memo": memo.strip(),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    save_shared_links(rows)


init_state()

st.markdown('<div class="main-title">✨ 학생용 AI 웹앱 스타터</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">아이디어 추천 → 프롬프트 생성 → 코드 생성 → GitHub 업로드 → Streamlit 배포를 한 번에!</div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("🔐 Gemini API 설정")
    secret = get_secret_key()
    if secret:
        st.success("secrets에서 API 키를 찾았어요.")
    else:
        st.session_state.api_key_sidebar = st.text_input(
            "Gemini API 키",
            type="password",
            value=st.session_state.api_key_sidebar,
            placeholder="AIza...",
            help="키가 없어도 아이디어/프롬프트 기본 기능은 사용 가능해요.",
        )

    st.markdown("---")
    st.session_state.level = st.selectbox("난이도", ["입문", "기초", "중급"], index=0)
    st.markdown("---")
    if st.button("🧹 전체 초기화", use_container_width=True):
        st.session_state.ideas = []
        st.session_state.prompt_pack = {}
        st.session_state.selected_idea = ""
        st.session_state.selected_target = "학생"
        st.session_state.selected_features = ""
        st.toast("초기화 완료!", icon="🧼")

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("오늘 목표", "내 앱 1개 배포")
with m2:
    st.metric("추천 작업 순서", "아이디어 → 프롬프트")
with m3:
    st.metric("현재 난이도", st.session_state.level)


tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "0. 제작 과정 설명",
        "1. 아이디어 추천",
        "2. 프롬프트 생성 도우미",
        "3. HTML/app.py 생성법",
        "4. GitHub 업로드",
        "5. Streamlit 배포",
        "6. 발표/공유",
    ]
)

with tab0:
    st.subheader("먼저 이 순서대로 진행하면 쉬워요")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(process_flow_markdown())
    st.markdown("</div>", unsafe_allow_html=True)
    st.download_button(
        "📥 제작 순서 가이드 다운로드",
        data=process_flow_markdown(),
        file_name="student_webapp_flow.md",
        mime="text/markdown",
    )

with tab1:
    st.subheader("웹앱 아이디어 추천")
    col_a, col_b = st.columns([2, 2])
    with col_a:
        st.session_state.topic_input = st.text_input("주제/키워드", value=st.session_state.topic_input)
    with col_b:
        st.session_state.interest_input = st.text_input("관심사", value=st.session_state.interest_input)
    idea_count = st.slider("추천 개수", 3, 10, 5)

    if st.button("✨ 아이디어 생성", type="primary", use_container_width=True):
        with st.spinner("아이디어 생성 중..."):
            st.session_state.ideas = generate_ideas(
                st.session_state.topic_input,
                st.session_state.interest_input,
                st.session_state.level,
                idea_count,
            )
            st.balloons()

    if st.session_state.ideas:
        st.markdown('<div class="tip">마음에 드는 아이디어에서 <b>이 아이디어 선택</b>을 누르면 2번 탭 프롬프트 입력칸에 자동 반영됩니다.</div>', unsafe_allow_html=True)
        for idx, idea in enumerate(st.session_state.ideas, start=1):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"### {idx}. {idea['app_name']}")
            st.markdown(f"- 타겟: {idea['target_user']}")
            st.markdown(f"- 해결 문제: {idea['problem']}")
            st.markdown("- 핵심 기능")
            for f in idea["core_features"]:
                st.markdown(f"  - {f}")
            st.markdown("- 재미 UI")
            for u in idea["fun_ui"]:
                st.markdown(f"  - {u}")
            st.markdown(f"- 미니 미션: {idea['mini_mission']}")
            if st.button("✅ 이 아이디어 선택", key=f"pick_{idx}", use_container_width=True):
                fill_prompt_from_idea(idea)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("주제와 관심사를 넣고 아이디어를 만들어 보세요.")

with tab2:
    st.subheader("프롬프트 생성 도우미")
    st.caption("1번 탭에서 아이디어를 선택하면 아래 입력칸이 자동으로 채워져요.")

    app_idea = st.text_area(
        "아이디어 설명",
        value=st.session_state.selected_idea,
        height=90,
        placeholder="예: 시험 스트레스 줄여주는 AI 루틴 앱",
    )
    target_user = st.text_input("타겟 사용자", value=st.session_state.selected_target)
    required_features = st.text_area(
        "필수 기능",
        value=st.session_state.selected_features,
        height=80,
        placeholder="예: 감정 선택, 추천 결과 카드, 진행도 바",
    )

    if st.button("🛠️ 프롬프트 3종 만들기", type="primary", use_container_width=True):
        if not app_idea.strip() or not required_features.strip():
            st.error("아이디어 설명과 필수 기능을 입력해 주세요.")
        else:
            st.session_state.prompt_pack = build_prompt_pack(
                app_idea.strip(),
                target_user.strip() or "학생",
                required_features.strip(),
                st.session_state.level,
            )
            st.success("프롬프트 생성 완료! 아래 코드블록 복사 아이콘으로 바로 복사해서 Gemini에 붙여넣으세요.")

    pack = st.session_state.prompt_pack
    if pack:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### A. HTML 코드 생성 프롬프트 (복사해서 Gemini에 붙여넣기)")
        st.code(pack["html_prompt"], language="text")
        st.download_button(
            "HTML 프롬프트 .txt 다운로드",
            data=pack["html_prompt"],
            file_name="prompt_html_generation.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### B. Streamlit app.py 생성 프롬프트")
        st.code(pack["streamlit_prompt"], language="text")
        st.download_button(
            "app.py 프롬프트 .txt 다운로드",
            data=pack["streamlit_prompt"],
            file_name="prompt_streamlit_generation.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### C. HTML → app.py 변환 프롬프트")
        st.code(pack["convert_prompt"], language="text")
        st.download_button(
            "변환 프롬프트 .txt 다운로드",
            data=pack["convert_prompt"],
            file_name="prompt_html_to_streamlit.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("아이디어를 입력하고 프롬프트 3종을 생성해 보세요.")

with tab3:
    st.subheader("Gemini로 HTML / app.py 코드 잘 뽑는 팁")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("- 요구사항은 숫자로 나눠서 쓰면 결과가 훨씬 정확해져요.")
    st.markdown("- 출력 형식을 꼭 지정하세요. (예: 코드블록 하나만 출력)")
    st.markdown("- 실패하면 기능을 줄여서 먼저 성공 버전을 만들고 확장하세요.")
    st.markdown("- 생성 직후 바로 실행해서 에러를 확인하고 수정 프롬프트를 이어서 요청하세요.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab4:
    st.subheader("GitHub 업로드 방법")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.code(
        """git init
git add .
git commit -m "feat: first student webapp"
git branch -M main
git remote add origin https://github.com/사용자명/저장소명.git
git push -u origin main""",
        language="bash",
    )
    st.markdown("- 수정 후에는 `git add . -> git commit -> git push`를 반복하면 됩니다.")
    st.markdown("- README에는 실행법, 기능 설명, 배포 링크를 꼭 적어두세요.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab5:
    st.subheader("Streamlit 배포 방법")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("1) [share.streamlit.io](https://share.streamlit.io/) 로그인")
    st.markdown("2) New app 클릭")
    st.markdown("3) Repository와 Branch(main) 선택")
    st.markdown("4) Main file path 설정 (`app.py` 또는 `webapp/app.py`)")
    st.markdown("5) Secrets에 아래 추가")
    st.code('GEMINI_API_KEY = "여기에_본인_API_키"', language="toml")
    st.markdown("6) Deploy 클릭")
    st.markdown("</div>", unsafe_allow_html=True)

    d1 = st.checkbox("requirements.txt 준비")
    d2 = st.checkbox("main file path 확인")
    d3 = st.checkbox("Secrets 입력")
    d4 = st.checkbox("배포 후 동작 테스트")
    done = sum([d1, d2, d3, d4])
    ratio = done / 4
    st.progress(ratio)
    st.caption(f"배포 준비도: {done}/4 ({int(ratio * 100)}%)")

with tab6:
    st.subheader("발표/공유 탭")
    st.markdown('<div class="tip">여기에 배포 링크를 제출하면 친구들이 같은 공간에서 바로 들어가볼 수 있어요.</div>', unsafe_allow_html=True)

    p1, p2 = st.columns(2)
    with p1:
        app_name = st.text_input("앱 이름", value=st.session_state.selected_idea.split("\n")[0] if st.session_state.selected_idea else "")
        one_line = st.text_input("한 줄 소개", value="학생 문제를 해결하는 AI 웹앱")
        feature_text = st.text_area(
            "핵심 기능(줄바꿈으로 입력)",
            value=st.session_state.selected_features.replace(", ", "\n") if st.session_state.selected_features else "",
            height=120,
        )
    with p2:
        github_url = st.text_input("GitHub 링크", value="")
        deploy_url = st.text_input("배포 링크", value="")
        challenge = st.text_area("어려웠던 점", value="", height=80)
        improvement = st.text_area("다음에 개선할 점", value="", height=80)

    features = [line.strip() for line in feature_text.splitlines() if line.strip()]
    report_md = build_presentation_markdown(
        app_name,
        one_line,
        features,
        github_url,
        deploy_url,
        challenge,
        improvement,
    )
    script_text = build_presentation_script(app_name, one_line, features, deploy_url)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 30초 발표 스크립트")
    st.code(script_text, language="text")
    st.download_button(
        "발표 스크립트 다운로드",
        data=script_text,
        file_name="presentation_script.txt",
        mime="text/plain",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 제출용 Markdown")
    st.code(report_md, language="markdown")
    st.download_button(
        "제출용 Markdown 다운로드",
        data=report_md,
        file_name="project_submission.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🌐 우리반 웹앱 공유 보드")

    with st.form("link_submit_form", clear_on_submit=True):
        student_name = st.text_input("이름/닉네임")
        shared_app_name = st.text_input("공유할 앱 이름")
        shared_url = st.text_input("배포 링크(URL)", placeholder="https://...")
        shared_memo = st.text_input("한 줄 소개", placeholder="예: 공부 루틴 도와주는 앱")
        submit_link = st.form_submit_button("공유 보드에 제출")

    if submit_link:
        if not student_name.strip() or not shared_app_name.strip() or not shared_url.strip():
            st.error("이름, 앱 이름, 배포 링크는 필수예요.")
        elif not is_valid_http_url(shared_url):
            st.error("링크는 http:// 또는 https:// 로 시작해야 해요.")
        else:
            try:
                add_shared_link(student_name, shared_app_name, shared_url, shared_memo)
                st.success("공유 보드에 등록 완료! 아래 목록에서 확인해 보세요.")
                st.toast("링크 제출 성공", icon="🎉")
            except Exception as exc:
                st.error(str(exc))

    links = load_shared_links()
    st.caption(f"총 {len(links)}개의 앱이 공유되어 있어요.")

    if links:
        for i, row in enumerate(links, start=1):
            st.markdown(f"**{i}. {row['app_name']}**")
            st.markdown(f"- 만든 사람: {row['student']}")
            if row.get("memo", "").strip():
                st.markdown(f"- 소개: {row['memo']}")
            st.markdown(f"- 배포 링크: [바로 들어가기]({row['url']})")
            st.caption(f"제출 시각: {row['submitted_at']}")
            st.markdown("---")
    else:
        st.info("아직 공유된 링크가 없습니다. 첫 번째로 등록해 보세요!")

    st.markdown("</div>", unsafe_allow_html=True)

st.caption(f"업데이트 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
