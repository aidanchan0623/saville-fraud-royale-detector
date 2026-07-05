import { parseReportPayload, type ApiReport } from "../features/report/reportSchema";
import type { DemoVictim } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function readJson(response: Response): Promise<unknown> {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body === "object" && body && "detail" in body ? String((body as { detail?: unknown }).detail) : "The report machine tripped over its own cape.";
    throw new Error(detail);
  }
  return body;
}

export async function getDemoVictims(): Promise<{ mock_mode: boolean; victims: DemoVictim[] }> {
  const payload = await readJson(await fetch(`${API_BASE}/api/demo-victims`));
  if (typeof payload !== "object" || payload === null || !Array.isArray((payload as { victims?: unknown }).victims)) {
    return { mock_mode: true, victims: [] };
  }
  return payload as { mock_mode: boolean; victims: DemoVictim[] };
}

export async function getReport(tag: string, goblinMode: boolean): Promise<ApiReport> {
  const encodedTag = encodeURIComponent(tag);
  const url = `${API_BASE}/api/reports/${encodedTag}?goblin_mode=${goblinMode}&seed=saville`;
  return parseReportPayload(await readJson(await fetch(url)));
}
