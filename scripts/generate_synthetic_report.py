"""Synthetic credit report generator (v2) for parser testing.

Layout follows the structure of Indian consumer credit reports (score, personal,
contact, employment, account blocks with a year x month DPD grid, enquiries).
Fictional person and fictional lenders. Not bureau-branded. Watermarked as test data.

Outputs (in OUT):
  synthetic_credit_report.pdf              text layer present
  synthetic_credit_report_image_only.pdf   scanned-style, no text layer (OCR path)
  synthetic_credit_report_protected.pdf    text PDF, password TEST1234
  synthetic_credit_report_expected.json    ground truth + expected insights
"""
import json, os, math, io
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether)
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fixtures")
REPORT_DATE = date(2026, 10, 10)
PASSWORD = "TEST1234"
MON = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]

BLUE = colors.HexColor("#1b8fc0"); YELLOW = colors.HexColor("#f6d54a")
OLIVE = colors.HexColor("#8a7f3a"); LBL = colors.HexColor("#1b8fc0"); RULE = colors.HexColor("#1b8fc0")

# ------------------------------------------------------------------ data
def months_between(start, end):
    """inclusive list of (y, m) from start to end; start/end = (y, m)"""
    y, m = start; out = []
    while (y, m) <= end:
        out.append((y, m)); m += 1
        if m == 13: y, m = y + 1, 1
    return out

def dpd(start, end, default="000", **over):
    """over keys like m2026_03='030'"""
    months = months_between(start, end)[-36:]
    d = {f"{y}-{m:02d}": default for y, m in months}
    for k, v in over.items():
        d[k[1:].replace("_", "-")] = v
    return d

person = dict(name="RAHUL SAMPLETEST", dob="01-01-1990", gender="MALE",
              id_type="INCOME TAX ID NUMBER (PAN)", id_number="AAAAA0000A")
addresses = [
    ("FLAT 000, TEST RESIDENCY, SAMPLE NAGAR NOIDA", "UTTAR PRADESH-201301", "RESIDENCE ADDRESS", "12-05-2026"),
    ("TOWER 0, EXAMPLE TECH PARK SECTOR 00 NOIDA", "UTTAR PRADESH-201301", "OFFICE ADDRESS", "08-08-2026"),
]
phones = [("MOBILE PHONE", "9000000000"), ("OFFICE PHONE", "1200000000")]
employment = dict(account_type="CREDIT CARD", date_reported="08-08-2026", occupation="SALARIED",
                  income=1320000, frequency="ANNUAL", indicator="NET INCOME")
score = 682

N = None
accounts = [
  dict(member="MERIDIAN BANK", type="PERSONAL LOAN", number="MB00PL0000004411", ownership="INDIVIDUAL",
       credit_limit=N, sanctioned=500000, high_credit=N, balance=312450, cash_limit=N, overdue=0,
       rate="13.75", tenure="48", emi=13650, frequency="MONTHLY", actual_payment=13650,
       opened="15-03-2024", closed=N, last_payment="05-10-2026", reported="30-09-2026",
       pay_start="01-09-2026", pay_end="01-04-2024", dpd=dpd((2024,4),(2026,9)),
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
  dict(member="SUNRISE AUTO FINANCE", type="AUTO LOAN (PERSONAL)", number="SAF0000007820", ownership="INDIVIDUAL",
       credit_limit=N, sanctioned=650000, high_credit=N, balance=348200, cash_limit=N, overdue=0,
       rate=N, tenure="60", emi=N, frequency="MONTHLY", actual_payment=14200,
       opened="10-08-2023", closed=N, last_payment="07-10-2026", reported="30-09-2026",
       pay_start="01-09-2026", pay_end="01-10-2023",
       dpd=dpd((2023,10),(2026,9), m2026_03="030"),
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
  dict(member="LOTUS BANK", type="CREDIT CARD", number="4000000000009032", ownership="INDIVIDUAL",
       credit_limit=150000, sanctioned=N, high_credit=132400, balance=121600, cash_limit=45000, overdue=0,
       rate="42.0", tenure=N, emi=N, frequency="MONTHLY", actual_payment=18000,
       opened="22-01-2017", closed=N, last_payment="28-09-2026", reported="30-09-2026",
       pay_start="01-09-2026", pay_end="01-10-2023", dpd=dpd((2023,10),(2026,9)),
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
  dict(member="MERIDIAN BANK", type="CREDIT CARD", number="5000000000005567", ownership="AUTHORISED USER",
       credit_limit=80000, sanctioned=N, high_credit=41200, balance=18400, cash_limit=24000, overdue=0,
       rate="38.4", tenure=N, emi=N, frequency="MONTHLY", actual_payment=9100,
       opened="03-06-2022", closed=N, last_payment="02-10-2026", reported="30-09-2026",
       pay_start="01-09-2026", pay_end="01-10-2023", dpd=dpd((2023,10),(2026,9)),
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
  dict(member="ORBIT CONSUMER FINANCE", type="CONSUMER LOAN", number="OCF000002093", ownership="INDIVIDUAL",
       credit_limit=N, sanctioned=48000, high_credit=N, balance=24000, cash_limit=N, overdue=0,
       rate=N, tenure="12", emi=N, frequency=N, actual_payment=N,
       opened="05-11-2025", closed=N, last_payment="05-10-2026", reported="30-09-2026",
       pay_start="01-09-2026", pay_end="01-12-2025", dpd=dpd((2025,12),(2026,9), m2025_12="XXX"),
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
  dict(member="NOVA BANK", type="CREDIT CARD", number="4500000000001184", ownership="INDIVIDUAL",
       credit_limit=50000, sanctioned=N, high_credit=22300, balance=9850, cash_limit=15000, overdue=0,
       rate="36.0", tenure=N, emi=N, frequency="MONTHLY", actual_payment=2400,
       opened="14-06-2016", closed=N, last_payment="12-01-2019", reported="31-01-2019",
       pay_start="01-01-2019", pay_end="01-02-2016", dpd=dpd((2016,2),(2019,1)),
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
  dict(member="KAVERI SMALL FINANCE BANK", type="PERSONAL LOAN", number="KSF00000000158", ownership="INDIVIDUAL",
       credit_limit=N, sanctioned=100000, high_credit=N, balance=0, cash_limit=N, overdue=0,
       rate=N, tenure="24", emi=N, frequency="MONTHLY", actual_payment=N,
       opened="12-02-2019", closed="30-06-2021", last_payment="18-06-2021", reported="30-06-2021",
       pay_start="01-06-2021", pay_end="01-07-2018",
       dpd=dpd((2019,3),(2021,6), m2020_06="030", m2020_07="060", m2020_08="090", m2020_09="SUB",
               m2020_10="SUB", m2020_11="SUB", m2020_12="DBT", m2021_01="DBT", m2021_02="DBT",
               m2021_03="DBT", m2021_04="DBT", m2021_05="DBT", m2021_06="DBT",
               **{f"m2019_{m:02d}": "000" for m in range(3, 13)}),
       suit=N, wo_status="SETTLED", wo_total=62000, wo_principal=55000, settlement=38000),
  dict(member="KAVERI SMALL FINANCE BANK", type="LOAN AGAINST BANK DEPOSITS", number="KSF00000000201-0", ownership="INDIVIDUAL",
       credit_limit=N, sanctioned=200000, high_credit=N, balance=0, cash_limit=N, overdue=0,
       rate=N, tenure=N, emi=N, frequency=N, actual_payment=N,
       opened="24-12-2014", closed="23-03-2015", last_payment=N, reported="31-03-2015",
       pay_start="01-03-2015", pay_end="01-12-2014",
       dpd={"2014-12": "STD", "2015-01": "STD", "2015-02": "STD", "2015-03": "XXX"},
       suit=N, wo_status=N, wo_total=N, wo_principal=N, settlement=N),
]
enquiries = [
  ("APEX BANK", "12-09-2026", "PERSONAL LOAN", 10000000), ("APEX BANK", "11-09-2026", "HOUSING LOAN", 10000000),
  ("APEX BANK", "09-09-2026", "TWO-WHEELER LOAN", 10000000), ("NIMBUS BANK", "02-08-2026", "CREDIT CARD", 100),
  ("FINTRUST CAPITAL", "20-06-2026", "PERSONAL LOAN", 200000), ("LOTUS BANK", "14-05-2026", "CREDIT CARD", 100),
  ("NIMBUS BANK", "28-02-2026", "CREDIT CARD", 100), ("ORBIT CONSUMER FINANCE", "04-11-2025", "CONSUMER LOAN", 48000),
  ("MERIDIAN BANK", "02-03-2024", "PERSONAL LOAN", 500000), ("SUNRISE AUTO FINANCE", "28-07-2023", "AUTO LOAN (PERSONAL)", 650000),
  ("NOVA BANK", "30-05-2016", "OTHER", 1),
]

# ------------------------------------------------------------------ helpers
def inr(n):
    if n is None: return "-"
    s = str(int(n)); last3, rest = s[-3:], s[:-3]; parts = []
    while len(rest) > 2: parts.insert(0, rest[-2:]); rest = rest[:-2]
    if rest: parts.insert(0, rest)
    return ",".join(parts + [last3])
v = lambda x: "-" if x in (None, "") else str(x)

TXT = ParagraphStyle("t", fontName="Times-Roman", fontSize=9, leading=11)
LAB = ParagraphStyle("l", fontName="Helvetica-Bold", fontSize=8.5, textColor=LBL, leading=10)

def section_bar(title):
    t = Table([[title]], colWidths=[180*mm], rowHeights=[8*mm])
    t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), BLUE), ("TEXTCOLOR", (0,0), (-1,-1), colors.black),
                           ("FONT", (0,0), (-1,-1), "Helvetica-Bold", 11), ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                           ("LEFTPADDING", (0,0), (-1,-1), 8), ("ROUNDEDCORNERS", [8, 0, 0, 8])]))
    return [Spacer(1, 6), t, Spacer(1, 4)]

def labelled(rows, widths, heads=None):
    """label rows (blue) at indices `heads` (default: even rows), others are value rows"""
    heads = set(range(0, len(rows), 2)) if heads is None else set(heads)
    data, style = [], [("LEFTPADDING", (0,0), (-1,-1), 4), ("TOPPADDING", (0,0), (-1,-1), 1), ("BOTTOMPADDING", (0,0), (-1,-1), 1)]
    for i, r in enumerate(rows):
        data.append(r)
        h = i in heads
        style.append(("FONT", (0, i), (-1, i), "Helvetica-Bold" if h else "Times-Roman", 8.5 if h else 9))
        style.append(("TEXTCOLOR", (0, i), (-1, i), LBL if h else colors.black))
        if not h and (i + 1 in heads or i == len(rows) - 1): style.append(("LINEBELOW", (0, i), (-1, i), 0.5, RULE))
    t = Table(data, colWidths=widths); t.setStyle(TableStyle(style)); return t

def kv_block(title, pairs_left, pairs_right):
    rows = [[title, "", "", ""]]
    for (a, b), (c, d) in zip(pairs_left, pairs_right):
        rows.append([a, b, c, d])
    t = Table(rows, colWidths=[44*mm, 38*mm, 58*mm, 40*mm])
    t.setStyle(TableStyle([("FONT", (0,0), (-1,0), "Helvetica-Bold", 8.5), ("TEXTCOLOR", (0,0), (-1,0), LBL),
                           ("FONT", (0,1), (-1,-1), "Times-Roman", 8.8), ("TOPPADDING", (0,0), (-1,-1), 0.6),
                           ("BOTTOMPADDING", (0,0), (-1,-1), 0.6), ("LEFTPADDING", (0,0), (-1,-1), 4),
                           ("LINEBELOW", (0,-1), (-1,-1), 0.5, RULE)]))
    return t

def dpd_grid(d):
    years = sorted({int(k[:4]) for k in d}, reverse=True)
    head = ["YEAR"] + [m for m in reversed(MON)]
    rows = [head]
    for y in years:
        rows.append([str(y)] + [d.get(f"{y}-{MON.index(m)+1:02d}", "") for m in reversed(MON)])
    t = Table(rows, colWidths=[20*mm] + [13.3*mm]*12)
    t.setStyle(TableStyle([("FONT", (0,0), (-1,0), "Times-Bold", 7.6), ("FONT", (0,1), (0,-1), "Times-Bold", 8),
                           ("FONT", (1,1), (-1,-1), "Times-Roman", 8.5), ("GRID", (0,0), (-1,-1), 0.6, colors.black),
                           ("ALIGN", (1,0), (-1,-1), "CENTER"), ("TOPPADDING", (0,0), (-1,-1), 1.2), ("BOTTOMPADDING", (0,0), (-1,-1), 1.2)]))
    return t

def account_block(a):
    HB = ParagraphStyle("hb", fontName="Times-Bold", fontSize=9, leading=10)
    head = Table([[Paragraph(a["member"], HB), Paragraph(a["type"], HB), a["number"], a["ownership"]],
                  ["(MEMBER NAME)", "(ACCOUNT TYPE)", "(ACCOUNT NUMBER)", "(OWNERSHIP)"]],
                 colWidths=[45*mm, 45*mm, 52*mm, 38*mm])
    head.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), YELLOW), ("FONT", (0,0), (-1,0), "Times-Bold", 9),
                              ("FONT", (0,1), (-1,1), "Times-Roman", 8.5), ("TEXTCOLOR", (0,1), (-1,1), OLIVE),
                              ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("LEFTPADDING", (0,0), (-1,-1), 4)]))
    is_card = a["credit_limit"] is not None
    det = kv_block("ACCOUNT DETAILS",
        [("CREDIT LIMIT", inr(a["credit_limit"])),
         ("HIGH CREDIT" if is_card else "SANCTIONED AMOUNT", inr(a["high_credit"] if is_card else a["sanctioned"])),
         ("CURRENT BALANCE", inr(a["balance"])), ("CASH LIMIT", inr(a["cash_limit"])), ("AMOUNT OVERDUE", inr(a["overdue"]))],
        [("RATE OF INTEREST", v(a["rate"])), ("REPAYMENT TENURE", v(a["tenure"])), ("EMI AMOUNT", inr(a["emi"])),
         ("PAYMENT FREQUENCY", v(a["frequency"])), ("ACTUAL PAYMENT AMOUNT", inr(a["actual_payment"]))])
    dates = kv_block("DATES", [("DATE OPENED/DISBURSED", v(a["opened"])), ("DATE CLOSED", v(a["closed"]))],
                     [("DATE OF LAST PAYMENT", v(a["last_payment"])), ("DATE REPORTED AND CERTIFIED", v(a["reported"]))])
    ks = sorted(a["dpd"]); a["pay_start"] = f"01-{ks[0][5:]}-{ks[0][:4]}"; a["pay_end"] = f"01-{ks[-1][5:]}-{ks[-1][:4]}"
    ph = kv_block("PAYMENT HISTORY (UP TO 36 MONTHS)", [("PAYMENT START DATE", v(a["pay_start"])), ("", "DD-MM-YYYY")],
                  [("PAYMENT END DATE", v(a["pay_end"])), ("", "DD-MM-YYYY")])
    lab = Paragraph("DAYS PAST DUE (No.of Days) or ASSET CLASSIFICATION (STD, SMA, SUB, DBT, LSS)", LAB)
    coll = kv_block("COLLATERAL", [("VALUE OF COLLATERAL", "-"), ("TYPE OF COLLATERAL", "-"), ("", ""), ("", ""), ("", "")],
                    [("SUIT FILED/WILFUL DEFAULT", v(a["suit"])), ("WRITTEN-OFF STATUS", v(a["wo_status"])),
                     ("WRITTEN-OFF AMOUNT(TOTAL)", inr(a["wo_total"])), ("WRITTEN-OFF AMOUNT(PRINCIPAL)", inr(a["wo_principal"])),
                     ("SETTLEMENT AMOUNT", inr(a["settlement"]))])
    coll._cellvalues[0][2] = "DEFAULT STATUS"
    return [KeepTogether([head, Spacer(1, 2), det, Spacer(1, 3), dates, Spacer(1, 3), ph, Spacer(1, 3), lab,
                          Spacer(1, 2), dpd_grid(a["dpd"]), Spacer(1, 3), coll]), Spacer(1, 10)]

# ------------------------------------------------------------------ watermark + page chrome
WM = os.path.join(OUT, "_watermark.png")
im = Image.new("RGBA", (1240, 1754), (0,0,0,0))
try: f = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
except Exception: f = ImageFont.load_default()
t = Image.new("RGBA", (1600, 300), (0,0,0,0)); td = ImageDraw.Draw(t)
td.text((800, 90), "SYNTHETIC TEST DATA", font=f, fill=(200,40,40,38), anchor="mm")
td.text((800, 210), "NOT A REAL CREDIT REPORT", font=f, fill=(200,40,40,38), anchor="mm")
t = t.rotate(40, expand=True); im.alpha_composite(t, ((1240-t.width)//2, (1754-t.height)//2)); im.save(WM)

def chrome(c, doc):
    W, H = A4
    c.drawImage(WM, 0, 0, width=W, height=H, mask="auto")
    c.setFont("Helvetica-Bold", 20); c.setFillColor(BLUE); c.drawString(15*mm, H-22*mm, "SAMPLE BUREAU")
    c.setFont("Helvetica", 8); c.setFillColor(colors.grey); c.drawString(15*mm, H-26.5*mm, "Fictional bureau for software testing")
    c.setFont("Helvetica-Bold", 12); c.setFillColor(BLUE); c.drawRightString(W-15*mm, H-20*mm, "CREDIT INFORMATION REPORT")
    c.setFont("Helvetica-Bold", 7.5)
    c.drawRightString(W-15*mm, H-27*mm, "CONTROL NUMBER: 0,000,000,001")
    c.setFillColor(colors.HexColor("#e03030")); c.rect(W-73*mm, H-31*mm, 3*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(BLUE); c.drawRightString(W-15*mm, H-30.5*mm, "INDICATES SECTION IS UNDER DISPUTE")
    c.drawRightString(W-15*mm, H-34*mm, "(e)  INDICATES THE VALUE PROVIDED BY BANK")
    c.drawString(15*mm, H-34*mm, f"DATE: {REPORT_DATE:%d-%m-%Y}")
    c.setStrokeColor(colors.HexColor("#e8c840")); c.setLineWidth(1); c.line(15*mm, H-36.5*mm, W-15*mm, H-36.5*mm)
    c.setFont("Times-Roman", 7); c.setFillColor(colors.black)
    c.drawCentredString(W/2, 14*mm, "SYNTHETIC SAMPLE. Fictional person and lenders. Not issued by any credit bureau.")
    c.drawCentredString(W/2, 9*mm, f"Page {doc.page}")

# ------------------------------------------------------------------ build
story = []
story += section_bar("CREDIT SCORE")
story.append(Table([[f"{score}", "Your Score   (range 300 - 900)"]], colWidths=[30*mm, 150*mm],
                   style=TableStyle([("FONT", (0,0), (0,0), "Helvetica-Bold", 28), ("TEXTCOLOR", (0,0), (0,0), BLUE),
                                     ("FONT", (1,0), (1,0), "Times-Roman", 10), ("VALIGN", (0,0), (-1,-1), "MIDDLE")])))
story += section_bar("PERSONAL INFORMATION")
story.append(labelled([["NAME", "DATE OF BIRTH", "GENDER", ""], [person["name"], person["dob"], person["gender"], ""],
                       ["IDENTIFICATION TYPE", "NUMBER", "ISSUE DATE", "EXPIRATION DATE"],
                       [person["id_type"], person["id_number"], "-", "-"]], [62*mm, 46*mm, 36*mm, 36*mm]))
story += section_bar("CONTACT INFORMATION")
rows = []
for i, (l1, l2, cat, dt) in enumerate(addresses, 1):
    rows += [[f"ADDRESS{i} (e)", "CATEGORY", "STATUS", "DATE REPORTED"], [Paragraph(f"{l1}<br/>{l2}", TXT), cat, "-", dt]]
rows += [["TELEPHONE TYPE", "TELEPHONE NUMBER", "", "EXTENSION"]]
for ty, no in phones: rows += [[ty, no, "", "-"]]
story.append(labelled(rows, [72*mm, 46*mm, 26*mm, 36*mm], heads=[0, 2, 4]))
story += section_bar("EMPLOYMENT INFORMATION")
e = employment
story.append(labelled([["ACCOUNT TYPE", "DATE REPORTED", "OCCUPATION"], [e["account_type"], e["date_reported"], e["occupation"]],
                       ["INCOME (e)", "FREQUENCY", "INCOME INDICATOR"], [inr(e["income"]), e["frequency"], e["indicator"]]],
                      [62*mm, 60*mm, 58*mm]))
story += section_bar("ACCOUNT INFORMATION")
for a in accounts: story += account_block(a)
story += section_bar("ENQUIRY INFORMATION")
story.append(labelled([["MEMBER NAME", "DATE OF ENQUIRY", "ENQUIRY PURPOSE", "ENQUIRY AMOUNT"]] +
                      [[m, d, p, inr(amt)] for m, d, p, amt in enquiries], [52*mm, 38*mm, 54*mm, 36*mm], heads=[0]))
story.append(Spacer(1, 8))
story.append(Paragraph(f"END OF CREDIT INFORMATION REPORT FOR {person['name']}", LAB))

text_pdf = os.path.join(OUT, "synthetic_credit_report.pdf")
SimpleDocTemplate(text_pdf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=40*mm, bottomMargin=20*mm,
                  title="Synthetic credit report (test data)").build(story, onFirstPage=chrome, onLaterPages=chrome)

# protected copy
w = PdfWriter(); [w.add_page(p) for p in PdfReader(text_pdf).pages]
w.encrypt(PASSWORD, algorithm="AES-256")
with open(os.path.join(OUT, "synthetic_credit_report_protected.pdf"), "wb") as fh: w.write(fh)

# image-only copy (no text layer), like a scanned/flattened download
try:
    from pdf2image import convert_from_path
    pages = [p.convert("RGB") for p in convert_from_path(text_pdf, dpi=300)]
    pages[0].save(os.path.join(OUT, "synthetic_credit_report_image_only.pdf"), save_all=True,
                  append_images=pages[1:], resolution=300, quality=80)
except Exception as ex:
    print("image-only variant skipped:", ex)

# ------------------------------------------------------------------ ground truth
def d2iso(s): return None if not s else f"{s[6:]}-{s[3:5]}-{s[:2]}"
def emi_formula(P, annual, n):
    if annual == 0: return round(P / n)
    r = annual / 1200; return round(P * r * (1 + r) ** n / ((1 + r) ** n - 1))
half_up = lambda x: int(math.floor(x + 0.5))

DEFAULT_RATES = {"PERSONAL LOAN": 14.0, "AUTO LOAN (PERSONAL)": 9.5, "CONSUMER LOAN": 0.0}
rd = REPORT_DATE
def stale(a):  # open account not reported for > 6 months
    r = date.fromisoformat(d2iso(a["reported"]))
    return a["closed"] is None and (rd - r).days > 183

gt_acc = []
for a in accounts:
    rec = {k: a[k] for k in ["pay_start","pay_end","member","type","ownership","credit_limit","sanctioned","high_credit","balance","cash_limit",
                             "overdue","rate","tenure","emi","frequency","actual_payment","suit","wo_status","wo_total",
                             "wo_principal","settlement"]}
    rec["account_last4"] = "".join(ch for ch in a["number"] if ch.isalnum())[-4:]
    for k in ["opened","closed","last_payment","reported"]: rec[k] = d2iso(a[k])
    rec["dpd"] = a["dpd"]; rec["is_open"] = a["closed"] is None; rec["is_stale"] = stale(a)
    is_loan = a["credit_limit"] is None and a["closed"] is None
    if is_loan:
        if a["emi"]: rec["emi_used"], rec["emi_source"] = a["emi"], "reported_emi"
        elif a["actual_payment"]: rec["emi_used"], rec["emi_source"] = a["actual_payment"], "actual_payment_amount"
        else:
            rec["emi_used"] = emi_formula(a["sanctioned"], DEFAULT_RATES[a["type"]], int(a["tenure"]))
            rec["emi_source"] = f"estimated ({DEFAULT_RATES[a['type']]}% default rate, user to confirm)"
    gt_acc.append(rec)

own_open = [r for r in gt_acc if r["is_open"] and r["ownership"] == "INDIVIDUAL"]
au_open = [r for r in gt_acc if r["is_open"] and r["ownership"] != "INDIVIDUAL"]
own_cards = [r for r in own_open if r["credit_limit"]]
loans = [r for r in own_open if "emi_used" in r]
inputs = {"take_home_monthly": employment["income"] // 12, "rent": 22000, "other_fixed_expenses": 15000,
          "_note": "take-home pre-filled from employment section (annual net income / 12), user confirms"}
loan_emi = sum(r["emi_used"] for r in loans)
min_due = sum(half_up(r["balance"] * 0.05) for r in own_cards)
left = inputs["take_home_monthly"] - loan_emi - inputs["rent"] - inputs["other_fixed_expenses"]
six_mo = date(2026, 4, 10)
enq_6m = [x for x in enquiries if date.fromisoformat(d2iso(x[1])) >= six_mo]
late_12m = [(r["member"], k, val) for r in gt_acc for k, val in r["dpd"].items()
            if k >= "2025-10" and val not in ("000", "XXX", "STD", "")]

expected = {
  "score": score,
  "report_date": rd.isoformat(),
  "accounts_total": len(gt_acc), "accounts_open_own": len(own_open), "accounts_open_authorised_user": len(au_open),
  "accounts_closed": sum(1 for r in gt_acc if not r["is_open"]),
  "total_outstanding_own": sum(r["balance"] for r in own_open),
  "authorised_user_balance_excluded": sum(r["balance"] for r in au_open),
  "monthly_loan_emi": loan_emi,
  "emi_breakdown": {f"{r['member']} {r['type']}": {"emi": r["emi_used"], "source": r["emi_source"]} for r in loans},
  "income_prefill_monthly": inputs["take_home_monthly"],
  "card_min_due_5pct_own": min_due,
  "money_left_after_emi_and_fixed": left,
  "money_left_after_card_min_due": left - min_due,
  "emi_to_income_pct": round(loan_emi / inputs["take_home_monthly"] * 100, 2),
  "card_utilisation_pct_own": {f"{r['member']} {r['account_last4']}": round(r["balance"] / r["credit_limit"] * 100, 2) for r in own_cards},
  "overall_utilisation_pct_own": round(sum(r["balance"] for r in own_cards) / sum(r["credit_limit"] for r in own_cards) * 100, 2),
  "paydown_to_30pct": {f"{r['member']} {r['account_last4']}": max(0, r["balance"] - half_up(r["credit_limit"] * 0.3)) for r in own_cards},
  "enquiries_last_6_months": len(enq_6m),
  "enquiry_amounts_unreliable": True,
  "late_payments_last_12_months": late_12m,
  "red_flags": [
    "Late payment: SUNRISE AUTO FINANCE auto loan, 030 in 2026-03",
    "Settled with write-off: KAVERI SMALL FINANCE BANK personal loan (settled Rs 38,000; written off Rs 62,000; DPD reached DBT)",
    "High utilisation: LOTUS BANK card 9032 at 81.07%",
    f"Enquiry burst: {len(enq_6m)} enquiries in 6 months, 3 from one lender within 4 days",
    "Stale account: NOVA BANK card 1184 open with balance but last reported 31-01-2019 (likely error, suggest dispute)",
    "EMI not reported: SUNRISE AUTO (using actual payment amount) and ORBIT CONSUMER (estimated)",
  ],
}
gt = {"_note": "Ground truth for the synthetic report. Fictional data for parser/rules testing.",
      "pdf_password": PASSWORD, "score": score, "report_date": rd.isoformat(),
      "personal": person, "employment": employment, "accounts": gt_acc,
      "enquiries": [{"member": m, "date": d2iso(d), "purpose": p, "amount_as_printed": a} for m, d, p, a in enquiries],
      "test_inputs": inputs, "expected_insights": expected}
with open(os.path.join(OUT, "synthetic_credit_report_expected.json"), "w") as fh:
    json.dump(gt, fh, indent=2, ensure_ascii=False)
os.remove(WM)
print(json.dumps(expected, indent=2))
