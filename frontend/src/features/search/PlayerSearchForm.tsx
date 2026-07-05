import type { FormEvent } from "react";
import { Search } from "lucide-react";
import { normalizePlayerTagInput } from "../../lib/formatting";

export function PlayerSearchForm({
  tag,
  setTag,
  loading,
  onSubmit,
  goblinMode,
  setGoblinMode,
}: {
  tag: string;
  setTag: (value: string) => void;
  loading: boolean;
  onSubmit: (event: FormEvent) => void;
  goblinMode: boolean;
  setGoblinMode: (value: boolean) => void;
}) {
  return (
    <form onSubmit={onSubmit} className="mt-8 rounded-lg border border-white/10 bg-slate-950/70 p-4">
      <label htmlFor="player-tag" className="text-xs font-black uppercase text-white/55">Player tag</label>
      <div className="mt-2 flex flex-col gap-3 sm:flex-row">
        <input
          id="player-tag"
          value={tag}
          onChange={(event) => setTag(event.target.value)}
          onBlur={() => setTag(normalizePlayerTagInput(tag))}
          placeholder="#PLAYER"
          className="h-12 min-w-0 flex-1 rounded-lg border border-white/15 bg-white px-4 text-lg font-black uppercase text-slate-950 outline-none focus:border-amber-300"
        />
        <button disabled={loading} className="inline-flex h-12 items-center justify-center gap-2 rounded-lg border border-amber-300 bg-amber-300 px-5 text-sm font-black uppercase text-slate-950 transition hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-60">
          <Search size={18} /> {loading ? "Analysing" : "Expose me"}
        </button>
      </div>
      <label className="mt-4 flex items-center gap-3 text-sm font-bold text-white/70">
        <input type="checkbox" checked={goblinMode} onChange={(event) => setGoblinMode(event.target.checked)} className="h-4 w-4 accent-amber-300" />
        Goblin mode wording
      </label>
    </form>
  );
}
