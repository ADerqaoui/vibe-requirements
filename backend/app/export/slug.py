"""Filename slug generation."""
import re
import unicodedata

NON_ALNUM = re.compile(r"[^a-z0-9]+")
REPEATED_DASHES = re.compile(r"-+")
DEFAULT_SLUG = "project"


def slugify(value: str) -> str:
    """Return a lowercase ASCII filename slug."""
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
    )
    dashed_value = NON_ALNUM.sub("-", ascii_value)
    normalized_value = REPEATED_DASHES.sub("-", dashed_value).strip("-")
    if normalized_value == "":
        return DEFAULT_SLUG
    return normalized_value
