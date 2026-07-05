export function EmptyState({ title, message }: { title: string; message: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-5 text-sm font-semibold leading-6 text-white/65">
      <div className="font-black uppercase text-white">{title}</div>
      <p className="mt-2">{message}</p>
    </div>
  );
}
