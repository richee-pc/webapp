# 🌟 우리반 웹앱 공유 보드

학생들이 만든 Streamlit 웹앱 링크를 한곳에 모아서 공유하는 앱입니다.

## 기능

- 제출 탭에서 아래 4가지만 입력 후 제출
  - 이름
  - 웹앱 제목
  - 한 줄 설명
  - 스트림릿 링크
- 제출 내용은 Google Sheets에 저장
- 친구들 링크 접속 탭에서 카드 형태로 보기 + 바로 접속 버튼

## 실행

```bash
git clone https://github.com/richee-pc/webapp.git
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## Streamlit Secrets 설정

```toml
GOOGLE_SHEETS_SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"

[GOOGLE_SERVICE_ACCOUNT]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "...@....iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

## 배포 시 메인 파일 경로

- `webapp/app.py`
