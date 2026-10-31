import os
from pathlib import Path
import sys
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "frankfurter-chatbot"
sys.path.insert(0, str(PROJECT))

import requests
from dotenv import load_dotenv
from streamlit.testing.v1 import AppTest
from exchange_api import get_exchange_rate


def assert_no_error(app):
    assert not app.exception, [item.message for item in app.exception]


def check_local():
    # 金額とエラー処理を、実際のAPIと同じ形式の応答で確認します。
    with patch("exchange_api.request_api", return_value={"rate": 1336.41, "date": "2026-10-30"}):
        data = get_exchange_rate(" usd ", "krw", 100, "2025-01-02")
        assert data["converted_amount"] == "133641.00"
        assert data["date"] == "2026-10-30"
        assert data["requested_date"] == "2025-01-02"
        assert get_exchange_rate("USD", "KRW", 0)["converted_amount"] == "0.00"
    for amount in [-1, float("nan"), float("inf")]:
        try:
            get_exchange_rate("USD", "KRW", amount)
            raise AssertionError("Invalid amount accepted")
        except ValueError:
            pass
    for day in ["2030-01-01", "bad-date"]:
        try:
            get_exchange_rate("USD", "KRW", date=day)
            raise AssertionError("Invalid date accepted")
        except ValueError:
            pass
    with patch("exchange_api.requests.get", side_effect=requests.Timeout):
        try:
            get_exchange_rate("USD", "KRW")
            raise AssertionError("Timeout not handled")
        except ValueError:
            pass
    with patch("exchange_api.get_currencies", return_value={"USD": "Dollar"}):
        same = get_exchange_rate("USD", "USD", 100)
        assert same["converted_amount"] == "100" and same["date"] is None
        try:
            get_exchange_rate("ZZZ", "ZZZ")
            raise AssertionError("Unsupported same currency accepted")
        except ValueError:
            pass

    # Missing-key, chat-history, follow-up context and reset behavior.
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        app = AppTest.from_file(str(PROJECT / "app.py")).run(timeout=30)
        assert_no_error(app)
        assert app.chat_input[0].disabled
    with patch.dict(os.environ, {"OPENAI_API_KEY": "local-test-key"}):
        fake_agent = Mock()
        fake_agent.invoke.return_value = {"messages": [Mock(content="100 USD = 133641 KRW")]}
        with patch("langchain.chat_models.init_chat_model"), patch("langchain.agents.create_agent", return_value=fake_agent):
            app = AppTest.from_file(str(PROJECT / "app.py")).run(timeout=30)
            app.chat_input[0].set_value("100 USD to KRW").run(timeout=30)
            assert_no_error(app)
            assert len(app.chat_message) == 2
            app.chat_input[0].set_value("Then 200?").run(timeout=30)
            assert_no_error(app)
            assert len(fake_agent.invoke.call_args.args[0]["messages"]) == 3
            assert len(app.chat_message) == 4
            app.button[0].click().run(timeout=30)
            assert len(app.chat_message) == 0

    # Calculator can run and display results with no model calls.
    with patch("exchange_api.get_currencies", return_value={"USD": "Dollar", "KRW": "Won"}), patch("exchange_api.request_api", return_value={"rate": 1336.41, "date": "2026-10-30"}):
        calculator = AppTest.from_file(str(PROJECT / "page_2.py")).run(timeout=30)
        assert_no_error(calculator)
        calculator.button[0].click().run(timeout=30)
        assert_no_error(calculator)
        assert calculator.metric[0].value == "133,641.00 KRW"
    guide = AppTest.from_file(str(PROJECT / "page_3.py")).run(timeout=30)
    assert_no_error(guide)
    print("PASS: validation, timeout, same-currency, three-page UI, conversation context, reset and calculator")


def check_live():
    load_dotenv(PROJECT / ".env", override=True)
    data = get_exchange_rate("USD", "KRW", 100)
    assert float(data["rate"]) > 0
    past = get_exchange_rate("EUR", "KRW", 100, "2025-01-02")
    assert past["date"] <= "2025-01-02"
    print("PASS: live Frankfurter latest and historical lookup")

    # Exercise the full UI -> LangChain tool -> Frankfurter -> model reply path.
    app = AppTest.from_file(str(PROJECT / "app.py")).run(timeout=30)
    assert_no_error(app)
    app.chat_input[0].set_value("100 USD를 KRW로 환산해줘. 반드시 도구를 사용하고 데이터 기준일도 알려줘.").run(timeout=150)
    assert_no_error(app)
    answer = app.session_state["messages"][-1]["content"]
    assert "답변을 생성하지 못했습니다" not in answer, "Model call failed; check local key/model permissions."
    assert "frankfurter" in answer.lower(), "Missing API attribution"
    assert data["date"] in answer, "Missing actual rate date"
    print("PASS: live chat invoked the model and returned API-sourced exchange answer")
    print(answer)


if __name__ == "__main__":
    if "--live" in sys.argv:
        check_live()
    else:
        check_local()
