import streamlit as st

st.title("사용 안내")

st.subheader("환율 챗봇")
st.write("평소 말하듯 질문하면 챗봇이 Frankfurter API를 호출해서 환율을 알려줍니다.")
st.markdown("""
- 미국 달러를 원화로 환산할 때 1달러는 얼마야?
- 100달러를 원화로 바꿔줘.
- 그럼 200달러는? (이전 대화를 이어서 질문할 수 있습니다.)
- 2025-01-02 기준 100유로는 원화로 얼마였어?
- 지원하는 통화 목록을 알려줘.
""")

st.subheader("환율 계산기")
st.write("기준 통화, 대상 통화, 금액을 선택하고 '환율 조회'를 누르세요. 과거 날짜 조회도 가능합니다.")

st.subheader("API 안내")
st.write("Frankfurter API는 별도 API 키 없이 사용할 수 있습니다. 챗봇의 자연어 답변에는 .env의 OPENAI_API_KEY를 사용합니다.")
st.write("환율은 일별 데이터입니다. 통화와 날짜에 따라 제공 여부 및 실제 데이터 기준일이 다를 수 있습니다.")
st.write("은행 환전 수수료는 계산에 포함되지 않습니다.")
st.link_button("Frankfurter API 공식 문서", "https://frankfurter.dev/")
