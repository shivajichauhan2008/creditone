from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_then_insights(pdf_bytes, expected):
    r = client.post("/api/reports/parse",
                    files={"file": ("r.pdf", pdf_bytes("synthetic_credit_report_protected.pdf"), "application/pdf")},
                    data={"password": expected["pdf_password"]})
    assert r.status_code == 200, r.text
    report = r.json()
    r2 = client.post("/api/insights", json={"report": report, "inputs": {"take_home_monthly": 110000, "rent": 22000,
                                                                         "other_fixed_expenses": 15000}})
    assert r2.status_code == 200
    assert r2.json()["money_left_after_card_min_due"] == expected["expected_insights"]["money_left_after_card_min_due"]


def test_password_errors(pdf_bytes):
    files = {"file": ("r.pdf", pdf_bytes("synthetic_credit_report_protected.pdf"), "application/pdf")}
    assert client.post("/api/reports/parse", files=files).status_code == 401


def test_rejects_non_pdf():
    r = client.post("/api/reports/parse", files={"file": ("x.txt", b"hello", "text/plain")})
    assert r.status_code == 415
