# ✨ 학생용 AI 웹앱 스타터

학생이 직접 웹앱을 만들고 배포할 수 있도록 만든 Streamlit 앱입니다.

## 주요 기능

- 웹앱 아이디어 추천
- 아이디어 선택 시 프롬프트 도우미로 자동 입력
- Gemini에 바로 붙여넣을 수 있는 고품질 프롬프트 3종 생성
  - HTML 코드 생성 프롬프트
  - Streamlit app.py 생성 프롬프트
  - HTML → app.py 변환 프롬프트
- GitHub 업로드 가이드
- Streamlit 배포 가이드
- Google Sheets 연동 링크 공유 보드
  - 학생 배포 링크 제출
  - 전체 학생 링크 모아보기

## 실행

```bash
git clone https://github.com/richee-pc/webapp.git
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## API 및 시트 연동 설정

`.streamlit/secrets.toml` 예시:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_KEY"
GOOGLE_SHEETS_SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"

[GOOGLE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

## 배포 시 메인 파일 경로

- `webapp/app.py`
