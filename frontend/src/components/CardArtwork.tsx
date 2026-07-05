import { ImageOff } from "lucide-react";
import { initials } from "../lib/formatting";
import type { ReportCard } from "../features/report/reportAdapter";

export function CardArtwork({ card, compact = false }: { card: ReportCard; compact?: boolean }) {
  const size = compact ? "h-16 w-16" : "h-24 w-24";
  if (card.iconUrl) {
    return <img src={card.iconUrl} alt="" loading="lazy" className={`${size} shrink-0 rounded-lg object-contain`} />;
  }
  return (
    <div className={`${size} flex shrink-0 flex-col items-center justify-center rounded-lg border border-amber-300/25 bg-amber-300/10 text-center text-amber-100`}>
      <ImageOff size={compact ? 18 : 24} />
      <span className="mt-1 text-xs font-black">{initials(card.name) || "CARD"}</span>
    </div>
  );
}
