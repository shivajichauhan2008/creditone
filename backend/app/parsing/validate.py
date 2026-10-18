"""Sanity checks run before anything is shown to the user."""
import re

from ..models import ParsedReport

DPD_CODE = re.compile(r"^(\d{3}|STD|SMA|SUB|DBT|LSS|XXX)$")


def validate(r: ParsedReport) -> list[str]:
    issues = []
    if r.report_date is None:
        issues.append("Report date not found")
    if r.score is None or not 300 <= r.score <= 900:
        issues.append("Score missing or out of range")
    if not r.accounts:
        issues.append("No accounts found")
    for a in r.accounts:
        name = f"{a.member} {a.type} {a.account_last4}".strip()
        if not a.member or not a.type or not a.ownership:
            issues.append(f"Account header incomplete: {name}")
        if a.balance is None:
            issues.append(f"Current balance missing: {name}")
        if a.opened and r.report_date and a.opened > r.report_date:
            issues.append(f"Opened after report date: {name}")
        bad = [c for c in a.dpd.values() if not DPD_CODE.match(c)]
        if bad:
            issues.append(f"Unreadable payment-history codes {bad[:3]}: {name}")
        if a.is_open and a.credit_limit is None and a.sanctioned is None:
            issues.append(f"No limit or sanctioned amount: {name}")
    return issues
