from pathlib import Path
import os
import re
import shutil
import sys
from unittest.mock import Mock, patch

import httpx
from dotenv import dotenv_values
from openai import AuthenticationError, RateLimitError, APIConnectionError, APIStatusError
from streamlit.testing.v1 import AppTest

QA = Path(__file__).resolve().parent
STAGE = QA / "fix-chat-config"
PROJECT = Path(r"C:\Users\Administrator\Desktop\My-Agent2")
sys.path.insert(0, str(STAGE))


def app_check():
    app = AppTest.from_file(str(STAGE / "app.py")).run(timeout=30)
    assert not app.exception, [item.message for item in app.exception]
    return app


def verify_local():
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        app = app_check()
        assert app.chat_input[0].disabled
    cases = [
        (AuthenticationError("do not reveal secret-token", response=httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")), body=None), "401"),
        (RateLimitError("do not reveal secret-token", response=httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")), body={"code": "insufficient_quota"}), "잔액"),
        (APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")), "연결"),
        (RuntimeError("do not reveal secret-token"), "RuntimeError"),
    ]
    for error, expected in cases:
        fake = Mock()
        fake.invoke.side_effect = error
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-placeholder"}), patch("langchain.chat_models.init_chat_model"), patch("langchain.agents.create_agent", return_value=fake):
            app = app_check()
            app.chat_input[0].set_value("100 USD to KRW").run(timeout=30)
            assert not app.exception
            answer = app.session_state["messages"][-1]["content"]
            assert expected in answer, type(error).__name__
            assert "secret-token" not in answer
    print("PASS: missing-key detection, authentication/quota/network errors, and secret redaction")


def verify_live_and_apply():
    values = dotenv_values(PROJECT / ".env", encoding="utf-8-sig")
    aliases = [name for name in values if re.fullmatch(r"open(?:ai)?_api_key", name, re.IGNORECASE)]
    key = values.get("OPENAI_API_KEY") or next((values[name] for name in aliases if values[name]), None)
    assert key, "No local key is configured."
    os.environ["OPENAI_API_KEY"] = key
    app = app_check()
    app.chat_input[0].set_value("100달러를 원화로 바꿔줘. 도구로 조회하고 데이터 기준일도 알려줘.").run(timeout=150)
    assert not app.exception, [item.message for item in app.exception]
    answer = app.session_state["messages"][-1]["content"]
    successful = "frankfurter" in answer.lower() and "기준" in answer
    if successful:
        print("PASS: live chat returned a Frankfurter exchange-rate answer with a reference date")
    else:
        # The UI contains only classified errors, never raw provider exceptions or keys.
        print("Live result:", answer.encode("ascii", errors="backslashreplace").decode("ascii"))

    current = (PROJECT / "page_1.py").read_text(encoding="utf-8-sig")
    before = (STAGE / "page_1.before.py").read_text(encoding="utf-8-sig")
    assert current == before, "page_1.py changed during verification; refusing to overwrite."
    env_path = PROJECT / ".env"
    env_text = env_path.read_text(encoding="utf-8-sig")
    latest = dotenv_values(env_path, encoding="utf-8-sig")
    latest_keys = [value for name, value in latest.items() if re.fullmatch(r"open(?:ai)?_api_key", name, re.IGNORECASE)]
    assert key in latest_keys, "The credential changed during verification; refusing to overwrite."
    # Rename the setting only; preserve the exact credential and the user's other settings.
    if not values.get("OPENAI_API_KEY"):
        env_text, replacements = re.subn(r"(?im)^(\s*)(?:export\s+)?open(?:ai)?_api_key(\s*=)", r"\1OPENAI_API_KEY\2", env_text)
        assert replacements == 1
    old_page = PROJECT / "page_1.py"
    shutil.copyfile(old_page, QA / "my-agent2-page_1.backup.py")
    env_path.write_text(env_text, encoding="utf-8")
    shutil.copyfile(STAGE / "page_1.py", old_page)
    assert dotenv_values(env_path).get("OPENAI_API_KEY") == key
    assert (PROJECT / "page_1.py").read_bytes() == (STAGE / "page_1.py").read_bytes()
    print("APPLIED: corrected .env variable name and page_1.py key loading/error handling")
    print("API credential contents were preserved and never printed.")
    if not successful:
        raise SystemExit(2)


if __name__ == "__main__":
    if "--live-and-apply" in sys.argv:
        verify_live_and_apply()
    else:
        verify_local()
