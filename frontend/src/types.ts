export type Confidence = "low" | "medium" | "high";

export interface DemoVictim {
  key: string;
  label: string;
  tag: string;
  name: string;
}

export interface Roast {
  rule_id: string;
  title: string;
  text: string;
  funny_description?: string;
  plain_language_explanation?: string;
  evidence: string[];
  confidence: Confidence;
  relevant_cards: string[];
  metrics: Record<string, unknown>;
}

export interface Report {
  player_summary: {
    name: string;
    tag: string;
    arena: string;
    trophies: number;
    player_level: number;
    clan: string;
    battles_analysed: number;
  };
  battle_summary: {
    battles_analysed: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
    three_crown_wins: number;
    three_crown_losses: number;
    close_wins: number;
    close_losses: number;
    current_streak: { type: string; count: number };
    timeline: Array<{ battleTime: string; result: string; playerCrowns: number; opponentCrowns: number; deck: string[] }>;
  };
  deck_analysis: {
    current_deck: Card[];
    average_elixir: number;
    composition: { troops: number; spells: number; buildings: number };
    most_used_cards: Array<{ card: string; used: number; wins: number; losses: number; win_rate: number }>;
    most_common_deck: { cards: string[]; uses: number };
    estimated_deck_style: string;
    deck_identity_score: number;
    emotional_support_card: Record<string, any>;
    main_character: Record<string, any>;
  };
  deck_personality: {
    title: string;
    style: string;
    plain_explanation: string;
    roast: string;
    traits: Array<{ label: string; explanation: string }>;
    evidence: string[];
    confidence: Confidence;
  };
  matchup_analysis: {
    traumatic_cards: Array<{ card: string; faced: number; losses: number; wins: number; win_rate_against: number; loss_rate: number; confidence: Confidence }>;
    who_hurt_you: { card: string; faced: number; losses: number; win_rate_against: number; confidence: Confidence } | null;
    one_match_trauma: Record<string, any> | null;
    complaint_without_proof: Record<string, any> | null;
    natural_predator: { label: string; core_cards: string[]; losses: number; matches: number; confidence: Confidence };
  };
  level_analysis: {
    loss_counts: { underlevelled: number; even: number; overlevelled: number };
    percentages: { matchmaking_conspiracy: number; fair_fight_failure: number; certified_skill_issue: number };
    overlevelled_fraud_score: number;
    tier: string;
  };
  behaviour_analysis: {
    title: string;
    unique_decks: number;
    exact_same_deck_percentage: number;
    core_deck_similarity_score: number;
    major_deck_changes: number;
    changes_after_losses: number;
    main_deck: string[];
    main_deck_games: number;
    main_deck_win_rate: number;
    emergency_deck_games: number;
    emergency_deck_win_rate: number;
    evidence: string[];
  };
  clutch_analysis: {
    rating: string;
    close_wins: number;
    close_losses: number;
    three_crown_losses: number;
    three_crown_wins: number;
  };
  divorce_recommendation: Record<string, any>;
  fraud_score: {
    score: number;
    tier: string;
    tier_key: string;
    tier_description: string;
    headline_roast: string;
    confidence: Confidence;
    contributors: Array<{ label: string; points: number; description: string; evidence: string[]; evidence_count: number; roast: string }>;
    score_receipts: string[];
  };
  personality_report: {
    section_title: string;
    title: string;
    summary: string;
    traits: Array<{ label: string; value: string }>;
    diagnosis: string;
    intervention_tip: string;
    evidence: string[];
    confidence: Confidence;
    scope_note: string;
  };
  roast_report: {
    title: string;
    troll_score: number;
    score_label: string;
    headline_roast: string;
    evidence: string[];
    score_breakdown: Array<{ label: string; points: number; description?: string; evidence?: string[]; roast?: string }>;
  };
  roasts: Roast[];
  disclaimer: string;
}

export interface Card {
  name: string;
  level: number;
  elixir: number;
  type: string;
  rarity: string;
  traits: string[];
  icon_url?: string | null;
  iconUrls?: { medium?: string; evolutionMedium?: string };
}
