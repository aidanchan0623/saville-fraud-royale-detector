import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState } from "../../components/EmptyState";
import { Section } from "../../components/Section";
import type { LevelChartRow } from "./reportAdapter";

export function LevelContextChart({ rows, visible, sampleSize, roast }: { rows: LevelChartRow[]; visible: boolean; sampleSize: number; roast?: string }) {
  return (
    <Section title="Level Context">
      {visible && rows.length ? (
        <div className="rounded-lg border border-white/10 bg-white/5 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-xs font-black uppercase text-white/45">Wins/losses by level-advantage bucket</div>
              <p className="mt-2 text-sm font-semibold text-white/60">Only eligible level-known standard 1v1 battles are included.</p>
            </div>
            <div className="rounded-md border border-white/10 bg-slate-950/70 px-2 py-1 text-xs font-black uppercase text-white/55">sample {sampleSize}</div>
          </div>
          <div className="mt-4 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.08)" />
                <XAxis dataKey="label" stroke="#cbd5e1" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} stroke="#94a3b8" />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const row = payload[0].payload as LevelChartRow;
                    return (
                      <div className="rounded-lg border border-white/15 bg-slate-950 p-3 text-sm shadow-2xl">
                        <div className="font-black uppercase text-white">{row.label}</div>
                        <p className="mt-1 font-semibold text-white/70">{row.matches} matches · {row.winRate}% win rate · avg level diff {row.averageLevelDifference >= 0 ? "+" : ""}{row.averageLevelDifference}</p>
                      </div>
                    );
                  }}
                />
                <Bar dataKey="wins" name="Wins" fill="#34d399" radius={[6, 6, 0, 0]} />
                <Bar dataKey="losses" name="Losses" fill="#fb7185" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          {roast && <p className="mt-4 text-lg font-black leading-7 text-emerald-50">"{roast}"</p>}
        </div>
      ) : (
        <EmptyState title="Chart withheld" message="Not enough level-known battles to make this chart worth showing." />
      )}
    </Section>
  );
}
