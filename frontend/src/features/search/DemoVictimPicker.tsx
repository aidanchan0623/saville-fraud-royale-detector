import type { DemoVictim } from "../../types";

export function DemoVictimPicker({ demos, onPick }: { demos: DemoVictim[]; onPick: (tag: string) => void }) {
  if (!demos.length) return null;
  return (
    <div className="mt-5">
      <div className="text-xs font-black uppercase text-white/45">Demo victims</div>
      <div className="mt-3 flex flex-wrap gap-2">
        {demos.map((demo) => (
          <button
            key={demo.key}
            onClick={() => onPick(demo.tag)}
            className="rounded-lg border border-white/15 bg-white/8 px-3 py-2 text-left text-sm font-black text-white transition hover:border-amber-300/60 hover:bg-amber-300/10"
          >
            <span className="block text-amber-100">{demo.label}</span>
            <span className="text-xs text-white/45">{demo.tag}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
