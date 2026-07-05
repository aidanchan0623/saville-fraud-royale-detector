import type { FormEvent } from "react";
import { ReceiptText } from "lucide-react";
import { DemoVictimPicker } from "../features/search/DemoVictimPicker";
import { PlayerSearchForm } from "../features/search/PlayerSearchForm";
import type { DemoVictim } from "../types";

export function LandingPage({
  tag,
  setTag,
  goblinMode,
  setGoblinMode,
  loading,
  demos,
  mockMode,
  onSubmit,
}: {
  tag: string;
  setTag: (value: string) => void;
  goblinMode: boolean;
  setGoblinMode: (value: boolean) => void;
  loading: boolean;
  demos: DemoVictim[];
  mockMode: boolean;
  onSubmit: (event: FormEvent) => void;
}) {
  return (
    <main className="min-h-screen bg-[linear-gradient(135deg,#0f172a,#172554_48%,#3f0b1c)] px-4 py-10 text-white">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-3xl items-center">
        <div className="w-full">
          <div className="inline-flex items-center gap-2 rounded-lg border border-amber-300/25 bg-amber-300/10 px-3 py-2 text-sm font-black uppercase text-amber-100">
            <ReceiptText size={16} /> No LLMs. Only receipts.
          </div>
          <h1 className="mt-5 text-5xl font-black uppercase leading-tight sm:text-7xl">Saville Fraud Royale Detector</h1>
          <p className="mt-4 max-w-2xl text-lg font-semibold leading-8 text-white/72">A rule-based deck autopsy built from battle-log receipts.</p>
          <PlayerSearchForm tag={tag} setTag={setTag} loading={loading} onSubmit={onSubmit} goblinMode={goblinMode} setGoblinMode={setGoblinMode} />
          <DemoVictimPicker demos={demos} onPick={setTag} />
          <p className="mt-5 text-sm font-semibold leading-6 text-white/50">
            {mockMode ? "Mock mode is active. Demo victims use local generated battle logs." : "Real API mode is active. The frontend never receives the API key."}
            {" "}Battle logs cannot show placements, timing, elixir use, or exact decisions.
          </p>
        </div>
      </div>
    </main>
  );
}
