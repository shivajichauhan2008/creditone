import UploadForm from "@/components/UploadForm";

export default function Home() {
  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
          What does your credit report mean for this month&rsquo;s salary?
        </h1>
        <p className="max-w-[60ch] text-lg leading-relaxed text-muted">
          Upload your CIBIL report. In about a minute you&rsquo;ll see what you owe, how much goes
          to EMIs, what&rsquo;s left after fixed costs, and the specific steps that will lift your
          score.
        </p>
      </section>

      <UploadForm />

      <section className="grid gap-6 border-t border-line pt-8 sm:grid-cols-3">
        <div>
          <h2 className="font-semibold">Where to get your report</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">
            Every Indian can download one free full report a year from each credit bureau. Use
            the PDF exactly as downloaded.
          </p>
        </div>
        <div>
          <h2 className="font-semibold">What we keep</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">
            Only the loan and card figures needed for your plan. Your name, PAN, address and phone
            number are never read into our system.
          </p>
        </div>
        <div>
          <h2 className="font-semibold">What we don&rsquo;t do</h2>
          <p className="mt-1 text-sm leading-relaxed text-muted">
            We don&rsquo;t pull your report from a bureau, sell your data, or show loan offers.
          </p>
        </div>
      </section>
    </div>
  );
}
