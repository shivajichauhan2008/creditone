"use client";

import Link from "next/link";
import { monthLabel, pct, rupees, titleCase } from "@/lib/format";
import { useReport } from "@/lib/store";
import type { Flag, Insights } from "@/lib/types";
import PaycheckStrip from "./PaycheckStrip";

const BAND_TEXT = {
  healthy: "Healthy: under 30% of your pay goes to EMIs.",
  stretched: "Stretched: lenders get cautious between 30% and 50%.",
  high: "High: over half your pay goes to EMIs. New loans will be hard to get.",
} as const;

type Action = { title: string; detail: string; tone: "critical" | "warning" | "info" };

/** Turn rule flags into one plain action each, most urgent first. */
function actions(ins: Insights): Action[] {
  const out: Action[] = [];
  const by = (k: Flag["kind"]) => ins.flags.filter((f) => f.kind === k);

  for (const f of by("overdue"))
    out.push({ tone: "critical", title: `Clear the overdue amount on ${titleCase(f.account ?? "")}`, detail: "Overdue balances hurt your score every month they stay unpaid. Pay this before any prepayment." });
  for (const f of by("suit_filed"))
    out.push({ tone: "critical", title: `Talk to ${titleCase(f.account ?? "the lender")} about the suit-filed status`, detail: "This needs a conversation with the lender or a lawyer; there's no quick fix." });
  if (ins.late_payments_last_12_months.length) {
    const list = ins.late_payments_last_12_months.map(([lender, month, code]) => `${titleCase(lender)}, ${lateText(code)} in ${monthLabel(month)}`);
    out.push({ tone: "critical", title: "Set up auto-debit for every EMI", detail: `Late in the last year: ${list.join("; ")}. Each on-time month from now on helps, and the effect fades over about two years.` });
  }
  for (const [card, amount] of Object.entries(ins.paydown_to_30pct)) {
    if (amount > 0)
      out.push({ tone: "warning", title: `Pay ${rupees(amount)} on your ${cardName(card)}`, detail: `It's at ${pct(ins.card_utilisation_pct_own[card])} of its limit. Bringing it under 30% is one of the fastest ways to lift your score.` });
  }
  if (by("enquiry_burst").length)
    out.push({ tone: "warning", title: "Stop applying for new loans and cards for 6 months", detail: `${ins.enquiries_last_6_months} lenders checked your report in the last 6 months. Each application lowers your score a little.` });
  for (const f of by("stale_account")) {
    const d = f.message.match(/(\d{2})-(\d{2})-(\d{4})/);
    const when = d ? monthLabel(`${d[3]}-${d[2]}-${d[1]}`) : "a long time ago";
    out.push({ tone: "warning", title: `Check your ${cardName(f.account ?? "")}`, detail: `It still shows as open with a balance, but the lender last updated it on ${when}. If you closed it, raise a dispute with the bureau and ask the lender for a closure letter.` });
  }
  for (const f of by("settled_written_off"))
    out.push({ tone: "warning", title: `Ask for a no-dues letter: ${titleCase(f.account ?? "")}`, detail: `"Settled" stays on your report for years and makes lenders cautious. If you can, pay the remaining amount and ask the lender to update the status to closed.` });
  if (by("authorised_user").length)
    out.push({ tone: "info", title: "Cards in someone else's name are kept separate", detail: "You're an authorised user on these, so they're not counted as your debt, but late payments on them can still show up for you." });
  return out;
}

function lateText(code: string): string {
  if (/^\d{3}$/.test(code)) return `${Number(code)} days late`;
  const names: Record<string, string> = { SMA: "flagged as special mention", SUB: "classed sub-standard", DBT: "classed doubtful", LSS: "classed as a loss" };
  return names[code] ?? code;
}

/** 'LOTUS BANK 9032' -> 'Lotus Bank card ending 9032' */
function cardName(label: string): string {
  const m = label.match(/^(.*?)\s+(\w{4})$/);
  return m ? `${titleCase(m[1])} card ending ${m[2]}` : titleCase(label);
}

const TONE = {
  critical: "border-l-brick",
  warning: "border-l-marigold",
  info: "border-l-slate",
};

export default function Dashboard() {
  const { report, inputs, insights: ins } = useReport();

  if (!report || !inputs || !ins) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Your plan isn&rsquo;t ready yet</h1>
        <p className="text-muted">Upload your report and check the numbers to see your plan.</p>
        <Link href="/" className="inline-block rounded-md bg-ink px-4 py-2.5 text-paper">
          Upload a report
        </Link>
      </div>
    );
  }

  const left = ins.money_left_after_card_min_due;
  const todo = actions(ins);
  const cards = Object.entries(ins.card_utilisation_pct_own);
  const loans = Object.entries(ins.emi_breakdown);

  return (
    <div className="space-y-12">
      <section className="space-y-6">
        <p className="text-sm text-muted">Report dated {monthLabel(ins.report_date)}</p>
        <h1 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
          {left >= 0 ? (
            <>
              <span className="text-leaf">{rupees(left)}</span> left each month after loans, cards and fixed costs
            </>
          ) : (
            <>
              You&rsquo;re <span className="text-brick">{rupees(-left)}</span> short each month
            </>
          )}
        </h1>
        <PaycheckStrip
          takeHome={inputs.take_home_monthly}
          emi={ins.monthly_loan_emi}
          rent={inputs.rent}
          fixed={inputs.other_fixed_expenses}
          cardDues={ins.card_min_due_5pct_own}
        />
      </section>

      <section className="grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-3">
        <Stat label="Credit score" value={ins.score ? String(ins.score) : "Not found"} note="Range 300 to 900" />
        <Stat label="You owe" value={rupees(ins.total_outstanding_own)} note={`Across ${ins.accounts_open_own} open accounts`} />
        <Stat
          label="EMIs vs pay"
          value={pct(ins.emi_to_income_pct)}
          note={ins.emi_to_income_band ? BAND_TEXT[ins.emi_to_income_band] : ""}
        />
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">What to do next</h2>
        {todo.length === 0 ? (
          <p className="text-muted">Nothing urgent. Keep paying on time and your score will keep improving.</p>
        ) : (
          <ol className="space-y-3">
            {todo.map((a) => (
              <li key={a.title} className={`rounded-md border border-line border-l-4 ${TONE[a.tone]} bg-paper p-4`}>
                <p className="font-medium">{a.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-muted">{a.detail}</p>
              </li>
            ))}
          </ol>
        )}
      </section>

      {cards.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Card usage</h2>
          <ul className="space-y-4">
            {cards.map(([name, used]) => (
              <li key={name}>
                <div className="flex justify-between text-sm">
                  <span>{cardName(name)}</span>
                  <span className={used > 30 ? "font-medium text-brick" : "text-muted"}>{pct(used)} used</span>
                </div>
                <div className="relative mt-1.5 h-2.5 rounded-full bg-panel">
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${Math.min(used, 100)}%`, background: used > 30 ? "var(--marigold)" : "var(--leaf)" }}
                  />
                  <div className="absolute inset-y-[-3px] w-px bg-ink" style={{ left: "30%" }} aria-hidden />
                </div>
              </li>
            ))}
          </ul>
          <p className="text-xs text-muted">The line marks 30%, the level to stay under.</p>
        </section>
      )}

      {loans.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-xl font-semibold">Loans</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-muted">
                <th className="py-2 font-normal">Loan</th>
                <th className="py-2 text-right font-normal">Monthly EMI</th>
              </tr>
            </thead>
            <tbody>
              {loans.map(([name, row]) => (
                <tr key={name} className="border-b border-line">
                  <td className="py-3">{titleCase(name)}</td>
                  <td className="py-3 text-right">
                    {rupees(row.emi)}
                    {row.source.startsWith("estimated") && <span className="block text-xs text-marigold">estimated</span>}
                  </td>
                </tr>
              ))}
              <tr>
                <td className="py-3 font-medium">Total</td>
                <td className="py-3 text-right font-medium">{rupees(ins.monthly_loan_emi)}</td>
              </tr>
            </tbody>
          </table>
        </section>
      )}

      <div className="flex flex-wrap gap-4 border-t border-line pt-6 text-sm">
        <Link href="/review" className="underline underline-offset-4">
          Change my numbers
        </Link>
        <Link href="/" className="underline underline-offset-4">
          Upload another report
        </Link>
      </div>
    </div>
  );
}

function Stat({ label, value, note }: { label: string; value: string; note: string }) {
  return (
    <div className="bg-paper p-4">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      <p className="mt-1 text-xs leading-relaxed text-muted">{note}</p>
    </div>
  );
}
