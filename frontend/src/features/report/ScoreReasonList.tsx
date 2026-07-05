import { formatConfidence } from "../../lib/formatting";
import type { ScoreReason } from "./reportAdapter";

export function ScoreReasonList({ reasons }: { reasons: ScoreReason[] }) {
  return (
    <div className="mt-6 space-y-3">
      <div className="text-xs font-black uppercase text-white/45">Built from</div>
      {reasons.slice(0, 3).map((reason) => (
        <div key={reason.id} className="flex items-start justify-between gap-4 rounded-lg border border-white/10 bg-white/5 p-3">
          <div>
            <div className="font-black text-white">{reason.label}</div>
            <p className="mt-1 text-sm font-semibold leading-5 text-white/55">{reason.description}</p>
            <div className="mt-2 text-xs font-black uppercase text-white/40">{formatConfidence(reason.confidence)} confidence · sample {reason.sampleSize}</div>
          </div>
          <div className="shrink-0 text-right text-xl font-black text-amber-100">{reason.value}/{reason.max}</div>
        </div>
      ))}
    </div>
  );
}
