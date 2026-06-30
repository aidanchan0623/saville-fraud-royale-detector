import type { DemoVictim, Report } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function readJson<T>(response: Response): Promise<T> {
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(body.detail ?? "The report machine tripped over its own cape.");
  }
  return body as T;
}

export async function getDemoVictims(): Promise<{ mock_mode: boolean; victims: DemoVictim[] }> {
  return readJson(await fetch(`${API_BASE}/api/demo-victims`));
}

export async function getReport(tag: string, goblinMode: boolean): Promise<Report> {
  const encodedTag = encodeURIComponent(tag);
  const url = `${API_BASE}/api/reports/${encodedTag}?goblin_mode=${goblinMode}&seed=saville`;
  return readJson(await fetch(url));
}

