import type { ReactNode } from "react";

type Tone = "blue" | "gold" | "green" | "red" | "neutral";

const tones: Record<Tone, string> = {
  blue: "border-sky-300/25 bg-sky-400/10 text-sky-100",
  gold: "border-amber-300/25 bg-amber-300/10 text-amber-100",
  green: "border-emerald-300/25 bg-emerald-300/10 text-emerald-100",
  red: "border-rose-300/25 bg-rose-400/10 text-rose-100",
  neutral: "border-white/15 bg-white/10 text-white/75",
};

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: Tone }) {
  return <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-black uppercase ${tones[tone]}`}>{children}</span>;
}
