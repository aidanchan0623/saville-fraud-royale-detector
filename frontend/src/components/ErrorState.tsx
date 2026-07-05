import { X } from "lucide-react";

export function ErrorState({ message, onDismiss }: { message: string; onDismiss?: () => void }) {
  return (
    <div className="fixed bottom-5 left-1/2 z-50 w-[min(92vw,720px)] -translate-x-1/2 rounded-lg border border-rose-300/40 bg-rose-950/95 p-4 text-sm font-bold text-rose-50 shadow-2xl">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-black uppercase text-rose-200">Report data could not be read</div>
          <p className="mt-1 leading-6">{message}</p>
        </div>
        {onDismiss && (
          <button aria-label="Dismiss error" onClick={onDismiss} className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-white/15 bg-white/10">
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  );
}
