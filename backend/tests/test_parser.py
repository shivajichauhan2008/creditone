"""The CIBIL-layout adapter must reproduce the ground-truth JSON field by field."""
import shutil
from datetime import date

import pytest

from app.parsing import PasswordRequired, WrongPassword, parse_report

FIELDS = ["member", "type", "ownership", "account_last4", "credit_limit", "sanctioned", "high_credit", "balance",
          "cash_limit", "overdue", "rate", "tenure", "emi", "frequency", "actual_payment", "suit", "wo_status",
          "wo_total", "wo_principal", "settlement"]


def iso(v):
    if v is None:
        return None
    if isinstance(v, date):
        return v.isoformat()
    return v if v[4] == "-" else f"{v[6:]}-{v[3:5]}-{v[:2]}"   # dd-mm-yyyy -> iso


def check_against_truth(report, expected, check_dpd=True):
    assert report.score == expected["score"]
    assert report.report_date.isoformat() == expected["report_date"]
    assert report.income_annual == expected["employment"]["income"]
    assert len(report.accounts) == len(expected["accounts"])
    for got, want in zip(report.accounts, expected["accounts"]):
        g = got.model_dump()
        for f in FIELDS:
            assert g[f] == want[f], f"{want['member']} {f}: {g[f]!r} != {want[f]!r}"
        for f in ["opened", "closed", "last_payment", "reported", "pay_start", "pay_end"]:
            assert iso(g[f]) == iso(want[f]), f"{want['member']} {f}"
        if check_dpd:
            assert g["dpd"] == want["dpd"], f"{want['member']} dpd"
    assert [(e.member, e.date.isoformat(), e.purpose) for e in report.enquiries] == \
           [(e["member"], e["date"], e["purpose"]) for e in expected["enquiries"]]


def test_text_layer_report(parsed, expected):
    assert parsed.used_ocr is False
    assert parsed.issues == []
    check_against_truth(parsed, expected)


def test_no_personal_data_extracted(parsed):
    dumped = parsed.model_dump_json()
    for secret in ["SAMPLETEST", "AAAAA0000A", "9000000000", "01-01-1990", "TEST RESIDENCY"]:
        assert secret not in dumped


def test_protected_report(pdf_bytes, expected):
    data = pdf_bytes("synthetic_credit_report_protected.pdf")
    with pytest.raises(PasswordRequired):
        parse_report(data)
    with pytest.raises(WrongPassword):
        parse_report(data, "nope")
    check_against_truth(parse_report(data, expected["pdf_password"]), expected)


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
def test_image_only_report_uses_ocr(pdf_bytes, expected):
    report = parse_report(pdf_bytes("synthetic_credit_report_image_only.pdf"))
    assert report.used_ocr is True
    assert report.issues == []
    check_against_truth(report, expected)
