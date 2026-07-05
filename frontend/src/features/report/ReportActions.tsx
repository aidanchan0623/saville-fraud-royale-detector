import { Copy, RotateCcw, ScrollText } from "lucide-react";
import { useState } from "react";

export function ReportActions({ roast, onReset, onViewReceipts }: { roast: string; onReset: () => void; onViewReceipts: () => void }) {
  const [copyState, setCopyState] = useState("Copy roast");

  async function copyRoast() {
    if (!navigator.clipboard) {
      setCopyState("Copy unavailable");
      return;
    }
    try {
      await navigator.clipboard.writeText(roast);
      setCopyState("Copied");
    } catch {
      setCopyState("Copy failed");
    }
  }

  const buttonClass = "inline-flex h-11 items-center justify-center gap-2 rounded-lg border px-4 text-sm font-black uppercase transition";
  return (
    <div className="mt-6 flex flex-wrap gap-3">
      <button onClick={onViewReceipts} className={`${buttonClass} border-white/15 bg-white/10 text-white hover:bg-white/15`}>
        <ScrollText size={17} /> View receipts
      </button>
      <button onClick={copyRoast} className={`${buttonClass} border-amber-300 bg-amber-300 text-slate-950 hover:bg-amber-200`}>
        <Copy size={17} /> {copyState}
      </button>
      <button onClick={onReset} className={`${buttonClass} border-rose-300/70 bg-rose-400 text-slate-950 hover:bg-rose-300`}>
        <RotateCcw size={17} /> Analyse another player
      </button>
    </div>
  );
}
