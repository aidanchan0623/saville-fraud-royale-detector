import { Crown } from "lucide-react";
import { Badge } from "../../components/Badge";
import { formatNumber, initials } from "../../lib/formatting";
import type { ReportView } from "./reportAdapter";

export function ReportHeader({ report }: { report: ReportView }) {
  return (
    <div className="flex items-center gap-4">
      <div className="flex h-20 w-20 items-center justify-center rounded-lg border border-amber-300/25 bg-amber-300/10 text-2xl font-black text-amber-100">
        {initials(report.player.name) || <Crown size={26} />}
      </div>
      <div className="min-w-0">
        <h2 className="truncate text-3xl font-black uppercase text-white">{report.player.name}</h2>
        <div className="mt-2 flex flex-wrap gap-2 text-sm font-bold text-white/60">
          <span>{report.player.tag}</span>
          {report.player.trophies !== undefined && report.player.trophies !== null && <span>{formatNumber(report.player.trophies)} trophies</span>}
          {report.player.arena && <span>{report.player.arena}</span>}
        </div>
        <div className="mt-3"><Badge tone="neutral">{report.player.matchesAnalysed} matches analysed</Badge></div>
      </div>
    </div>
  );
}
