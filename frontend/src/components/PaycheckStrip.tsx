import { rupees } from "@/lib/format";

type Part = { label: string; amount: number; color: string };

/** The month's take-home pay, split into where it goes. The green end is what's left. */
export default function PaycheckStrip({
  takeHome,
  emi,
  rent,
  fixed,
  cardDues,
}: {
  takeHome: number;
  emi: number;
  rent: number;
  fixed: number;
  cardDues: number;
}) {
  const left = takeHome - emi - rent - fixed - cardDues;
  const parts: Part[] = [
    { label: "Loan EMIs", amount: emi, color: "var(--indigo)" },
    { label: "Card minimum dues", amount: cardDues, color: "var(--marigold)" },
    { label: "Rent", amount: rent, color: "var(--slate)" },
    { label: "Other fixed costs", amount: fixed, color: "var(--mist)" },
    { label: "Left for you", amount: Math.max(0, left), color: "var(--leaf)" },
  ].filter((p) => p.amount > 0);
  const total = Math.max(takeHome, emi + rent + fixed + cardDues);

  return (
    <figure className="space-y-3">
      <div
        className="flex h-12 w-full overflow-hidden rounded-md"
        role="img"
        aria-label={parts.map((p) => `${p.label} ${rupees(p.amount)}`).join(", ")}
      >
        {parts.map((p) => (
          <div key={p.label} style={{ width: `${(p.amount / total) * 100}%`, background: p.color }} />
        ))}
      </div>
      <figcaption>
        <ul className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-3">
          {parts.map((p) => (
            <li key={p.label} className="flex items-center gap-2">
              <span className="h-3 w-3 shrink-0 rounded-sm" style={{ background: p.color }} />
              <span className="text-muted">{p.label}</span>
              <span className="ml-auto font-medium sm:ml-0">{rupees(p.amount)}</span>
            </li>
          ))}
        </ul>
        {left < 0 && (
          <p className="mt-3 text-sm font-medium text-brick">
            Your fixed payments are {rupees(-left)} more than your take-home pay.
          </p>
        )}
      </figcaption>
    </figure>
  );
}
