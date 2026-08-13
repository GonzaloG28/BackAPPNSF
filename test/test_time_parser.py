# test/test_time_parser.py
from app.services.time_parser import parse_time_to_seconds, TimeParseError
import pytest


def test_simple_seconds_dot():
    assert parse_time_to_seconds("20.01") == 20.01

def test_simple_seconds_comma():
    assert parse_time_to_seconds("20,01") == 20.01

def test_minutes_seconds_standard():
    assert parse_time_to_seconds("1:02.45") == 62.45

def test_apostrophe_comma():
    assert parse_time_to_seconds("1'10,10") == 70.10

def test_apostrophe_dot():
    assert parse_time_to_seconds("1'10.10") == 70.10

def test_doublequote_dot():
    assert parse_time_to_seconds('1"10.01') == 70.01

def test_invalid_format_raises():
    with pytest.raises(TimeParseError):
        parse_time_to_seconds("no-es-un-tiempo")

def test_empty_raises():
    with pytest.raises(TimeParseError):
        parse_time_to_seconds("")