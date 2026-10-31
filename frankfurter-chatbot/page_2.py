from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import streamlit as st

from exchange_api import get_currencies, get_exchange_rate

st.title("환율 계산기")
st.caption("통화와 금액을 선택해서 바로 계산할 수 있습니다. OpenAI API 키는 필요하지 않습니다.")


@st.cache_data(ttl=3600, show_spinner=False)
def load_currencies():
    return get_currencies()


try:
    currencies = load_currencies()
except ValueError as error:
    st.error(str(error))
    st.stop()

codes = sorted(currencies)
with st.form("exchange_form"):
    base = st.selectbox("기준 통화", codes, index=codes.index("USD"), format_func=lambda code: f"{code} - {currencies[code]}")
    target = st.selectbox("대상 통화", codes, index=codes.index("KRW"), format_func=lambda code: f"{code} - {currencies[code]}")
    amount = st.number_input("환산할 금액", min_value=0.0, max_value=1e15, value=100.0, step=1.0)
    historical = st.checkbox("과거 날짜로 조회")
    selected_date = st.date_input(
        "조회 날짜 (과거 날짜로 조회할 때만 적용)",
        value=datetime.now(ZoneInfo("Asia/Seoul")).date(),
        min_value=date(1948, 1, 1),
        max_value=datetime.now(ZoneInfo("Asia/Seoul")).date(),
    )
    submitted = st.form_submit_button("환율 조회")

if submitted:
    try:
        with st.spinner("환율을 조회하고 있습니다..."):
            result = get_exchange_rate(base, target, amount, selected_date.isoformat() if historical else "latest")
        converted = Decimal(result["converted_amount"])
        st.metric(f"{amount:,.2f} {base} 환산 결과", f"{converted:,.2f} {target}")
        st.write(f"1 {base} = {Decimal(result['rate']):,.6f} {target}")
        if result["date"]:
            st.write(f"데이터 기준일: {result['date']}")
            if historical and result["date"] != selected_date.isoformat():
                st.info(f"요청일 {selected_date.isoformat()} 대신 API가 반환한 {result['date']} 기준입니다.")
        else:
            st.info(result["source"])
        st.caption("출처: https://frankfurter.dev/ · 실제 환전 금액은 은행 수수료 등에 따라 달라질 수 있습니다.")
    except ValueError as error:
        st.error(str(error))
