"""Rules engine must match the expected insight figures for the synthetic report."""
from app.models import UserInputs
from app.rules import compute, emi_formula

NUMERIC = ["score", "accounts_total", "accounts_open_own", "accounts_open_authorised_user", "accounts_closed",
           "total_outstanding_own", "authorised_user_balance_excluded", "monthly_loan_emi", "income_prefill_monthly",
           "card_min_due_5pct_own", "money_left_after_emi_and_fixed", "money_left_after_card_min_due",
           "emi_to_income_pct", "card_utilisation_pct_own", "overall_utilisation_pct_own", "paydown_to_30pct",
           "enquiries_last_6_months", "late_payments_last_12_months"]


def run(parsed, expected):
    t = expected["test_inputs"]
    return compute(parsed, UserInputs(take_home_monthly=t["take_home_monthly"], rent=t["rent"],
                                      other_fixed_expenses=t["other_fixed_expenses"]))


def test_figures_match(parsed, expected):
    out, want = run(parsed, expected), expected["expected_insights"]
    for k in NUMERIC:
        assert out[k] == want[k], k


def test_emi_sources(parsed, expected):
    out, want = run(parsed, expected), expected["expected_insights"]["emi_breakdown"]
    assert {k: v["emi"] for k, v in out["emi_breakdown"].items()} == {k: v["emi"] for k, v in want.items()}
    sources = {k: v["source"].split(" ")[0] for k, v in out["emi_breakdown"].items()}
    assert sources == {"MERIDIAN BANK PERSONAL LOAN": "reported_emi",
                       "SUNRISE AUTO FINANCE AUTO LOAN (PERSONAL)": "actual_payment_amount",
                       "ORBIT CONSUMER FINANCE CONSUMER LOAN": "estimated"}


def test_flags(parsed, expected):
    kinds = {f["kind"] for f in run(parsed, expected)["flags"]}
    assert {"late_payment", "settled_written_off", "high_utilisation", "enquiry_burst",
            "stale_account", "emi_not_reported", "authorised_user"} <= kinds
    assert "overdue" not in kinds and "suit_filed" not in kinds


def test_emi_formula():
    assert emi_formula(48000, 0, 12) == 4000
    assert emi_formula(500000, 13.75, 48) == 13601  # standard reducing-balance EMI
