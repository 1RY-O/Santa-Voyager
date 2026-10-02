import json
from ai_provider import DemoProvider, extract_json
from models import GiftOutput, HangoutOutput


def test_extract_raw_json():
    assert extract_json('{"a": 1}') == {"a": 1}


def test_extract_fenced_json():
    assert extract_json('Here:\n```json\n{"title": "x"}\n```') == {"title": "x"}


def test_extract_malformed_raises():
    try:
        extract_json("no json here")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_demo_gift_schema_valid():
    p = DemoProvider()
    data = p.parse_json(p.generate("gift idea", "gift please"))
    g = GiftOutput(**data)
    assert g.title and "$" in g.estimated_price


def test_demo_hangout_schema_valid():
    p = DemoProvider()
    data = p.parse_json(p.generate("hangout plan", "hangout please"))
    h = HangoutOutput(**data)
    assert isinstance(h.assumptions, list) and len(h.activities) == 4
    json.dumps(data)  # must stay JSON-serializable
