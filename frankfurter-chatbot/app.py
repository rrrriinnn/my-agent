from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

st.set_page_config(page_title="환율 조회 챗봇", page_icon="💱")

# 기존 app.py와 동일하게 3개 페이지를 상단 메뉴로 연결합니다.
page_1 = st.Page("page_1.py", title="환율 챗봇", icon="💱")
page_2 = st.Page("page_2.py", title="환율 계산기")
page_3 = st.Page("page_3.py", title="사용 안내")

pages = st.navigation([page_1, page_2, page_3], position="top")

pages.run()
