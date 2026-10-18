# Web app (Next.js) — phase 2

Scaffold with:

```bash
npx create-next-app@latest . --ts --tailwind --app --eslint
```

Planned screens:

1. **Upload**: PDF picker, password field, consent checkbox (purpose-specific, English and Hindi).
2. **Review**: extracted accounts; user confirms or edits EMIs (estimated values highlighted),
   marks loans that are actually closed, confirms income (pre-filled from the report when present).
3. **Dashboard**: total owed, monthly EMI, money left, EMI-to-income band, card utilisation,
   red flags with one-line actions, pay-down amounts, score-improvement plan.
4. **Settings**: language, delete-my-data.

API: `POST /api/reports/parse` then `POST /api/insights` (see the root README).
Generate a typed client from the backend's OpenAPI schema at `http://localhost:8000/openapi.json`.
