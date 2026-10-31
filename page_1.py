import streamlit as st  
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langchain.agents import create_agent

model = init_chat_model("gpt-5.4-mini")

tavily_tool = TavilySearch(
    max_results=5,
    topic="general",
)

agent = create_agent(model, tools=[tavily_tool])

if "messages" not in st.session_state :
    st.session_state.messages = []

st.title("우리 회사 챗봇")

prompt = st.chat_input("여기에 입력하시오")
if prompt:
    response = agent.invoke(
    {"messages": [{"role": "user", "content": prompt}]}
    )
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    st.session_state.messages.append({'role': 'ai', 'content': response['messages'][-1].content})
        
    # with st.chat_message("ai"):
        # st.write("반갑습니다.")
    # st.write(f"User has sent the following prompt: {prompt}")
    # st.write(prompt) -> 위에 로그? 같은 거 없이 그냥 유저가 쓴 말만 나옴
for message in st.session_state.messages :
    with st.chat_message(message['role']):
        st.write(message['content'])