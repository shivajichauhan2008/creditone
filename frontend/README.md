# Web app (Next.js)

Three screens, all client-side state (the report is held in memory only and cleared on refresh):

1. **Upload** (`/`): PDF picker, password field, consent. A 401 from the API turns into a password prompt.
2. **Review** (`/review`): pre-filled take-home pay (from the report's income when present),
   rent and fixed costs; each open loan's EMI with where it came from (report, last payment,
   or estimate highlighted for checking); "I've already closed this loan"; cards and
   authorised-user cards.
3. **Dashboard** (`/dashboard`): money left this month, a pay-cheque strip showing where the salary
   goes, score / debt / EMI-to-pay, a ranked "What to do next" list built from the rules engine's
   flags, card usage against the 30% line, and the loan table.

## Run

```bash
cp .env.example .env.local      # NEXT_PUBLIC_API_URL, default http://localhost:8000
npm install
npm run dev                     # http://localhost:3000 (start the backend first)
```

`npm run build && npm run lint` must pass; CI runs both.

## Notes

- Next.js 16 with the App Router. Read `node_modules/next/dist/docs/` before changing framework
  code: APIs differ from older versions (see `AGENTS.md`).
- Font: IBM Plex Sans via `@fontsource` (self-hosted, no Google Fonts request at build time).
- Colour tokens are in `src/app/globals.css`: green is reserved for money left, brick red for
  things that hurt the score, marigold for card dues and anything to check.
- Types in `src/lib/types.ts` mirror `backend/app/models.py`; replace with an OpenAPI-generated
  client once the API settles.
