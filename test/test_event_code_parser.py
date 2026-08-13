# test/test_event_code_parser.py — nuevo
from app.services.event_code_parser import parse_event_code

def test_parses_freestyle():
    assert parse_event_code("200L") == (200, "FREE")

def test_parses_backstroke():
    assert parse_event_code("50E") == (50, "BACK")

def test_invalid_code_raises():
    import pytest
    from app.services.event_code_parser import EventCodeParseError
    with pytest.raises(EventCodeParseError):
        parse_event_code("XYZ")