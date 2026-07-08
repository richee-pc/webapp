from datetime import datetime
from typing import Dict, List

import gspread
import streamlit as st


st.set_page_config(
    page_title="우리반 웹앱 공유 보드",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
.main-title { font-size: 2.0rem; font-weight: 800; margin-bottom: 0.2rem; }
.sub-title { color: #6b7280; margin-bottom: 1rem; }
.card {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 1rem;
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    margin-bottom: 0.8rem;
}
.meta { color: #6b7280; font-size: 0.9rem; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def get_worksheet() -> gspread.Worksheet:
    spreadsheet_id = st.secrets["GOOGLE_SHEETS_SPREADSHEET_ID"]
    service_account_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])

    client = gspread.service_account_from_dict(service_account_info)
    spreadsheet = client.open_by_key(spreadsheet_id)

    try:
        ws = spreadsheet.worksheet("shared_links")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title="shared_links", rows=500, cols=8)
        ws.append_row(["name", "title", "description", "url", "submitted_at"])

    return ws


def load_links() -> List[Dict[str, str]]:
    ws = get_worksheet()
    records = ws.get_all_records()

    rows: List[Dict[str, str]] = []
    for row in records:
        rows.append(
            {
                "name": str(row.get("name", "")),
                "title": str(row.get("title", "")),
                "description": str(row.get("description", "")),
                "url": str(row.get("url", "")),
                "submitted_at": str(row.get("submitted_at", "")),
            }
        )

    rows.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    return rows


def submit_link(name: str, title: str, description: str, url: str) -> None:
    ws = get_worksheet()
    current = ws.get_all_records()

    clean_url = url.strip()
    if not (clean_url.startswith("http://") or clean_url.startswith("https://")):
        raise ValueError("링크는 http:// 또는 https:// 로 시작해야 해요.")

    duplicate = any(str(item.get("url", "")).strip() == clean_url for item in current)
    if duplicate:
        raise ValueError("이미 제출된 링크예요. 다른 링크를 입력해 주세요.")

    ws.append_row(
        [
            name.strip(),
            title.strip(),
            description.strip(),
            clean_url,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]
    )


st.markdown('<div class="main-title">🌟 우리반 웹앱 공유 보드</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">이름, 제목, 한 줄 설명, 스트림릿 링크만 제출하면 친구들이 바로 접속할 수 있어요.</div>',
    unsafe_allow_html=True,
)

submit_tab, gallery_tab = st.tabs(["제출하기", "친구들 링크 접속하기"])

with submit_tab:
    st.subheader("내 웹앱 제출")

    with st.form("submit_form", clear_on_submit=True):
        name = st.text_input("이름")
        title = st.text_input("웹앱 제목")
        description = st.text_input("관련 한 줄 설명")
        url = st.text_input("스트림릿 링크", placeholder="https://...streamlit.app")

        submitted = st.form_submit_button("제출")

    if submitted:
        if not name.strip() or not title.strip() or not description.strip() or not url.strip():
            st.error("모든 항목을 입력해 주세요.")
        else:
            try:
                submit_link(name, title, description, url)
                st.success("제출 완료! 이제 친구들이 링크를 눌러 들어갈 수 있어요 🎉")
            except Exception as exc:
                st.error(str(exc))

with gallery_tab:
    st.subheader("친구들이 만든 웹앱")

    try:
        links = load_links()
    except Exception as exc:
        links = []
        st.error("Google Sheets 연결에 실패했어요. Secrets 설정을 확인해 주세요.")
        st.caption(f"오류: {exc}")

    st.caption(f"총 {len(links)}개 작품")

    if not links:
        st.info("아직 제출된 작품이 없어요. 첫 작품을 제출해 보세요!")
    else:
        for idx, item in enumerate(links, start=1):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"### {idx}. {item['title']}")
                st.markdown(f"- 👤 제출자: **{item['name']}**")
                st.markdown(f"- 📝 한 줄 설명: {item['description']}")
                st.markdown(f"<div class='meta'>제출 시각: {item['submitted_at']}</div>", unsafe_allow_html=True)
            with c2:
                st.link_button("바로 접속", item["url"], use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
