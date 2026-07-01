import type { DemoVictim, Report } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail ?? "The report machine tripped over its own cape.");
  }
  return body as T;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function assertReportPayload(payload: unknown): Report {
  if (!isRecord(payload)) {
    throw new Error("Backend returned an invalid report payload.");
  }

  const requiredObjects = ["player_summary", "battle_summary", "deck_analysis", "fraud_score", "personality_report", "deck_personality", "roast_report"];
  const missing = requiredObjects.filter((key) => !isRecord(payload[key]));
  if (missing.length) {
    if (import.meta.env.DEV) {
      console.warn("Malformed report payload missing top-level sections", { missing, payload });
    }
    throw new Error(`Backend returned an outdated report payload missing: ${missing.join(", ")}. Restart the backend or refresh the report.`);
  }

  if (!Array.isArray(payload.roasts)) {
    if (import.meta.env.DEV) {
      console.warn("Malformed report payload missing roasts array", payload);
    }
    throw new Error("Backend returned an invalid report payload missing roasts.");
  }

  return payload as unknown as Report;
}

export async function getDemoVictims(): Promise<{ mock_mode: boolean; victims: DemoVictim[] }> {
  return readJson(await fetch(`${API_BASE}/api/demo-victims`));
}

export async function getReport(tag: string, goblinMode: boolean): Promise<Report> {
  const encodedTag = encodeURIComponent(tag);
  const url = `${API_BASE}/api/reports/${encodedTag}?goblin_mode=${goblinMode}&seed=saville`;
  return assertReportPayload(await readJson<unknown>(await fetch(url)));
}
