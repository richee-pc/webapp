# 🧠 학생용 AI 웹앱 메이커

Gemini + GitHub + Streamlit을 활용해 학생들이 원하는 웹앱을 직접 만들고 배포할 수 있도록 돕는 수업용 앱입니다.

## 포함 기능

- 웹앱 아이디어 추천 기능
- 학생 아이디어를 실제 코드로 바꾸는 프롬프트 생성 기능
- Gemini/GitHub/Streamlit 전체 제작 과정 설명 탭 (가장 먼저 배치)
- Gemini로 HTML 코드 + app.py 코드 생성 프롬프트 작성법
- GitHub 업로드 방법 가이드
- Streamlit Community Cloud 배포 방법 가이드

## 실행 방법

```bash
git clone https://github.com/richee-pc/webapp.git
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## API 키 설정

`.streamlit/secrets.toml` 예시:

```toml
GEMINI_API_KEY = "여기에_본인_API_키"
```

## 배포 시 메인 파일 경로

`webapp/app.py`
