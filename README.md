# 🚀 AI 웹앱 수업 메이커 (Gemini + GitHub + Streamlit)

학생들이 **각자 원하는 주제**로 웹앱을 만들 수 있도록, 선생님이 4차시를 자유롭고 흥미롭게 운영할 수 있게 도와주는 앱입니다.

- 4차시 수업 운영안 자동 생성
- 학생 프로젝트 아이디어 자동 생성
- GitHub/Streamlit 배포 체크리스트 제공

---

## 1) 이 앱이 해결하는 문제

수업 전에 가장 어려운 부분은 아래 3가지입니다.

1. 주제가 제각각인 학생들을 한 흐름으로 운영하기
2. Gemini 연동 + GitHub + 배포까지 4차시에 맞추기
3. 흥미 요소(게임화, 미션, 발표)를 자연스럽게 넣기

이 앱은 위 과정을 클릭 몇 번으로 설계할 수 있게 만듭니다.

---

## 2) 주요 기능

### 🧭 4차시 수업 설계
- 테마/난이도/학생 수/차시 시간 입력
- 1~4차시 목표, 활동, 산출물, 흥미 요소 자동 생성
- Markdown 파일로 운영안 다운로드

### 💡 학생 아이디어 생성
- 키워드 입력 시 학생 프로젝트 아이디어 여러 개 생성
- 각 아이디어마다 핵심 기능 3개 + UI 포인트 3개 제안
- GitHub 미션과 배포 팁 함께 제공

### ✅ GitHub/배포 트래커
- GitHub 실습 체크리스트
- Streamlit Community Cloud 배포 체크리스트
- 전체 진행률 시각화

---

## 3) 실행 방법

### 3-1. 저장소 클론

```bash
git clone https://github.com/richee-pc/webapp.git
cd webapp
```

### 3-2. 가상환경 생성 및 활성화

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3-3. 패키지 설치

```bash
pip install -r webapp/requirements.txt
```

### 3-4. 실행

```bash
streamlit run webapp/app.py
```

---

## 4) Gemini API 키 설정

앱은 아래 우선순위로 API 키를 사용합니다.

1. `st.secrets["GEMINI_API_KEY"]` (권장)
2. 사이드바 직접 입력

### 로컬 secrets 설정

프로젝트 루트에 `.streamlit/secrets.toml` 생성:

```toml
GEMINI_API_KEY = "여기에_본인_API_키"
```

---

## 5) 4차시 운영 예시

### 1차시: 환경 설정 + 기본 UI
- Streamlit 기본 구조 만들기
- 학생별 주제 선택

### 2차시: Gemini API 연동
- 입력 폼 + 프롬프트 + 출력 파싱
- 예외 처리 실습

### 3차시: GitHub 협업
- 커밋/푸시/README 작성
- 기능 고도화

### 4차시: Streamlit 배포 + 발표
- Cloud 배포
- URL 공유 및 데모 발표

---

## 6) Streamlit Community Cloud 배포

1. [Streamlit Community Cloud](https://share.streamlit.io/) 접속
2. Repository: `richee-pc/webapp`
3. Branch: `main`
4. Main file path: `webapp/app.py`
5. Secrets 등록:

```toml
GEMINI_API_KEY = "여기에_본인_API_키"
```

6. Deploy

---

## 7) 확장 아이디어

- 학생 발표 점수표 자동 생성
- 팀별 작업 보드(역할/진행 상황)
- 우수작 자동 하이라이트 갤러리
- 수업 종료 후 회고 리포트 자동 생성
