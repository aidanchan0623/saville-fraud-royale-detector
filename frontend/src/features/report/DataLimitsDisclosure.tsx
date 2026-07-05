import type { ReportView } from "./reportAdapter";

export function DataLimitsDisclosure({ report }: { report: ReportView }) {
  return (
    <footer className="mx-auto w-full max-w-6xl px-4 pb-10 sm:px-6 lg:px-8">
      <details className="rounded-lg border border-white/10 bg-slate-950/70 p-4">
        <summary className="cursor-pointer text-sm font-black uppercase text-white/70">How this works / data limits</summary>
        <div className="mt-3 space-y-2 text-sm font-semibold leading-6 text-white/55">
          <p>Fraud Score is an entertainment index based on deck traits, recent battle-log evidence, level context, and recurring matchup patterns. It is not a skill rating or cheating detector.</p>
          <p>Battle log data cannot see card placements, timing, elixir use, card-cast counts, or exact decisions.</p>
          <p>No LLMs. Only deterministic rules and local template receipts.</p>
          <p>Report schema: {report.schemaVersion}</p>
        </div>
      </details>
    </footer>
  );
}
