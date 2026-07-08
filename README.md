# 🎬 MoodFlix AI - 감정 기반 영화 추천 웹앱

Gemini API + Streamlit으로 만드는 감정 기반 영화 추천 프로젝트입니다.  
입문자도 따라할 수 있도록 **설치 → 실행 → GitHub 관리 → 배포**까지 한 번에 정리했습니다.

---

## 1) 프로젝트 소개

- **앱 이름**: MoodFlix AI
- **핵심 기능**
  - 오늘의 기분/장르/시청 시간 기반 맞춤 영화 추천
  - Gemini가 추천 이유와 감정 매칭 점수 생성
  - 추천 결과 찜 목록 저장
- **대상**: Python/Streamlit 입문자, 수업 프로젝트 제작 학생

---

## 2) 폴더 구조

```text
webapp/
├── app.py
├── requirements.txt
└── .gitignore
```

> 현재 저장소 루트 기준으로 앱 코드는 `webapp/app.py`에 있습니다.

---

## 3) 로컬 실행 방법

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

### 3-4. 앱 실행

```bash
streamlit run webapp/app.py
```

브라우저가 자동으로 열리지 않으면 터미널에 출력된 로컬 주소를 직접 접속하세요.

---

## 4) Gemini API 키 설정

앱은 아래 우선순위로 API 키를 읽습니다.

1. `st.secrets["GEMINI_API_KEY"]` (권장)
2. 앱 사이드바에 직접 입력

### 4-1. 로컬 Secrets 설정 (권장)

프로젝트 루트에 `.streamlit/secrets.toml` 파일 생성:

```toml
GEMINI_API_KEY = "여기에_본인_API_키"
```

> `.streamlit/secrets.toml`은 `.gitignore`에 포함되어 있어 GitHub에 올라가지 않습니다.

---

## 5) 수업용 4차시 로드맵

### ✅ 1차시: 환경 설정 + UI 익히기

- 가상환경 생성/패키지 설치
- Streamlit 기본 구조 이해 (사이드바, 컬럼, 탭, 폼)
- 앱 실행 확인

### ✅ 2차시: Gemini API 연동 + 프롬프트 튜닝

- API 키 발급 및 Secrets 연결
- 프롬프트 수정 실습 (추천 개수, 말투, 설명 방식)
- 예외 처리 확인 (키 누락, 파싱 실패)

### ✅ 3차시: GitHub 버전 관리

- 변경 사항 커밋/푸시
- 커밋 메시지 규칙 연습 (`feat`, `fix`, `docs`)
- README 업데이트 및 협업 준비

### ✅ 4차시: Streamlit Community Cloud 배포

- GitHub 저장소 연결
- 메인 파일 경로: `webapp/app.py`
- Secrets에 `GEMINI_API_KEY` 등록
- 배포 링크 생성 및 공유

---

## 6) Streamlit Community Cloud 배포 순서

1. [Streamlit Community Cloud](https://share.streamlit.io/) 로그인
2. **New app** 클릭
3. Repository: `richee-pc/webapp` 선택
4. Branch: `main`
5. Main file path: `webapp/app.py`
6. Advanced settings > Secrets에 아래 추가:

```toml
GEMINI_API_KEY = "여기에_본인_API_키"
```

7. Deploy 클릭

---

## 7) 트러블슈팅

- **API 키 오류**: 키 앞뒤 공백 제거, Secrets 저장 후 재배포
- **모듈 오류**: 가상환경 활성화 상태에서 `pip install -r webapp/requirements.txt`
- **배포 실패**: Main file path가 `webapp/app.py`인지 확인
- **응답 파싱 실패**: 앱에서 다시 요청하거나 추천 조건을 단순화

---

## 8) 확장 아이디어

- 영화 포스터 이미지 자동 표시
- 추천 결과 CSV 다운로드 기능
- 사용자 닉네임/테마 컬러 설정
- 명대사 카드 공유 이미지 생성

---

## 9) 라이선스

학습/수업용으로 자유롭게 사용 가능합니다.
