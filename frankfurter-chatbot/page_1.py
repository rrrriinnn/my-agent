import os
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import tool

from exchange_api import get_currencies, get_exchange_rate


# 기존 TavilySearch 대신 직접 만든 환율 조회 도구를 연결합니다.
@tool
def exchange_rate_tool(
    base_currency: str,
    target_currency: str,
    amount: float = 1.0,
    date: str = "latest",
) -> dict:
    """Frankfurter에서 환율과 환산 금액을 조회합니다.

    base_currency와 target_currency는 USD, KRW, JPY 같은 영문 통화 코드입니다.
    amount는 환산할 금액이며, date는 최신 조회 시 latest, 과거 조회 시 YYYY-MM-DD입니다.
    """
    try:
        return get_exchange_rate(base_currency, target_currency, amount, date)
    except ValueError as error:
        return {"error": str(error)}


@tool
def currency_list_tool() -> dict:
    """Frankfurter가 지원하는 통화 코드와 이름을 조회합니다."""
    try:
        return get_currencies()
    except ValueError as error:
        return {"error": str(error)}


if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("환율 조회 챗봇")
st.caption("예: 100달러는 원화로 얼마야? / 2025-01-02의 엔화 환율을 알려줘")
st.caption("Frankfurter에서 제공하는 일별 환율이며, 답변에 데이터 기준일을 표시합니다.")

if st.button("대화 초기화"):
    st.session_state.messages = []

api_key = os.getenv("OPENAI_API_KEY", "").strip()
if not api_key:
    st.info("챗봇을 사용하려면 .env 파일에 OPENAI_API_KEY를 입력해 주세요. 환율 계산기는 키 없이 이용할 수 있습니다.")

prompt = st.chat_input("조회할 환율이나 환산할 금액을 입력하세요", disabled=not api_key)
if prompt:
    try:
        # 기존 파일과 같은 모델 초기화 → 도구 연결 → agent.invoke 순서입니다.
        model = init_chat_model(
            os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
            model_provider="openai",
            timeout=45,
            max_retries=1,
        )
        today = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
        agent = create_agent(
            model,
            tools=[exchange_rate_tool, currency_list_tool],
            system_prompt=(
                f"당신은 한국어로 답변하는 환율 조회 도우미입니다. 오늘은 한국 기준 {today}입니다. "
                "환율과 환산 금액은 반드시 이번 질문에서 exchange_rate_tool을 호출해 확인하세요. "
                "이전 대화의 숫자나 기억으로 환율을 추측하지 마세요. 날짜 미지정 시 latest를 사용하세요. "
                "달러는 USD, 원화는 KRW, 엔화는 JPY, 유로는 EUR로 해석하세요. "
                "기준 또는 대상 통화가 빠지면 이전 대화를 참고하되 불명확하면 질문하세요. "
                "조회 결과의 기준 통화, 대상 통화, 1단위 환율, 환산 금액, 실제 데이터 기준일을 표시하세요. "
                "동일 통화 결과의 date가 null이면 환산 비율 1이며 조회가 불필요하다고 설명하세요. "
                "과거 조회에서 요청 날짜와 반환 날짜가 다르면 두 날짜를 모두 안내하세요. "
                "오류 결과는 원인을 안내하고, 성공한 환율처럼 답변하지 마세요. "
                "실시간 시세라고 표현하지 말고 은행의 실제 환전 금액은 수수료 등으로 다를 수 있다고 안내하세요. "
                "환율 관련 요청에 집중하고, 답변 끝에 출처 https://frankfurter.dev/ 를 표시하세요."
            ),
        )
        with st.spinner("환율을 확인하고 있습니다..."):
            response = agent.invoke(
                {"messages": st.session_state.messages + [{"role": "user", "content": prompt}]},
                config={"recursion_limit": 12},
            )
        answer = response["messages"][-1].content
        if isinstance(answer, list):
            answer = "\n".join(block.get("text", "") for block in answer if isinstance(block, dict))
        if not answer:
            raise ValueError("답변이 비어 있습니다.")
    except Exception:
        # 오류 원문에는 인증 정보가 포함될 수 있어 화면에 그대로 표시하지 않습니다.
        answer = "답변을 생성하지 못했습니다. .env의 API 키, 모델 이용 권한, API 사용 한도와 인터넷 연결을 확인한 뒤 다시 질문해 주세요."

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": answer})

# 기존 page_1.py와 동일하게 저장된 대화를 순회하며 출력합니다.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
