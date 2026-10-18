import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


@pytest.fixture(scope="session")
def expected():
    return json.loads((FIXTURES / "synthetic_credit_report_expected.json").read_text())


@pytest.fixture(scope="session")
def pdf_bytes():
    return lambda name: (FIXTURES / name).read_bytes()


@pytest.fixture(scope="session")
def parsed(pdf_bytes):
    from app.parsing import parse_report
    return parse_report(pdf_bytes("synthetic_credit_report.pdf"))
