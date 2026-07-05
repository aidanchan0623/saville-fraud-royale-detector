import { useRef } from "react";
import { DataLimitsDisclosure } from "../features/report/DataLimitsDisclosure";
import { DeckProfile } from "../features/report/DeckProfile";
import { EvidenceSection } from "../features/report/EvidenceSection";
import { LevelContextChart } from "../features/report/LevelContextChart";
import { ReportActions } from "../features/report/ReportActions";
import { ReportHeader } from "../features/report/ReportHeader";
import { VerdictPanel } from "../features/report/VerdictPanel";
import type { ReportView } from "../features/report/reportAdapter";

export function ReportPage({ report, onReset }: { report: ReportView; onReset: () => void }) {
  const receiptsRef = useRef<HTMLDivElement | null>(null);
  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="border-b border-white/10 bg-[linear-gradient(135deg,#0f172a,#172554_48%,#3f0b1c)]">
        <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[.85fr_1.15fr] lg:px-8">
          <div>
            <ReportHeader report={report} />
            <ReportActions roast={report.score.headlineRoast} onReset={onReset} onViewReceipts={() => receiptsRef.current?.scrollIntoView({ behavior: "smooth" })} />
          </div>
          <VerdictPanel report={report} />
        </div>
      </section>
      <DeckProfile report={report} />
      <div ref={receiptsRef}>
        <EvidenceSection evidence={report.evidence} moreEvidence={report.moreEvidence} />
      </div>
      <LevelContextChart rows={report.levelChart.rows} visible={report.levelChart.visible} sampleSize={report.levelChart.sampleSize} roast={report.levelChart.roast} />
      <DataLimitsDisclosure report={report} />
    </main>
  );
}
