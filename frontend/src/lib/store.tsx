"use client";

import { createContext, useContext, useState, type ReactNode } from "react";
import type { Insights, ParsedReport, UserInputs } from "./types";

// The report lives in memory only: never in localStorage, never sent anywhere except our API.
// Refreshing the page clears it, which is deliberate for credit data.

type State = {
  report: ParsedReport | null;
  inputs: UserInputs | null;
  insights: Insights | null;
  setReport: (r: ParsedReport | null) => void;
  setInputs: (i: UserInputs | null) => void;
  setInsights: (i: Insights | null) => void;
  clear: () => void;
};

const Ctx = createContext<State | null>(null);

export function ReportProvider({ children }: { children: ReactNode }) {
  const [report, setReport] = useState<ParsedReport | null>(null);
  const [inputs, setInputs] = useState<UserInputs | null>(null);
  const [insights, setInsights] = useState<Insights | null>(null);
  const clear = () => {
    setReport(null);
    setInputs(null);
    setInsights(null);
  };
  return (
    <Ctx.Provider value={{ report, inputs, insights, setReport, setInputs, setInsights, clear }}>
      {children}
    </Ctx.Provider>
  );
}

export function useReport(): State {
  const v = useContext(Ctx);
  if (!v) throw new Error("useReport must be used inside ReportProvider");
  return v;
}
