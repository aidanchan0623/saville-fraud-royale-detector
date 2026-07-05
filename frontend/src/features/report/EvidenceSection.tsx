import { EmptyState } from "../../components/EmptyState";
import { Section } from "../../components/Section";
import { EvidenceCard } from "./EvidenceCard";
import type { EvidenceItem } from "./reportAdapter";

export function EvidenceSection({ evidence, moreEvidence }: { evidence: EvidenceItem[]; moreEvidence: EvidenceItem[] }) {
  return (
    <Section title="Evidence">
      {evidence.length ? (
        <div className="grid gap-4 lg:grid-cols-3">
          {evidence.slice(0, 3).map((item) => <EvidenceCard key={item.id} evidence={item} />)}
        </div>
      ) : (
        <EmptyState title="No evidence cards" message="The backend did not return structured evidence for this report." />
      )}
      {moreEvidence.length > 0 && (
        <details className="mt-5 rounded-lg border border-white/10 bg-white/5 p-4">
          <summary className="cursor-pointer text-sm font-black uppercase text-white/75">More receipts</summary>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {moreEvidence.map((item) => <EvidenceCard key={item.id} evidence={item} />)}
          </div>
        </details>
      )}
    </Section>
  );
}
