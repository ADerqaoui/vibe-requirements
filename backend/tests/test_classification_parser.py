"""Classification vote parser tests."""
import pytest

from app.classification.parser import VoteParseError, parse_complexity_vote


def test_parse_digit_alone() -> None:
    """A single valid digit parses directly."""
    assert parse_complexity_vote("3") == 3


def test_parse_embedded_digit() -> None:
    """The first valid embedded digit is used."""
    assert parse_complexity_vote("Complexity: 4") == 4


def test_parse_two_digits_takes_first_valid() -> None:
    """Multiple valid digits use the first one."""
    assert parse_complexity_vote("I'd say 2, maybe 5") == 2


def test_parse_out_of_range_digit_rejected() -> None:
    """Out-of-range-only responses are invalid."""
    with pytest.raises(VoteParseError, match="No valid complexity vote"):
        parse_complexity_vote("6")


def test_parse_no_digit_rejected() -> None:
    """Responses without a valid digit are invalid."""
    with pytest.raises(VoteParseError, match="No valid complexity vote"):
        parse_complexity_vote("moderate")
