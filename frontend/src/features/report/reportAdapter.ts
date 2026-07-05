import type { ApiReport } from "./reportSchema";

export type Confidence = "low" | "medium" | "high";

export interface ReportCard {
  name: string;
  iconUrl?: string;
  elixir?: number | null;
  type?: string;
  traits: string[];
}

export interface ScoreReason {
  id: string;
  label: string;
  value: number;
  max: number;
  confidence: Confidence;
  sampleSize: number;
  description: string;
}

export interface EvidenceItem {
  id: string;
  title: string;
  observation: string;
  sampleSize: number;
  confidence: Confidence;
  scoreImpact: number;
  roast: string;
  receipts: string[];
}

export interface LevelChartRow {
  key: string;
  label: string;
  wins: number;
  losses: number;
  draws: number;
  matches: number;
  winRate: number;
  averageLevelDifference: number;
}

export interface ReportView {
  schemaVersion: string;
  goblinMode: boolean;
  player: {
    name: string;
    tag: string;
    arena?: string;
    trophies?: number | null;
    clan?: string;
    matchesAnalysed: number;
    eligibleMatches: number;
  };
  score: {
    value: number;
    tier: string;
    description: string;
    confidence: Confidence;
    headlineRoast: string;
    reasons: ScoreReason[];
  };
  deck: {
    cards: ReportCard[];
    archetype: string;
    averageElixir: number;
    traits: Array<{ label: string; explanation: string }>;
    uses?: number;
    eligibleMatches: number;
    roast: string;
    receipts: string[];
    recentMainNote?: string;
  };
  evidence: EvidenceItem[];
  moreEvidence: EvidenceItem[];
  levelChart: {
    sampleSize: number;
    visible: boolean;
    rows: LevelChartRow[];
    roast?: string;
  };
  receipts: string[];
  disclaimer: string;
}

function cardFromApi(card: ApiReport["deck_analysis"]["current_deck"][number]): ReportCard {
  return {
    name: card.name,
    iconUrl: card.icon_url ?? card.iconUrls?.medium ?? card.iconUrls?.evolutionMedium,
    elixir: card.elixir,
    type: card.type,
    traits: card.traits ?? [],
  };
}

function scoreReasonFromGroup(group: NonNullable<ApiReport["fraud_score"]["score_groups"]>[number], index: number): ScoreReason {
  return {
    id: group.key ?? group.group ?? `score-${index}`,
    label: group.label.replace("Community Meme Deck Score", "Deck meme exposure").replace("Performance / Loss Score", "Loss-pattern evidence").replace("Level-Reliance Score", "Level context"),
    value: group.applied_points ?? group.points,
    max: group.max_points ?? group.max_score ?? 100,
    confidence: group.confidence ?? "low",
    sampleSize: group.sample_size ?? 0,
    description: group.description ?? "Evidence-backed score reason.",
  };
}

function evidenceFromApi(item: ApiReport["structured_evidence"][number]): EvidenceItem {
  return {
    id: item.id,
    title: item.title,
    observation: item.observation,
    sampleSize: item.sample_size,
    confidence: item.confidence,
    scoreImpact: item.score_impact,
    roast: item.roast_text,
    receipts: item.receipts,
  };
}

export function toReportView(report: ApiReport, goblinMode: boolean): ReportView {
  const scoreGroups = report.fraud_score.score_groups?.length ? report.fraud_score.score_groups : report.fraud_score.contributors ?? [];
  const evidence = report.structured_evidence.map(evidenceFromApi);
  const deckRoast = report.deck_personality.current_deck_roast;
  const eligibleMatches = report.deck_analysis.eligible_battle_history?.eligible_matches ?? report.battle_summary.eligible_battles ?? report.battle_summary.battles_analysed;
  const recentMainUses = report.deck_analysis.recent_main_deck?.uses;
  const deckChanged = report.deck_analysis.current_matches_recent_main_deck === false && (report.deck_analysis.current_recent_shared_cards ?? 8) < 6;

  return {
    schemaVersion: report.schema_version,
    goblinMode,
    player: {
      name: report.player_summary.name,
      tag: report.player_summary.tag,
      arena: report.player_summary.arena,
      trophies: report.player_summary.trophies,
      clan: report.player_summary.clan,
      matchesAnalysed: report.battle_summary.battles_analysed,
      eligibleMatches,
    },
    score: {
      value: Math.max(0, Math.min(100, report.fraud_score.score)),
      tier: report.fraud_score.tier,
      description: report.fraud_score.tier_description ?? "Entertainment index based on deterministic report evidence.",
      confidence: report.fraud_score.confidence,
      headlineRoast: evidence[0]?.roast ?? report.fraud_score.headline_roast ?? "The receipts are quieter than usual.",
      reasons: scoreGroups.slice(0, 3).map(scoreReasonFromGroup),
    },
    deck: {
      cards: report.deck_analysis.current_deck.map(cardFromApi),
      archetype: report.deck_analysis.estimated_deck_style,
      averageElixir: report.deck_analysis.average_elixir,
      traits: report.deck_personality.traits,
      uses: recentMainUses,
      eligibleMatches,
      roast: deckRoast?.main_roast ?? report.deck_personality.roast ?? "The deck profile was readable, but the roast filed late.",
      receipts: report.deck_personality.evidence,
      recentMainNote: deckChanged ? "Recent main deck differs materially from the current deck, so historical deck receipts may describe the previous list." : undefined,
    },
    evidence: evidence.slice(0, 3),
    moreEvidence: evidence.slice(3),
    levelChart: {
      sampleSize: report.level_analysis.level_known_sample_size ?? 0,
      visible: Boolean(report.level_analysis.level_chart_visible && (report.level_analysis.level_known_sample_size ?? 0) >= 5),
      rows: (report.level_analysis.level_reliance_chart ?? []).map((row) => ({
        key: row.key,
        label: row.label,
        wins: row.wins,
        losses: row.losses,
        draws: row.draws,
        matches: row.matches,
        winRate: row.win_rate,
        averageLevelDifference: row.average_level_difference,
      })),
      roast: report.level_analysis.level_reliance_roast,
    },
    receipts: report.fraud_score.score_receipts ?? [],
    disclaimer: report.disclaimer ?? "This is an entertainment report, not a skill rating or cheating detector.",
  };
}
