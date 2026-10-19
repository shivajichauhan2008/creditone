"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { ApiError, parseReport } from "@/lib/api";
import { useReport } from "@/lib/store";

export default function UploadForm() {
  const router = useRouter();
  const { setReport, setInputs, setInsights } = useReport();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [password, setPassword] = useState("");
  const [needsPassword, setNeedsPassword] = useState(false);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return setError("Choose your report PDF first.");
    if (!consent) return setError("Tick the consent box so we can read your report.");
    setBusy(true);
    setError(null);
    try {
      const report = await parseReport(file, password || undefined);
      setReport(report);
      setInputs(null);
      setInsights(null);
      router.push("/review");
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setNeedsPassword(true);
        setError(
          password
            ? "That password didn't open the report. Check it and try again."
            : "This report is password-protected. Enter the password you used to download it.",
        );
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong reading the report.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-5 rounded-lg border border-line bg-panel p-5 sm:p-6">
      <div>
        <label htmlFor="report" className="block font-medium">
          Your credit report (PDF)
        </label>
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="mt-2 flex w-full items-center justify-between rounded-md border border-dashed border-slate bg-paper px-4 py-4 text-left hover:border-ink"
        >
          <span className={file ? "font-medium" : "text-muted"}>
            {file ? file.name : "Choose a PDF from your device"}
          </span>
          <span className="text-sm text-muted">{file ? "Change" : "Browse"}</span>
        </button>
        <input
          ref={fileRef}
          id="report"
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null);
            setError(null);
          }}
        />
      </div>

      <div>
        <label htmlFor="password" className="block font-medium">
          Report password <span className="font-normal text-muted">(if it has one)</span>
        </label>
        <input
          id="password"
          type="password"
          autoComplete="off"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={`mt-2 w-full rounded-md border bg-paper px-3 py-2.5 ${
            needsPassword ? "border-marigold" : "border-line"
          }`}
        />
        <p className="mt-1 text-sm text-muted">Used once to open the file, never stored.</p>
      </div>

      <label className="flex gap-3 text-sm leading-relaxed">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => setConsent(e.target.checked)}
          className="mt-1 h-4 w-4 accent-[var(--ink)]"
        />
        <span>
          I agree that CreditOne may read the loan and card details in this report to build my
          plan. The PDF is deleted as soon as it&rsquo;s read.
        </span>
      </label>

      {error && (
        <p role="alert" className="rounded-md bg-sun px-3 py-2 text-sm">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={busy}
        className="w-full rounded-md bg-ink px-4 py-3 font-medium text-paper disabled:opacity-60 sm:w-auto"
      >
        {busy ? "Reading your report…" : "Read my report"}
      </button>
      {busy && (
        <p className="text-sm text-muted">
          Scanned reports take up to a minute while we read each page.
        </p>
      )}
    </form>
  );
}
