"""Tunable thresholds and defaults. Change values here, not in the rules code."""

RULES_VERSION = "2026.10.1"

# Default annual interest rates (%) used only when a loan's EMI must be estimated.
# Always shown to the user as "estimated" and confirmed on the review screen.
DEFAULT_RATES = {
    "PERSONAL LOAN": 14.0,
    "AUTO LOAN (PERSONAL)": 9.5,
    "TWO-WHEELER LOAN": 12.0,
    "HOUSING LOAN": 8.75,
    "PROPERTY LOAN": 9.5,
    "CONSUMER LOAN": 0.0,  # most consumer-durable loans are 0% EMI schemes
    "EDUCATION LOAN": 10.5,
    "GOLD LOAN": 11.0,
}
FALLBACK_RATE = 14.0

OWN_OWNERSHIP = {"INDIVIDUAL", "JOINT"}           # counted as the user's own debt
CARD_MIN_DUE_PCT = 0.05                            # typical minimum amount due
UTILISATION_LIMIT = 0.30                           # flag cards above this
EMI_TO_INCOME = {"healthy": 0.30, "stretched": 0.50}
ENQUIRY_WINDOW_MONTHS = 6
ENQUIRY_BURST_COUNT = 3
LATE_PAYMENT_WINDOW_MONTHS = 12
STALE_ACCOUNT_DAYS = 183                           # open account not reported for ~6 months
BALANCE_TRANSFER_RATE = 18.0

# Payment-history codes: numbers are days past due; the rest are asset classifications.
GOOD_CODES = {"000", "STD", "XXX", ""}
BAD_CLASSES = {"SMA", "SUB", "DBT", "LSS"}
