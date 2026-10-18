# Credit Report Insights App — Development Plan

Snapshot of the living plan doc (Oct 18, 2026). The editable version lives in Claude as a doc;
update both when decisions change.

## Product summary

A user uploads their own credit report PDF, adds take-home income and fixed expenses, and gets a
one-screen answer: what they owe, what they pay each month, what's left, and the exact steps to
lift their score and cut interest.

- **Who it's for:** salaried Indians aged 25–45 with 2+ active loans or cards who feel stretched.
- **Core promise:** "Upload your report, get a personal debt and score plan in 60 seconds."
- **Edge over free score apps:** a real cash-flow picture, a ranked payoff plan with rupee savings,
  and help disputing report errors.
- **Platform order:** responsive web app first, then React Native on the same backend.

## MVP scope (web)

| Area | In the MVP | Later |
| --- | --- | --- |
| Input | CIBIL PDF upload with password unlock; income, rent and fixed-expense form | Bank statement upload, Account Aggregator, other bureaus |
| Review | Extracted accounts for confirmation; user edits missing or wrong EMIs | Auto-detect closed loans still shown as active |
| Dashboard | Debt summary, monthly EMI, money left, EMI-to-income, card utilisation, red flags | Month-on-month tracking across re-uploads |
| Plans | Score-improvement actions; prepay order with interest saved | Balance-transfer and consolidation offers from partners |
| Language | English + Hindi explanations | Regional languages |
| Account | Phone OTP login, delete-my-data | Family profiles |
| Output | Shareable PDF summary | Reminders and alerts |

Out of scope: fetching reports from the bureau directly, investment advice, loan offers.

## Architecture

Pipeline: Upload → Unlock (in memory) → Extract (text layer or OCR, then block parser) →
Validate → User confirms → Rules engine (every rupee figure) → Explain (LLM, from figures only) → Dashboard.

| Layer | Choice | Why |
| --- | --- | --- |
| Web frontend | Next.js + Tailwind | Existing stack; SEO for landing pages |
| Mobile (phase 4) | React Native + Expo | Reuses React skills and the same API |
| API | FastAPI, Pydantic, OpenAPI client for both apps | One contract for web and mobile |
| Jobs | Redis + RQ or Celery | Parsing 5–20 s, OCR up to a minute |
| PDF unlock | pikepdf | Password-protected reports |
| Text-layer check | pdfplumber; no text → OCR | Real downloads can be image-only |
| OCR | Self-hosted Tesseract (PaddleOCR later); vision LLM only as fallback | Page images never leave our servers |
| Extraction | Block parser keyed on fixed labels; LLM with strict JSON schema as fallback | Labels are stable when layout shifts |
| Validation | Counts, balances, dates, DPD codes | Catch errors before the user sees them |
| Rules engine | Plain Python, unit-tested | Deterministic, auditable figures |
| Explanations | LLM writes English/Hindi from computed figures only | No hallucinated numbers |
| Storage | PostgreSQL for extracted data only | Privacy by design |
| Auth | Phone OTP | Expected by Indian users |
| Hosting | Docker, India region | Financial data stays in India |

**Multi-bureau design.** Every report is converted into the same internal model; a detector routes
page 1 to a per-bureau adapter. Launch ships CIBIL only.

## Data model

| Table | Key fields |
| --- | --- |
| users | id, phone, language, consent_at, deleted_at |
| reports | id, user_id, bureau, report_date, score, parse_status, parser_version |
| accounts | lender, type, ownership, account_last4, dates (opened, closed, last payment, last reported), sanctioned, credit_limit, high_credit, cash_limit, balance, overdue, rate, tenure, frequency, emi_reported, actual_payment, emi_estimated, emi_confirmed, emi_source, suit_filed, written-off status/amounts, settlement |
| payment_history | account_id, month, dpd (000–999 or STD, SMA, SUB, DBT, LSS, XXX) |
| enquiries | report_id, lender, purpose, date, amount (unreliable, never used in rules) |
| user_finances | take_home (pre-filled from report income when present), rent, other_fixed |
| insights | report_id, kind, severity, payload_json, rules_version |

Drop PAN, full account numbers, address and date of birth at extraction time.

## Insight logic

- **EMI order:** user-confirmed → reported EMI → actual payment amount → formula with default rate
  by loan type (always labelled "estimated").
- **Total outstanding:** own open accounts only; authorised-user cards shown separately.
- **Money left** = take-home − EMIs − rent − other fixed. **EMI-to-income:** <30% healthy,
  30–50% stretched, >50% high.

| Rule | Trigger | Action |
| --- | --- | --- |
| Card utilisation | Own card or all own cards > 30% | "Pay ₹X on card Y to drop below 30%" |
| Missed payments | DPD > 000 or SMA/SUB/DBT/LSS in 12 months | Auto-debit; recovery timeline |
| Overdue now | overdue > 0 | Clear before prepaying anything |
| Settled / written-off | Status or amounts present | Impact; how to get a no-dues letter |
| Suit filed | Field present | Legal or lender contact |
| Enquiry burst | 3+ in 6 months (by date) | Pause applications 6 months |
| Stale account | Open, not reported 6+ months | Likely error; dispute guide |
| Authorised-user card | Ownership | Show separately |

**Savings plan:** avalanche order; balance-transfer flag above 18%.
**Cross-bureau check (phase 4):** missing accounts, mismatched balances or late payments, score gaps > 50.

## Security, privacy and compliance

Raw PDF and password in memory only; field minimisation; encryption; DPDP Act consent, privacy
notice in English and Hindi, delete-my-data, grievance contact; OCR on our servers, LLM sees only
masked extracted fields; no bureau pull; debt and budgeting guidance only (no investment advice);
estimates labelled; never use bureau or bank logos.

## Roadmap (part-time, ~15 h/week)

| Phase | Weeks | Scope |
| --- | --- | --- |
| 0 Foundations | 1–2 | Repo, CI, Docker, Postgres, Redis, OTP login, upload + unlock, fixtures in tests |
| 1 Parser + rules | 3–6 | Text-layer check and OCR path; block parser + LLM fallback; rules engine |
| 2 Web MVP | 7–10 | Confirm screen, dashboard, score plan, Hindi, PDF summary, consent, security review |
| Gate A | | Synthetic tests pass; security checklist done |
| 3 Beta + payments | 11–14 | 20–30 real users, open beta, Experian adapter, UPI checkout, price test |
| Gate B | | 100 reports, 90%+ parse success, people paying |
| 4 Mobile | 15–20 | React Native app; CRIF and Equifax adapters; cross-bureau check |

## Monetisation

Beta free → free summary + paid full plan (one-time, roughly ₹99–199) → re-upload subscription →
lender and card referrals once formal partnerships exist. Low-cost channels: Hindi/English
"how to read your CIBIL report" videos, SEO pages, own network, HR financial-wellness partnerships.

## Risks and open questions

| Risk | Mitigation |
| --- | --- |
| Real layouts differ | Masked real samples in beta; LLM fallback; validation |
| Wrong EMI estimates | Label estimates; mandatory confirm step |
| Users won't pay | Lead with cash-flow and payoff plan; test price early |
| Data breach | No raw storage, minimisation, encryption, India hosting |
| Regulated advice | Debt and budgeting only; legal review before offers |
| Moonlighting conflict | Check employment contract |

- [x] Bureaus: CIBIL at launch; Experian in phase 3; CRIF and Equifax in phase 4
- [ ] LLM provider with zero data retention
- [ ] Brand name and domain
- [ ] Free vs paid split
- [ ] Masked real samples of Experian, CRIF and Equifax reports
