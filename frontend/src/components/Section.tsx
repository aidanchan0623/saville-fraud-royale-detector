import type { ReactNode } from "react";

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <h2 className="text-xl font-black uppercase tracking-normal text-white sm:text-2xl">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}
