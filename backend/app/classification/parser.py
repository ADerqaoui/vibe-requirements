"""Complexity vote parser."""
import re

VALID_VOTE = re.compile(r"[1-5]")


class VoteParseError(Exception):
    """Raised when a model response does not contain a valid complexity vote."""


def parse_complexity_vote(text: str) -> int:
    """Extract the first valid complexity digit from model text."""
    match = VALID_VOTE.search(text)
    if match is None:
        raise VoteParseError("No valid complexity vote found in model response")
    return int(match.group(0))
