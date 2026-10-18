"""Deterministic rules engine. Every rupee figure the user sees comes from here, never from the LLM."""
import math
from datetime import date

from .. import config as C
from ..models import Account, Flag, ParsedReport, UserInputs


def half_up(x: float) -> int:
    return int(math.floor(x + 0.5))


def months_back(d: date, n: int) -> date:
    y, m = d.year, d.month - n
    while m <= 0:
        y, m = y - 1, m + 12
    return date(y, m, min(d.day, 28))


def emi_formula(principal: int, annual_rate: float, months: int) -> int:
    if annual_rate == 0:
        return round(principal / months)
    r = annual_rate / 1200
    return round(principal * r * (1 + r) ** months / ((1 + r) ** months - 1))


def choose_emi(a: Account) -> tuple[int | None, str]:
    """Reported EMI -> actual payment amount -> formula estimate. A user-confirmed value wins over all."""
    if a.emi_confirmed is not None:
        return a.emi_confirmed, "user_confirmed"
    if a.emi:
        return a.emi, "reported_emi"
    if a.actual_payment:
        return a.actual_payment, "actual_payment_amount"
    if a.sanctioned and a.tenure and a.tenure.isdigit():
        rate = float(a.rate) if a.rate else C.DEFAULT_RATES.get(a.type, C.FALLBACK_RATE)
        return emi_formula(a.sanctioned, rate, int(a.tenure)), f"estimated ({rate}% {'reported' if a.rate else 'default'} rate, user to confirm)"
    return None, "unknown (ask the user)"


def label(a: Account) -> str:
    return f"{a.member} {a.account_last4}".strip()


def is_stale(a: Account, report_date: date) -> bool:
    return a.is_open and a.reported is not None and (report_date - a.reported).days > C.STALE_ACCOUNT_DAYS


def compute(report: ParsedReport, inputs: UserInputs) -> dict:
    rd = report.report_date
    own_open = [a for a in report.accounts if a.is_open and a.ownership in C.OWN_OWNERSHIP]
    other_open = [a for a in report.accounts if a.is_open and a.ownership not in C.OWN_OWNERSHIP]
    cards = [a for a in own_open if a.is_card]
    loans = [a for a in own_open if not a.is_card]

    emi_rows = {}
    for a in loans:
        value, source = choose_emi(a)
        emi_rows[f"{a.member} {a.type}"] = {"emi": value, "source": source}
    loan_emi = sum(r["emi"] or 0 for r in emi_rows.values())

    card_bal = sum(a.balance or 0 for a in cards)
    card_lim = sum(a.credit_limit or 0 for a in cards)
    min_due = sum(half_up((a.balance or 0) * C.CARD_MIN_DUE_PCT) for a in cards)
    take_home = inputs.take_home_monthly
    left = take_home - loan_emi - inputs.rent - inputs.other_fixed_expenses
    eti = loan_emi / take_home if take_home else None

    util = {label(a): round((a.balance or 0) / a.credit_limit * 100, 2) for a in cards if a.credit_limit}
    paydown = {label(a): max(0, (a.balance or 0) - half_up(a.credit_limit * C.UTILISATION_LIMIT)) for a in cards if a.credit_limit}

    enq_from = months_back(rd, C.ENQUIRY_WINDOW_MONTHS)
    enq_recent = [e for e in report.enquiries if e.date >= enq_from]
    late_from = months_back(rd, C.LATE_PAYMENT_WINDOW_MONTHS).strftime("%Y-%m")
    late = [[a.member, k, v] for a in report.accounts for k, v in sorted(a.dpd.items())
            if k >= late_from and v not in C.GOOD_CODES]

    flags: list[Flag] = []
    for member, month, code in late:
        flags.append(Flag(kind="late_payment", severity="critical" if code in C.BAD_CLASSES or code >= "060" else "warning",
                          message=f"{member}: {code} in {month}", account=member))
    for a in report.accounts:
        if a.overdue:
            flags.append(Flag(kind="overdue", severity="critical", message=f"Rs {a.overdue:,} overdue", account=label(a)))
        if a.wo_status or a.settlement or a.wo_total:
            flags.append(Flag(kind="settled_written_off", severity="critical", account=label(a),
                              message=f"{a.member} {a.type}: {a.wo_status or 'written off'}"
                                      f"{f', settled Rs {a.settlement:,}' if a.settlement else ''}"))
        if a.suit:
            flags.append(Flag(kind="suit_filed", severity="critical", message=f"{a.member}: {a.suit}", account=label(a)))
        if is_stale(a, rd):
            flags.append(Flag(kind="stale_account", severity="warning", account=label(a),
                              message=f"{a.member} {a.type}: open but last reported {a.reported:%d-%m-%Y}; likely error, consider a dispute"))
    for name, pct in util.items():
        if pct > C.UTILISATION_LIMIT * 100:
            flags.append(Flag(kind="high_utilisation", severity="warning", message=f"{name} at {pct}%", account=name))
    if len(enq_recent) >= C.ENQUIRY_BURST_COUNT:
        flags.append(Flag(kind="enquiry_burst", severity="warning",
                          message=f"{len(enq_recent)} enquiries in the last {C.ENQUIRY_WINDOW_MONTHS} months"))
    for name, row in emi_rows.items():
        if row["source"] not in ("reported_emi", "user_confirmed"):
            flags.append(Flag(kind="emi_not_reported", severity="info", message=f"{name}: {row['source']}", account=name))
    for a in other_open:
        flags.append(Flag(kind="authorised_user", severity="info", account=label(a),
                          message=f"{a.member} {a.type} held as {a.ownership.lower()}; excluded from your debt"))

    return {
        "rules_version": C.RULES_VERSION,
        "score": report.score,
        "report_date": rd.isoformat(),
        "accounts_total": len(report.accounts),
        "accounts_open_own": len(own_open),
        "accounts_open_authorised_user": len(other_open),
        "accounts_closed": sum(1 for a in report.accounts if not a.is_open),
        "total_outstanding_own": sum(a.balance or 0 for a in own_open),
        "authorised_user_balance_excluded": sum(a.balance or 0 for a in other_open),
        "monthly_loan_emi": loan_emi,
        "emi_breakdown": emi_rows,
        "income_prefill_monthly": report.income_annual // 12 if report.income_annual and report.income_frequency == "ANNUAL" else None,
        "card_min_due_5pct_own": min_due,
        "money_left_after_emi_and_fixed": left,
        "money_left_after_card_min_due": left - min_due,
        "emi_to_income_pct": round(eti * 100, 2) if eti is not None else None,
        "emi_to_income_band": None if eti is None else ("healthy" if eti < C.EMI_TO_INCOME["healthy"] else
                                                         "stretched" if eti <= C.EMI_TO_INCOME["stretched"] else "high"),
        "card_utilisation_pct_own": util,
        "overall_utilisation_pct_own": round(card_bal / card_lim * 100, 2) if card_lim else None,
        "paydown_to_30pct": paydown,
        "enquiries_last_6_months": len(enq_recent),
        "late_payments_last_12_months": late,
        "flags": [f.model_dump() for f in flags],
    }
