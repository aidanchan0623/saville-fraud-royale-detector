import { z } from "zod";

export const ConfidenceSchema = z.enum(["low", "medium", "high"]);

const CardSchema = z.object({
  name: z.string(),
  level: z.number().nullable().optional(),
  elixir: z.number().nullable().optional(),
  type: z.string().optional(),
  rarity: z.string().optional(),
  traits: z.array(z.string()).optional(),
  icon_url: z.string().nullable().optional(),
  iconUrls: z.object({
    medium: z.string().optional(),
    evolutionMedium: z.string().optional(),
  }).optional(),
}).passthrough();

const ScoreGroupSchema = z.object({
  key: z.string().optional(),
  group: z.string().optional(),
  label: z.string(),
  points: z.number(),
  applied_points: z.number().optional(),
  max_points: z.number().optional(),
  max_score: z.number().optional(),
  description: z.string().optional(),
  confidence: ConfidenceSchema.optional(),
  sample_size: z.number().optional(),
  roast: z.string().optional(),
  evidence: z.array(z.string()).optional(),
}).passthrough();

const StructuredEvidenceSchema = z.object({
  id: z.string(),
  title: z.string(),
  observation: z.string(),
  sample_size: z.number(),
  confidence: ConfidenceSchema,
  score_impact: z.number(),
  roast_key: z.string(),
  roast_text: z.string(),
  receipts: z.array(z.string()).default([]),
});

const LevelChartRowSchema = z.object({
  key: z.string(),
  label: z.string(),
  wins: z.number(),
  losses: z.number(),
  draws: z.number().default(0),
  matches: z.number(),
  win_rate: z.number(),
  average_level_difference: z.number(),
});

export const ReportSchema = z.object({
  schema_version: z.string(),
  player_summary: z.object({
    name: z.string().default("Unknown player"),
    tag: z.string().default("Unknown tag"),
    arena: z.string().optional(),
    trophies: z.number().nullable().optional(),
    clan: z.string().optional(),
    battles_analysed: z.number().default(0),
  }).passthrough(),
  battle_summary: z.object({
    battles_analysed: z.number().default(0),
    eligible_battles: z.number().optional(),
  }).passthrough(),
  deck_analysis: z.object({
    current_deck: z.array(CardSchema).default([]),
    average_elixir: z.number().default(0),
    estimated_deck_style: z.string().default("Unclassified deck style"),
    recent_main_deck: z.object({
      cards: z.array(z.string()).default([]),
      card_details: z.array(CardSchema).optional(),
      uses: z.number().default(0),
    }).partial().optional(),
    current_matches_recent_main_deck: z.boolean().optional(),
    current_exact_recent_main_deck: z.boolean().optional(),
    current_recent_shared_cards: z.number().optional(),
    eligible_battle_history: z.object({
      eligible_matches: z.number().default(0),
      excluded_matches: z.number().default(0),
      note: z.string().optional(),
    }).partial().optional(),
  }).passthrough(),
  deck_personality: z.object({
    title: z.string().default("Deck profile"),
    plain_explanation: z.string().optional(),
    roast: z.string().optional(),
    supporting_roast: z.string().optional(),
    traits: z.array(z.object({ label: z.string(), explanation: z.string() }).passthrough()).default([]),
    evidence: z.array(z.string()).default([]),
    current_deck_roast: z.object({
      headline: z.string().optional(),
      one_liner: z.string().optional(),
      main_roast: z.string().optional(),
      evidence_summary: z.string().optional(),
    }).passthrough().optional(),
    recent_main_deck_roast: z.object({
      headline: z.string().optional(),
      one_liner: z.string().optional(),
      main_roast: z.string().optional(),
    }).passthrough().nullable().optional(),
  }).passthrough(),
  level_analysis: z.object({
    level_known_sample_size: z.number().optional(),
    level_chart_visible: z.boolean().optional(),
    level_reliance_chart: z.array(LevelChartRowSchema).optional(),
    level_reliance_roast: z.string().optional(),
  }).passthrough().default({}),
  fraud_score: z.object({
    score: z.number(),
    tier: z.string(),
    tier_description: z.string().optional(),
    headline_roast: z.string().optional(),
    confidence: ConfidenceSchema,
    score_groups: z.array(ScoreGroupSchema).optional(),
    contributors: z.array(ScoreGroupSchema).optional(),
    score_receipts: z.array(z.string()).optional(),
  }).passthrough(),
  structured_evidence: z.array(StructuredEvidenceSchema).default([]),
  disclaimer: z.string().optional(),
}).passthrough();

export type ApiReport = z.infer<typeof ReportSchema>;

export function parseReportPayload(payload: unknown): ApiReport {
  const parsed = ReportSchema.safeParse(payload);
  if (!parsed.success) {
    if (import.meta.env.DEV) {
      console.warn("Report validation failed", parsed.error.flatten());
    }
    throw new Error("Report data could not be read. The backend returned an unexpected report shape.");
  }
  return parsed.data;
}
