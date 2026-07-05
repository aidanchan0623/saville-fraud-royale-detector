import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

const read = (path) => readFileSync(new URL(`../${path}`, import.meta.url), "utf8");

test("malformed API response has a clear error message", () => {
  const schema = read("src/features/report/reportSchema.ts");
  const error = read("src/components/ErrorState.tsx");
  assert(schema.includes("Report data could not be read"));
  assert(error.includes("Report data could not be read"));
});

test("report page renders exactly three default evidence cards", () => {
  const adapter = read("src/features/report/reportAdapter.ts");
  const section = read("src/features/report/EvidenceSection.tsx");
  assert(adapter.includes("evidence: evidence.slice(0, 3)"));
  assert(section.includes("evidence.slice(0, 3)"));
});

test("insufficient level evidence withholds the chart", () => {
  const chart = read("src/features/report/LevelContextChart.tsx");
  assert(chart.includes("Not enough level-known battles to make this chart worth showing."));
});

test("player tag input normalizes tags", () => {
  const formatting = read("src/lib/formatting.ts");
  assert(formatting.includes("normalizePlayerTagInput"));
  assert(formatting.includes("startsWith(\"#\")"));
});

test("score reasons and evidence cards expose observation, confidence, and sample size", () => {
  const score = read("src/features/report/ScoreReasonList.tsx");
  const card = read("src/features/report/EvidenceCard.tsx");
  assert(score.includes("reason.value"));
  assert(card.includes("Observed"));
  assert(card.includes("evidence.sampleSize"));
  assert(card.includes("formatConfidence"));
});

test("copy action handles missing clipboard", () => {
  const actions = read("src/features/report/ReportActions.tsx");
  assert(actions.includes("!navigator.clipboard"));
  assert(actions.includes("Copy unavailable"));
});
