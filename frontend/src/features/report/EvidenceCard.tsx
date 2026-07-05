import { Badge } from "../../components/Badge";
import { formatConfidence } from "../../lib/formatting";
import type { EvidenceItem } from "./reportAdapter";

export function EvidenceCard({ evidence }: { evidence: EvidenceItem }) {
  return (
    <article className="rounded-lg border border-white/10 bg-white/5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <h3 className="text-lg font-black uppercase text-white">{evidence.title}</h3>
        <Badge tone={evidence.confidence === "high" ? "green" : evidence.confidence === "medium" ? "gold" : "blue"}>{formatConfidence(evidence.confidence)}</Badge>
      </div>
      <div className="mt-4 text-xs font-black uppercase text-white/45">Observed</div>
      <p className="mt-2 text-base font-semibold leading-7 text-white/80">{evidence.observation}</p>
      <div className="mt-3 text-xs font-black uppercase text-white/45">Sample size: {evidence.sampleSize} · Score impact: {evidence.scoreImpact}</div>
      <p className="mt-4 text-lg font-black leading-7 text-amber-50">"{evidence.roast}"</p>
      {evidence.receipts.length > 0 && (
        <details className="mt-4 rounded-lg border border-amber-300/20 bg-amber-300/10 p-3">
          <summary className="cursor-pointer text-sm font-black uppercase text-amber-100">View receipts</summary>
          <ul className="mt-3 space-y-2 text-sm font-semibold leading-6 text-amber-50/80">
            {evidence.receipts.map((receipt) => <li key={receipt}>- {receipt}</li>)}
          </ul>
        </details>
      )}
    </article>
  );
}
