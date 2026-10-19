import type { Insights, ParsedReport, UserInputs } from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function readError(res: Response): Promise<ApiError> {
  let detail = `Request failed (${res.status})`;
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") detail = body.detail;
  } catch {
    /* keep the generic message */
  }
  return new ApiError(res.status, detail);
}

export async function parseReport(file: File, password?: string): Promise<ParsedReport> {
  const form = new FormData();
  form.append("file", file);
  if (password) form.append("password", password);
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/reports/parse`, { method: "POST", body: form });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }
  if (!res.ok) throw await readError(res);
  return res.json();
}

export async function getInsights(report: ParsedReport, inputs: UserInputs): Promise<Insights> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/api/insights`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ report, inputs }),
    });
  } catch {
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }
  if (!res.ok) throw await readError(res);
  return res.json();
}
