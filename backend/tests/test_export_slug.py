"""Slug generation tests."""
from app.export.slug import slugify


def test_slugify_lowercases_and_collapses_separators() -> None:
    """Names become lowercase ASCII slug strings."""
    assert slugify("Brake Controller!! v2") == "brake-controller-v2"


def test_slugify_removes_non_ascii_marks() -> None:
    """Accents are normalized to ASCII."""
    assert slugify("Ångström Control") == "angstrom-control"


def test_slugify_returns_default_for_empty_result() -> None:
    """Names without usable characters still get a filename."""
    assert slugify("!!!") == "project"
