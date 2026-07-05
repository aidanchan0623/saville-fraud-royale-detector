import { Badge } from "../../components/Badge";
import { formatConfidence } from "../../lib/formatting";
import { ScoreReasonList } from "./ScoreReasonList";
import type { ReportView } from "./reportAdapter";

export function VerdictPanel({ report }: { report: ReportView }) {
  return (
    <div className="rounded-lg border border-amber-300/25 bg-slate-950/80 p-6 shadow-2xl">
      <div className="flex flex-wrap items-start justify-between gap-5">
        <div>
          <div className="text-xs font-black uppercase text-amber-200">Fraud Score</div>
          <div className="mt-2 text-7xl font-black leading-none text-rose-300">{report.score.value}<span className="text-3xl text-white/45">/100</span></div>
          <p className="mt-2 text-sm font-bold text-white/55">{formatConfidence(report.score.confidence)} confidence · {report.player.eligibleMatches} eligible battles analysed</p>
        </div>
        <Badge tone={report.score.confidence === "high" ? "green" : report.score.confidence === "medium" ? "gold" : "blue"}>{formatConfidence(report.score.confidence)}</Badge>
      </div>
      <h1 className="mt-6 text-4xl font-black uppercase leading-tight text-white">{report.score.tier}</h1>
      <p className="mt-3 text-sm font-semibold leading-6 text-white/60">{report.score.description}</p>
      <p className="mt-5 text-2xl font-black leading-9 text-amber-50">"{report.score.headlineRoast}"</p>
      <ScoreReasonList reasons={report.score.reasons} />
    </div>
  );
}
