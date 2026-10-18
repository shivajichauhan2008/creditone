# CreditOne: credit report insights

Upload your credit report, confirm a few numbers, and get a one-screen answer: what you owe,
what you pay each month, what's left, and the exact steps to lift your score and cut interest.

Web app first (Next.js), mobile later (React Native + Expo), one FastAPI backend for both.
The full product and development plan is in [`docs/PLAN.md`](docs/PLAN.md).

## Repository layout

```
backend/            FastAPI API, report parser, OCR, rules engine, tests
  app/parsing/      unlock -> text layer or OCR -> bureau detection -> adapter -> validation
  app/rules/        deterministic rules engine (every rupee figure comes from here)
  app/config.py     thresholds and default interest rates
  tests/            parser, rules and API tests against the synthetic fixtures
fixtures/           synthetic test reports + ground-truth JSON (fictional data only)
scripts/            synthetic report generator
frontend/           Next.js web app (to be scaffolded, see frontend/README.md)
mobile/             React Native app (phase 4)
docs/               product and development plan
```

## Quick start (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
sudo apt install tesseract-ocr   # needed only for image-only reports (macOS: brew install tesseract)
pytest -q                         # 11 tests: parser (text, protected, OCR), rules, API
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

Or with Docker: `docker compose up --build` (API on port 8000, plus Postgres and Redis for later phases).

## API

| Method | Path | What it does |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| POST | `/api/reports/parse` | Multipart `file` (PDF) + optional `password`. Returns the parsed, masked report and validation issues. 401 if a password is needed or wrong, 422 for unsupported bureaus. |
| POST | `/api/insights` | JSON `{report, inputs}` where inputs = take-home, rent, other fixed expenses. Returns debt, EMI, cash flow, utilisation, pay-down amounts and flags. |

The intended flow is parse -> show the review screen (user confirms EMIs and income, sets
`emi_confirmed` on accounts) -> insights.

## How parsing works

1. **Unlock** password-protected PDFs in memory (pikepdf).
2. **Text layer check**: pages with selectable text are read directly (pdfplumber).
3. **OCR fallback** for image-only pages: Tesseract on a cleaned 300 dpi image, with a second
   restricted-alphabet pass on the payment-history grids and a sparse-text pass on account headers.
4. **Bureau detection** from page 1, then the bureau's adapter (CIBIL at launch).
5. **Validation**: dates, score range, payment-history codes, missing balances.

Personal details (name, PAN, date of birth, address, phone) are never extracted, and raw PDFs
and page images are never written to disk.

## EMI rule

Real reports usually leave EMI blank, so the engine uses: user-confirmed value, else reported EMI,
else actual payment amount, else the standard EMI formula with a default rate by loan type
(`app/config.py`). Estimates are always labelled.

## Test fixtures

`fixtures/` holds a 7-page synthetic report laid out like a real bureau report, in three forms
(text layer, image-only for OCR, password `TEST1234`), plus `synthetic_credit_report_expected.json`
with every expected field and insight. Regenerate with `python scripts/generate_synthetic_report.py`.

**Never commit real credit reports.** `real_reports/` is git-ignored for local, consented testing.

## Status

- [x] Synthetic fixtures and ground truth
- [x] Parser: text layer, password, OCR (matches ground truth exactly on the synthetic report)
- [x] Rules engine and API
- [ ] OCR tuning on real reports (score badge, grid header variants)
- [ ] Next.js web app
- [ ] Explanations layer (LLM, English and Hindi, from computed figures only)
- [ ] Experian / CRIF / Equifax adapters, cross-bureau check
