// Mirrors backend/app/models.py. Regenerate from /openapi.json once the API settles.

export type Account = {
  member: string;
  type: string;
  ownership: string;
  account_last4: string;
  credit_limit: number | null;
  sanctioned: number | null;
  high_credit: number | null;
  balance: number | null;
  cash_limit: number | null;
  overdue: number | null;
  rate: string | null;
  tenure: string | null;
  emi: number | null;
  frequency: string | null;
  actual_payment: number | null;
  opened: string | null;
  closed: string | null;
  last_payment: string | null;
  reported: string | null;
  pay_start: string | null;
  pay_end: string | null;
  suit: string | null;
  wo_status: string | null;
  wo_total: number | null;
  wo_principal: number | null;
  settlement: number | null;
  dpd: Record<string, string>;
  emi_confirmed: number | null;
  notes: string[];
};

export type Enquiry = {
  member: string;
  date: string;
  purpose: string;
  amount_as_printed: number | null;
};

export type ParsedReport = {
  bureau: string;
  report_date: string;
  score: number | null;
  income_annual: number | null;
  income_frequency: string | null;
  accounts: Account[];
  enquiries: Enquiry[];
  used_ocr: boolean;
  issues: string[];
};

export type UserInputs = {
  take_home_monthly: number;
  rent: number;
  other_fixed_expenses: number;
};

export type Flag = {
  kind:
    | "late_payment"
    | "overdue"
    | "settled_written_off"
    | "suit_filed"
    | "stale_account"
    | "high_utilisation"
    | "enquiry_burst"
    | "emi_not_reported"
    | "authorised_user";
  severity: "info" | "warning" | "critical";
  message: string;
  account: string | null;
};

export type Insights = {
  rules_version: string;
  score: number | null;
  report_date: string;
  accounts_total: number;
  accounts_open_own: number;
  accounts_open_authorised_user: number;
  accounts_closed: number;
  total_outstanding_own: number;
  authorised_user_balance_excluded: number;
  monthly_loan_emi: number;
  emi_breakdown: Record<string, { emi: number | null; source: string }>;
  income_prefill_monthly: number | null;
  card_min_due_5pct_own: number;
  money_left_after_emi_and_fixed: number;
  money_left_after_card_min_due: number;
  emi_to_income_pct: number | null;
  emi_to_income_band: "healthy" | "stretched" | "high" | null;
  card_utilisation_pct_own: Record<string, number>;
  overall_utilisation_pct_own: number | null;
  paydown_to_30pct: Record<string, number>;
  enquiries_last_6_months: number;
  late_payments_last_12_months: [string, string, string][];
  flags: Flag[];
};
