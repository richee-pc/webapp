# ✨ 학생용 AI 웹앱 메이커

핵심 기능 전체를 포함한 학생용 수업 웹앱입니다.

## 포함 기능

- 제작 과정 설명 탭
- 웹앱 아이디어 추천
- 아이디어 클릭 시 프롬프트 도우미 자동 입력
- 고품질 프롬프트 3종 생성 (HTML / app.py / 변환)
- GitHub 업로드 방법
- Streamlit 배포 방법
- 친구들 링크 접속하기 탭
  - 이름/제목/한 줄 설명/스트림릿 링크 제출
  - 카드 형태로 목록 표시 + 바로 접속 버튼

## 공유 탭 저장 방식

- 기본: **설정 없이 즉시 동작** (앱 내부 로컬 파일 저장)
- 선택: Google Sheets secrets가 있으면 자동으로 시트 저장

## 실행

```bash
git clone https://github.com/richee-pc/webapp.git
cd webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r webapp/requirements.txt
streamlit run webapp/app.py
```

## 배포 경로

- `webapp/app.py`
