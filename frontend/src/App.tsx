import { type FormEvent, useEffect, useState } from "react";
import { ErrorState } from "./components/ErrorState";
import { LandingPage } from "./pages/LandingPage";
import { ReportPage } from "./pages/ReportPage";
import { getDemoVictims, getReport } from "./lib/api";
import { normalizePlayerTagInput } from "./lib/formatting";
import { toReportView, type ReportView } from "./features/report/reportAdapter";
import type { DemoVictim } from "./types";

export default function App() {
  const [tag, setTag] = useState("#MID001");
  const [goblinMode, setGoblinMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [demos, setDemos] = useState<DemoVictim[]>([]);
  const [mockMode, setMockMode] = useState(true);
  const [report, setReport] = useState<ReportView | null>(null);

  useEffect(() => {
    getDemoVictims()
      .then((payload) => {
        setMockMode(payload.mock_mode);
        setDemos(payload.victims);
      })
      .catch(() => setDemos([]));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const apiReport = await getReport(normalizePlayerTagInput(tag), goblinMode);
      setReport(toReportView(apiReport, goblinMode));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Report failed.");
    } finally {
      setLoading(false);
    }
  }

  if (report) {
    return <ReportPage report={report} onReset={() => setReport(null)} />;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <LandingPage
        tag={tag}
        setTag={setTag}
        goblinMode={goblinMode}
        setGoblinMode={setGoblinMode}
        loading={loading}
        demos={demos}
        mockMode={mockMode}
        onSubmit={submit}
      />
      {error && <ErrorState message={error} onDismiss={() => setError("")} />}
    </div>
  );
}
