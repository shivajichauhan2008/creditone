"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { getInsights } from "@/lib/api";
import { rupees, titleCase, toNumber } from "@/lib/format";
import { useReport } from "@/lib/store";
import type { Account } from "@/lib/types";

const OWN = new Set(["INDIVIDUAL", "JOINT"]);

function sourceLabel(source: string): { text: string; needsCheck: boolean } {
  if (source === "reported_emi") return { text: "From your report", needsCheck: false };
  if (source === "actual_payment_amount") return { text: "From your last payment", needsCheck: false };
  if (source === "user_confirmed") return { text: "You confirmed this", needsCheck: false };
  if (source.startsWith("estimated")) return { text: "Estimated — please check", needsCheck: true };
  return { text: "Not in your report — please enter", needsCheck: true };
}

const key = (a: Account) => `${a.member} ${a.type}`;

function monthlyIncome(annual: number | null, frequency: string | null): number {
  return annual && frequency === "ANNUAL" ? Math.round(annual / 12) : 0;
}

export default function ReviewForm() {
  const router = useRouter();
  const { report, setReport, setInputs, setInsights } = useReport();
  const [emis, setEmis] = useState<Record<string, string>>({});
  const [sources, setSources] = useState<Record<string, string>>({});
  const [closedByUser, setClosedByUser] = useState<Record<string, boolean>>({});
  const [income, setIncome] = useState(() => {
    const monthly = monthlyIncome(report?.income_annual ?? null, report?.income_frequency ?? null);
    return monthly ? String(monthly) : "";
  });
  const [rent, setRent] = useState("");
  const [fixed, setFixed] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const openLoans = useMemo(
    () => (report?.accounts ?? []).filter((a) => !a.closed && OWN.has(a.ownership) && a.credit_limit === null),
    [report],
  );
  const openCards = useMemo(
    () => (report?.accounts ?? []).filter((a) => !a.closed && OWN.has(a.ownership) && a.credit_limit !== null),
    [report],
  );
  const others = useMemo(
    () => (report?.accounts ?? []).filter((a) => !a.closed && !OWN.has(a.ownership)),
    [report],
  );

  // Ask the rules engine for its best EMI figures so the user starts from them.
  useEffect(() => {
    if (!report) return;
    const monthly = monthlyIncome(report.income_annual, report.income_frequency);
    getInsights(report, { take_home_monthly: monthly || 1, rent: 0, other_fixed_expenses: 0 })
      .then((ins) => {
        const e: Record<string, string> = {};
        const s: Record<string, string> = {};
        for (const [k, v] of Object.entries(ins.emi_breakdown)) {
          e[k] = v.emi ? String(v.emi) : "";
          s[k] = v.source;
        }
        setEmis(e);
        setSources(s);
      })
      .catch(() => setError("Couldn't load suggested EMIs. You can still enter them yourself."));
  }, [report]);

  if (!report) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Start by uploading your report</h1>
        <p className="text-muted">
          Your report is kept only while this page is open, so refreshing clears it.
        </p>
        <Link href="/" className="inline-block rounded-md bg-ink px-4 py-2.5 text-paper">
          Upload a report
        </Link>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!report) return;
    const takeHome = toNumber(income);
    if (!takeHome) return setError("Enter your monthly take-home pay so we can work out what's left.");
    const accounts = report.accounts.map((a) => {
      const k = key(a);
      const next = { ...a };
      if (openLoans.includes(a) && emis[k] !== undefined && emis[k] !== "") next.emi_confirmed = toNumber(emis[k]);
      if (closedByUser[k]) next.closed = report.report_date;
      return next;
    });
    const confirmed = { ...report, accounts };
    const inputs = { take_home_monthly: takeHome, rent: toNumber(rent), other_fixed_expenses: toNumber(fixed) };
    setBusy(true);
    setError(null);
    try {
      const ins = await getInsights(confirmed, inputs);
      setReport(confirmed);
      setInputs(inputs);
      setInsights(ins);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't build your plan.");
    } finally {
      setBusy(false);
    }
  }

  const checks = report.issues.filter((i) => !i.startsWith("Score missing"));

  return (
    <form onSubmit={submit} className="space-y-10">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">Check a few numbers</h1>
        <p className="max-w-[60ch] leading-relaxed text-muted">
          Credit reports often leave out EMIs. We&rsquo;ve filled in the best figures we could
          find; correct anything that doesn&rsquo;t match your bank statement.
        </p>
      </section>

      {checks.length > 0 && (
        <section className="rounded-lg bg-sun p-4">
          <h2 className="font-semibold">Please double-check</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {checks.map((c) => (
              <li key={c}>{c}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Your monthly money</h2>
        <div className="grid gap-4 sm:grid-cols-3">
          <Money id="income" label="Take-home pay" hint={report.income_annual ? "Pre-filled from your report" : undefined} value={income} onChange={setIncome} />
          <Money id="rent" label="Rent or home EMI not in report" value={rent} onChange={setRent} />
          <Money id="fixed" label="Other fixed costs" hint="School fees, insurance, bills" value={fixed} onChange={setFixed} />
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold">Loans ({openLoans.length})</h2>
        {openLoans.length === 0 && <p className="text-muted">No open loans in your report.</p>}
        <ul className="divide-y divide-line rounded-lg border border-line">
          {openLoans.map((a) => {
            const k = key(a);
            const src = sourceLabel(sources[k] ?? "");
            return (
              <li key={k + a.account_last4} className="grid gap-3 p-4 sm:grid-cols-[1fr_12rem] sm:items-start">
                <div>
                  <p className="font-medium">{titleCase(a.member)}</p>
                  <p className="text-sm text-muted">
                    {titleCase(a.type)}, {rupees(a.balance)} left of {rupees(a.sanctioned)}
                  </p>
                  <label className="mt-2 flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={!!closedByUser[k]}
                      onChange={(e) => setClosedByUser({ ...closedByUser, [k]: e.target.checked })}
                      className="h-4 w-4 accent-[var(--ink)]"
                    />
                    I&rsquo;ve already closed this loan
                  </label>
                </div>
                <div>
                  <label htmlFor={`emi-${k}`} className="text-sm font-medium">
                    Monthly EMI
                  </label>
                  <input
                    id={`emi-${k}`}
                    inputMode="numeric"
                    disabled={!!closedByUser[k]}
                    value={emis[k] ?? ""}
                    onChange={(e) => setEmis({ ...emis, [k]: e.target.value })}
                    className={`mt-1 w-full rounded-md border bg-paper px-3 py-2 ${src.needsCheck ? "border-marigold" : "border-line"}`}
                  />
                  <p className={`mt-1 text-xs ${src.needsCheck ? "text-marigold" : "text-muted"}`}>{src.text}</p>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Credit cards ({openCards.length})</h2>
        <ul className="divide-y divide-line rounded-lg border border-line">
          {openCards.map((a) => (
            <li key={key(a) + a.account_last4} className="flex justify-between gap-4 p-4">
              <span>
                {titleCase(a.member)} <span className="text-muted">ending {a.account_last4}</span>
              </span>
              <span className="text-right">
                {rupees(a.balance)} <span className="text-muted">of {rupees(a.credit_limit)}</span>
              </span>
            </li>
          ))}
        </ul>
        {others.length > 0 && (
          <p className="text-sm text-muted">
            {others.length} card{others.length > 1 ? "s" : ""} where you&rsquo;re an authorised user
            {" "}won&rsquo;t be counted as your debt.
          </p>
        )}
      </section>

      {error && (
        <p role="alert" className="rounded-md bg-sun px-3 py-2 text-sm">
          {error}
        </p>
      )}

      <div className="flex flex-wrap items-center gap-4">
        <button type="submit" disabled={busy} className="rounded-md bg-ink px-5 py-3 font-medium text-paper disabled:opacity-60">
          {busy ? "Building your plan…" : "Show my plan"}
        </button>
        <Link href="/" className="text-sm underline underline-offset-4">
          Upload a different report
        </Link>
      </div>
    </form>
  );
}

function Money(props: { id: string; label: string; hint?: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label htmlFor={props.id} className="text-sm font-medium">
        {props.label}
      </label>
      <div className="mt-1 flex items-center rounded-md border border-line bg-paper focus-within:border-ink">
        <span className="pl-3 text-muted">₹</span>
        <input
          id={props.id}
          inputMode="numeric"
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          className="w-full bg-transparent px-2 py-2 outline-none"
        />
      </div>
      {props.hint && <p className="mt-1 text-xs text-muted">{props.hint}</p>}
    </div>
  );
}
