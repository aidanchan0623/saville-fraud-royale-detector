import { CardArtwork } from "../../components/CardArtwork";
import { Section } from "../../components/Section";
import type { ReportView } from "./reportAdapter";

export function DeckProfile({ report }: { report: ReportView }) {
  return (
    <Section title="Current Deck">
      <div className="rounded-lg border border-white/10 bg-white/5 p-5">
        <div className="grid gap-6 lg:grid-cols-[1fr_.85fr]">
          <div>
            <div className="grid grid-cols-4 gap-3 sm:grid-cols-8 lg:grid-cols-4 xl:grid-cols-8">
              {report.deck.cards.map((card) => (
                <div key={card.name} className="min-w-0 text-center">
                  <CardArtwork card={card} compact />
                  <div className="mt-2 truncate text-xs font-black text-white">{card.name}</div>
                </div>
              ))}
            </div>
            {report.deck.recentMainNote && (
              <p className="mt-4 rounded-lg border border-sky-300/20 bg-sky-400/10 p-3 text-sm font-semibold leading-6 text-sky-50">{report.deck.recentMainNote}</p>
            )}
          </div>
          <div>
            <div className="text-xs font-black uppercase text-white/45">Archetype</div>
            <h3 className="mt-2 text-2xl font-black uppercase text-white">{report.deck.archetype}</h3>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <Metric label="Average elixir" value={report.deck.averageElixir.toFixed(1)} />
              <Metric label="Usage" value={report.deck.uses !== undefined ? `${report.deck.uses} of ${report.deck.eligibleMatches}` : "Not available"} />
            </div>
            <div className="mt-4 space-y-2">
              {report.deck.traits.slice(0, 3).map((trait) => (
                <div key={trait.label} className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                  <div className="font-black text-white">{trait.label}</div>
                  <p className="mt-1 text-sm font-semibold leading-5 text-white/55">{trait.explanation}</p>
                </div>
              ))}
            </div>
            <p className="mt-5 text-lg font-black leading-7 text-amber-50">"{report.deck.roast}"</p>
            <Receipts receipts={report.deck.receipts} />
          </div>
        </div>
      </div>
    </Section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
      <div className="text-xs font-black uppercase text-white/45">{label}</div>
      <div className="mt-1 text-xl font-black text-white">{value}</div>
    </div>
  );
}

function Receipts({ receipts }: { receipts: string[] }) {
  if (!receipts.length) return null;
  return (
    <details className="mt-4 rounded-lg border border-amber-300/20 bg-amber-300/10 p-3">
      <summary className="cursor-pointer text-sm font-black uppercase text-amber-100">View deck receipts</summary>
      <ul className="mt-3 space-y-2 text-sm font-semibold leading-6 text-amber-50/80">
        {receipts.slice(0, 8).map((receipt) => <li key={receipt}>- {receipt}</li>)}
      </ul>
    </details>
  );
}
