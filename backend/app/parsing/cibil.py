"""Adapter for the CIBIL report layout.

Keyed on the report's fixed labels (ACCOUNT DETAILS, DATES, the DAYS PAST DUE grid,
DEFAULT STATUS) and on word positions, so it works on text-layer and OCR output alike.
Personal details (name, PAN, DOB, address, phone) are deliberately never extracted.
"""
import re
from datetime import date

from ..models import Account, Enquiry, ParsedReport
from .pdf import Line

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DATE_RE = re.compile(r"\b(\d{2})-(\d{2})-(\d{4})\b")
DPD_CODE = re.compile(r"^(\d{3}|STD|SMA|SUB|DBT|LSS|XXX)$")

LABELS = {
    "CREDIT LIMIT": "credit_limit", "SANCTIONED AMOUNT": "sanctioned", "HIGH CREDIT": "high_credit",
    "CURRENT BALANCE": "balance", "CASH LIMIT": "cash_limit", "AMOUNT OVERDUE": "overdue",
    "RATE OF INTEREST": "rate", "REPAYMENT TENURE": "tenure", "EMI AMOUNT": "emi",
    "PAYMENT FREQUENCY": "frequency", "ACTUAL PAYMENT AMOUNT": "actual_payment",
    "DATE OPENED/DISBURSED": "opened", "DATE CLOSED": "closed", "DATE OF LAST PAYMENT": "last_payment",
    "DATE REPORTED AND CERTIFIED": "reported", "PAYMENT START DATE": "pay_start", "PAYMENT END DATE": "pay_end",
    "SUIT FILED/WILFUL DEFAULT": "suit", "WRITTEN-OFF STATUS": "wo_status",
    "WRITTEN-OFF AND SETTLED STATUS": "wo_status", "WRITTEN-OFF AMOUNT(TOTAL)": "wo_total",
    "WRITTEN-OFF AMOUNT(PRINCIPAL)": "wo_principal", "SETTLEMENT AMOUNT": "settlement",
    "VALUE OF COLLATERAL": "_collateral_value", "TYPE OF COLLATERAL": "_collateral_type",
}
AMOUNT_FIELDS = {"credit_limit", "sanctioned", "high_credit", "balance", "cash_limit", "overdue", "emi",
                 "actual_payment", "wo_total", "wo_principal", "settlement"}
DATE_FIELDS = {"opened", "closed", "last_payment", "reported", "pay_start", "pay_end"}
_LABELS_BY_LEN = sorted(LABELS, key=len, reverse=True)


def to_amount(s: str | None) -> int | None:
    if s is None:
        return None
    s = s.replace(",", "").replace("Rs.", "").strip()
    return int(s) if re.fullmatch(r"-?\d+", s) else None


def to_date(s: str | None) -> date | None:
    m = DATE_RE.search(s or "")
    return date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else None


JUNK = " -_—–=|.,'’‘\"~"


def clean(s: str | None) -> str | None:
    """'-' means empty; OCR adds stray marks (_ — = |) around values, so strip those too."""
    s = (s or "").strip().strip(JUNK).strip()
    return s or None


def is_month(tok: str) -> bool:
    import difflib

    u = tok.upper().replace("0", "O")[:3]
    return u in MONTHS or bool(difflib.get_close_matches(u, MONTHS, n=1, cutoff=0.6))


def norm_dpd(tok: str) -> str | None:
    """'000', '030', 'STD' ... ; tolerate OCR's letter O for zero and dropped leading zeros."""
    t = tok.upper().strip(".,:;")
    if re.fullmatch(r"[0-9O]{1,4}", t):
        t = t.replace("O", "0")
        t = "000" if set(t) == {"0"} else t.zfill(3)
    return t if DPD_CODE.match(t) else None


def parse_kv(text: str) -> dict[str, str]:
    """Split a line like 'CREDIT LIMIT 50,000 RATE OF INTEREST 36.0' into label -> value."""
    spans: list[tuple[int, int, str]] = []
    for label in _LABELS_BY_LEN:
        for m in re.finditer(re.escape(label), text):
            s, e = m.span()
            if not any(s < e2 and e > s2 for s2, e2, _ in spans):
                spans.append((s, e, label))
    spans.sort()
    out = {}
    for i, (s, e, label) in enumerate(spans):
        nxt = spans[i + 1][0] if i + 1 < len(spans) else len(text)
        out[LABELS[label]] = text[e:nxt].strip()
    return out


def _strip_chrome(lines: list[Line]) -> list[Line]:
    """Drop the repeating page header (top ~13%) and footer (bottom ~7%)."""
    return [ln for ln in lines if 0.13 * ln.page_height < ln.top < 0.93 * ln.page_height]


def parse(lines: list[Line], used_ocr: bool = False) -> ParsedReport:
    page1 = " ".join(ln.text for ln in lines if ln.page == 0)
    report_date = to_date(re.search(r"DATE:?\s*(\d{2}-\d{2}-\d{4})", page1).group(1)) if "DATE" in page1 else None
    body = _strip_chrome(lines)

    score, income, income_freq = None, None, None
    accounts: list[Account] = []
    enquiries: list[Enquiry] = []

    i, pending, section = 0, [], None
    while i < len(body):
        ln, t = body[i], body[i].text

        if t.startswith("CREDIT SCORE") or "TRANSUNION SCORE" in t:
            section = "score"
        elif score is None and (section == "score" or "YOUR SCORE" in t.upper()):
            # the score is large type; OCR can split '682' into '6 82', so look at nearby lines too
            near = [body[k].text for k in range(max(0, i - 2), i + 1)]
            for cand in reversed(near):
                m = re.search(r"\b([3-8]\d\d|900)\b", re.sub(r"(?<=\d) (?=\d)", "", cand).replace("(range 300 - 900)", "").replace("300 900", ""))
                if m:
                    score, section = int(m.group(1)), None
                    break
        if "INCOME INDICATOR" in t and i + 1 < len(body):
            parts = body[i + 1].text.split()
            income = to_amount(parts[0]) if parts else None
            income_freq = parts[1] if len(parts) > 1 else None

        if t.startswith("ACCOUNT INFORMATION"):
            pending = []
        elif t.startswith("(MEMBER NAME)"):
            acc, i = _parse_account(body, i, pending)
            accounts.append(acc)
            pending = []
            continue
        elif t.startswith("ENQUIRY INFORMATION") or ("DATE OF ENQUIRY" in t and not enquiries):
            enquiries, i = _parse_enquiries(body, i + 1)
            continue
        else:
            pending.append(ln)
        i += 1

    big = _largest_score_token([ln for ln in lines if ln.page == 0])
    score = big if big is not None else score
    return ParsedReport(bureau="cibil", report_date=report_date, score=score, income_annual=income,
                        income_frequency=income_freq, accounts=accounts, enquiries=enquiries, used_ocr=used_ocr)


def _largest_score_token(page_lines: list[Line]) -> int | None:
    """The score is the 300-900 number in the largest type on page 1 (gauge ticks are small)."""
    words = [w for ln in page_lines for w in ln.words]
    if not words:
        return None
    heights = sorted(w.bottom - w.top for w in words)
    typical = heights[len(heights) // 2]
    cands = [w for w in words if re.fullmatch(r"[3-9]\d\d", w.text) and 300 <= int(w.text) <= 900
             and (w.bottom - w.top) > 1.6 * typical]
    return int(max(cands, key=lambda w: w.bottom - w.top).text) if cands else None


ICON_JUNK = re.compile(r"^(?=.*[A-Z0-9])[A-Z0-9&.,'/()-]+$")


def _header(label_line: Line, pending: list[Line]) -> list[str]:
    """Member / type / number / ownership sit above the '(MEMBER NAME) ...' label row, in the same columns."""
    starts = [w.x0 - 3 for w in label_line.words if w.text.startswith("(")]
    cols = [[] for _ in starts]
    above = [ln for ln in pending if ln.page == label_line.page and 0 < label_line.top - ln.top < 32]
    for ln in above:
        for w in ln.words:
            idx = max([k for k, s in enumerate(starts) if w.x0 >= s] or [0])
            cols[idx].append(w)
    # wrapped names ("KAVERI SMALL FINANCE / BANK") read top-to-bottom, then left-to-right
    out = []
    for c in cols:
        rows: list[list] = []
        for w in sorted(c, key=lambda w: w.top):
            if rows and w.top - rows[-1][0].top < 5:
                rows[-1].append(w)
            else:
                rows.append([w])
        ordered = [w.text for row in rows for w in sorted(row, key=lambda w: w.x0)]
        while ordered and not ICON_JUNK.match(ordered[0]):   # bullet icons OCR'd as '@', 'r', 'Yd)'
            ordered.pop(0)
        text = " ".join(ordered)
        out.append(clean(re.sub(r"(\w)\(", r"\1 (", text)) or "")
    return out


def _parse_account(body: list[Line], i: int, pending: list[Line]) -> tuple[Account, int]:
    member, typ, number, ownership = (_header(body[i], pending) + ["", "", "", ""])[:4]
    fields: dict[str, str] = {}
    dpd: dict[str, str] = {}
    month_x: dict[str, float] = {}
    i += 1
    while i < len(body):
        t = body[i].text
        if t.startswith("(MEMBER NAME)") or t.startswith("ENQUIRY INFORMATION"):
            break
        if sum(is_month(w.text) for w in body[i].words) >= 9 and len(body[i].words) >= 12:
            # header columns run DEC .. JAN; position is more reliable than OCR'd spelling,
            # and the 'MONTH / YEAR' corner cell is often unreadable, so take the last 12 tokens
            month_x = {m: w.cx for m, w in zip(reversed(MONTHS), body[i].words[-12:])}
        elif month_x and re.match(r"^(19|20)\d\d\b", t):
            year = body[i].words[0].text
            for w in body[i].words[1:]:
                code = norm_dpd(w.text)
                if code:
                    mon = min(month_x, key=lambda m: abs(month_x[m] - w.cx))
                    dpd[f"{year}-{MONTHS.index(mon) + 1:02d}"] = code
        else:
            fields.update(parse_kv(t))
        done = "settlement" in fields
        i += 1
        if done:
            break

    data: dict = {"member": member, "type": typ, "ownership": ownership,
                  "account_last4": re.sub(r"\W", "", number)[-4:], "dpd": dict(sorted(dpd.items()))}
    for k, v in fields.items():
        if k.startswith("_"):
            continue
        if k in AMOUNT_FIELDS:
            data[k] = to_amount(clean(v))
        elif k in DATE_FIELDS:
            data[k] = to_date(v)
        else:
            data[k] = clean(v)
    return Account(**data), i


def _parse_enquiries(body: list[Line], i: int) -> tuple[list[Enquiry], int]:
    out = []
    row = re.compile(r"^(.*?)\s+(\d{2}-\d{2}-\d{4})\s+(.*?)\s+([\d,]+|-)$")
    while i < len(body):
        t = body[i].text
        if t.startswith("END OF"):
            break
        m = row.match(t)
        if m:
            out.append(Enquiry(member=m.group(1), date=to_date(m.group(2)), purpose=m.group(3),
                               amount_as_printed=to_amount(clean(m.group(4)))))
        i += 1
    return out, i
