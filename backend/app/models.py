"""API and domain models. Bureau-agnostic: every adapter produces a ParsedReport."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class Account(BaseModel):
    member: str
    type: str
    ownership: str
    account_last4: str = ""
    credit_limit: Optional[int] = None
    sanctioned: Optional[int] = None
    high_credit: Optional[int] = None
    balance: Optional[int] = None
    cash_limit: Optional[int] = None
    overdue: Optional[int] = None
    rate: Optional[str] = None
    tenure: Optional[str] = None
    emi: Optional[int] = None
    frequency: Optional[str] = None
    actual_payment: Optional[int] = None
    opened: Optional[date] = None
    closed: Optional[date] = None
    last_payment: Optional[date] = None
    reported: Optional[date] = None
    pay_start: Optional[date] = None
    pay_end: Optional[date] = None
    suit: Optional[str] = None
    wo_status: Optional[str] = None
    wo_total: Optional[int] = None
    wo_principal: Optional[int] = None
    settlement: Optional[int] = None
    dpd: dict[str, str] = Field(default_factory=dict, description="'YYYY-MM' -> code")
    emi_confirmed: Optional[int] = Field(None, description="value the user confirmed on the review screen")

    @property
    def is_open(self) -> bool:
        return self.closed is None

    @property
    def is_card(self) -> bool:
        return self.credit_limit is not None


class Enquiry(BaseModel):
    member: str
    date: date
    purpose: str
    amount_as_printed: Optional[int] = None  # often a placeholder; never used in rules


class ParsedReport(BaseModel):
    bureau: str
    report_date: date
    score: Optional[int] = None
    income_annual: Optional[int] = None
    income_frequency: Optional[str] = None
    accounts: list[Account]
    enquiries: list[Enquiry]
    used_ocr: bool = False
    issues: list[str] = Field(default_factory=list, description="validation warnings")


class UserInputs(BaseModel):
    take_home_monthly: int
    rent: int = 0
    other_fixed_expenses: int = 0


class Flag(BaseModel):
    kind: str
    severity: str  # info | warning | critical
    message: str
    account: Optional[str] = None


class InsightsRequest(BaseModel):
    report: ParsedReport
    inputs: UserInputs
