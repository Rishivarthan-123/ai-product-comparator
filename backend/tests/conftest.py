import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def sample_product_html() -> str:
    return load_fixture("sample_product.html")


@pytest.fixture
def rival_product_html() -> str:
    return load_fixture("rival_product.html")
