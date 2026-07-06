"""
tests/test_chatbot.py
----------------------
Unit tests for the chatbot NLP engine.

Run with:
    pytest -v
"""

import json
import sys
from pathlib import Path

import pytest

# Make the project root importable when running `pytest` from anywhere.
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.chatbot import Chatbot  # noqa: E402

INTENTS_PATH = ROOT_DIR / "intents.json"


@pytest.fixture(scope="module")
def bot() -> Chatbot:
    return Chatbot(str(INTENTS_PATH))


# ---------------------------------------------------------------- #
# Knowledge base integrity
# ---------------------------------------------------------------- #
def test_intents_file_exists():
    assert INTENTS_PATH.exists(), "intents.json must exist at project root"


def test_intents_file_is_valid_json():
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "intents" in data
    assert isinstance(data["intents"], list)
    assert len(data["intents"]) > 0


def test_every_intent_has_required_fields():
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for intent in data["intents"]:
        assert "tag" in intent
        assert "responses" in intent
        assert isinstance(intent["responses"], list)
        assert len(intent["responses"]) > 0


def test_fallback_intent_exists():
    with open(INTENTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    tags = [intent["tag"] for intent in data["intents"]]
    assert (
        "fallback" in tags
    ), "A 'fallback' intent is required for graceful degradation"


# ---------------------------------------------------------------- #
# Chatbot initialization
# ---------------------------------------------------------------- #
def test_chatbot_initializes_successfully(bot: Chatbot):
    assert bot is not None
    assert len(bot.patterns) > 0
    assert len(bot.responses_by_tag) > 0


def test_chatbot_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        Chatbot("this_file_does_not_exist.json")


# ---------------------------------------------------------------- #
# Response behaviour — checked against the matched INTENT TAG rather
# than substring keywords in the (randomly chosen) response text, so
# these tests stay reliable regardless of which response is sampled.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "user_input,expected_tag",
    [
        ("hi there", "greeting"),
        ("where is my order", "order_status"),
        ("i want to cancel my order", "cancel_order"),
        ("when will i get my refund", "refund_policy"),
        ("my payment failed", "payment_issue"),
        ("thanks a lot", "thanks"),
        ("bye bye", "goodbye"),
        ("i want to return this product", "return_policy"),
        ("connect me to a human agent", "contact_human"),
    ],
)
def test_relevant_queries_match_expected_intent(bot: Chatbot, user_input, expected_tag):
    matched_tag = bot.get_intent_tag(user_input)
    assert (
        matched_tag == expected_tag
    ), f"Expected intent {expected_tag!r} for {user_input!r}, got {matched_tag!r}"


def test_gibberish_input_triggers_fallback(bot: Chatbot):
    matched_tag = bot.get_intent_tag("asdkfjaskdjf zzxxqq random nonsense")
    assert matched_tag == "fallback"


def test_empty_input_does_not_crash(bot: Chatbot):
    response = bot.get_response("")
    assert isinstance(response, str)
    assert len(response) > 0


def test_whitespace_only_input_does_not_crash(bot: Chatbot):
    response = bot.get_response("     ")
    assert isinstance(response, str)
    assert len(response) > 0


def test_none_like_input_does_not_crash(bot: Chatbot):
    # Simulates defensive handling if a caller ever passes a non-string-like value.
    response = bot.get_response(None)  # type: ignore[arg-type]
    assert isinstance(response, str)
    assert len(response) > 0


def test_response_is_always_a_non_empty_string(bot: Chatbot):
    for query in ["hello", "refund please", "xyzabc123", "shipping cost", ""]:
        response = bot.get_response(query)
        assert isinstance(response, str)
        assert response.strip() != ""
