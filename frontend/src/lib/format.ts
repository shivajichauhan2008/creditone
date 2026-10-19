const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

/** ₹1,23,456 — Indian digit grouping. */
export function rupees(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  const sign = n < 0 ? "−" : "";
  return `${sign}₹${inr.format(Math.abs(n))}`;
}

export function pct(n: number | null | undefined, digits = 0): string {
  if (n === null || n === undefined) return "—";
  return `${n.toFixed(digits)}%`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** '2026-03' or '2026-03-14' -> 'Mar 2026' / '14 Mar 2026' */
export function monthLabel(iso: string): string {
  const [y, m, d] = iso.split("-");
  const month = MONTHS[Number(m) - 1] ?? m;
  return d ? `${Number(d)} ${month} ${y}` : `${month} ${y}`;
}

export function titleCase(s: string): string {
  return s
    .toLowerCase()
    .replace(/\b([a-z])/g, (c) => c.toUpperCase())
    .replace(/\bEmi\b/g, "EMI");
}

/** Parse a rupee input like "1,10,000" -> 110000 */
export function toNumber(s: string): number {
  const n = Number(s.replace(/[^\d]/g, ""));
  return Number.isFinite(n) ? n : 0;
}
