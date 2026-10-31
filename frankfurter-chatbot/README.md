# Streamlit 환율 조회 챗봇

기존 프로젝트의 `app.py → st.Page 3개 → st.navigation → pages.run()` 구성을 유지했습니다.
`page_1.py`도 `init_chat_model → create_agent → st.chat_input → agent.invoke → session_state → st.chat_message` 순서로 작성했습니다.
기존 Tavily 검색 도구만 Frankfurter 환율 조회 도구로 교체했습니다.

## 파일 구성

- `app.py`: 환경 변수 로딩 및 상단 페이지 메뉴
- `page_1.py`: 자연어 환율 챗봇, 대화 기록 및 초기화
- `page_2.py`: 최신/과거 환율 계산기 (OpenAI 키 없이 사용 가능)
- `page_3.py`: 사용 안내
- `exchange_api.py`: 두 페이지에서 함께 사용하는 Frankfurter API 호출 및 금액 계산
- `.env`: 로컬 OpenAI API 키 설정
- `.env.example`: API 키가 없는 설정 예시
- `requirements.txt`, `.gitignore`: 의존성 및 비공개 파일 제외 설정

## 실행 방법 (PowerShell)

이 폴더에서 터미널을 열고 실행합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

이미 설치된 원본 프로젝트의 가상환경으로 실행할 수도 있습니다.

```powershell
& "C:\Users\Administrator\Desktop\my-agent\.venv\Scripts\python.exe" -m streamlit run "C:\Users\Administrator\Desktop\frankfurter-chatbot\app.py"
```

브라우저에서 `http://localhost:8501`을 엽니다. 다른 Streamlit 앱이 실행 중이면 터미널에 표시된 주소를 사용하세요.

챗봇 사용 전 `.env`의 `OPENAI_API_KEY`에 본인의 키가 있는지 확인하세요.
`OPENAI_MODEL` 기본값은 원본 코드와 같은 `gpt-5.4-mini`입니다.
Frankfurter에는 별도 키가 필요 없으며 `TAVILY_API_KEY`도 필요 없습니다.
`.env`는 공유하거나 Git에 올리지 마세요.

## 질문 예시

- "100달러는 원화로 얼마야?"
- "그럼 200달러는?"
- "2025-01-02의 100유로를 원화로 바꿔줘."
- "10000엔은 원화로 얼마야?"

## 데이터

[Frankfurter 공식 문서](https://frankfurter.dev/)의 v2 API를 사용합니다.

- 통화 목록: `GET https://api.frankfurter.dev/v2/currencies`
- 환율 조회: `GET https://api.frankfurter.dev/v2/rate/USD/KRW`
- 과거 조회: 같은 URL에 `?date=2025-01-02` 추가
- 금액 계산: API가 반환한 환율에 입력 금액을 곱합니다.

환율은 일별 데이터이며 화면과 답변에 실제 데이터 기준일을 표시합니다.
요청일과 API 반환일이 다르면 두 날짜를 모두 안내합니다.
은행별 실제 환전 수수료는 포함하지 않습니다.
