import streamlit as st

page_1 = st.Page("page_1.py", title="환율 챗봇", icon="💱")
page_2 = st.Page("page_2.py", title="환율 계산기")
page_3 = st.Page("page_3.py", title="사용 안내")

pages = st.navigation([page_1, page_2, page_3], position="top")

pages.run()