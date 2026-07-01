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

export interface GalleryStat {
  label: string;
  value: string | number | null;
  tone?: "blue" | "gold" | "red" | "green";
}

export interface CardEvidenceGalleryItem {
  id: string;
  category: string;
  title: string;
  card?: Card | null;
  card_name?: string | null;
  roast: string;
  stats: GalleryStat[];
  evidence: string[];
  confidence: Confidence;
}

export interface RoastModule {
  id: string;
  category: string;
  title: string;
  text: string;
  confidence: Confidence;
  confidence_requirement?: string;
  severity: string;
  eligibility_conditions: string[];
  required_evidence: string[];
  evidence: string[];
  linked_cards: Card[];
  score_impact?: string;
}

export interface Report {
  schema_version: string;
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
    timeline: Array<{ battleTime: string; result: string; playerCrowns: number; opponentCrowns: number; deck: string[]; eligible?: boolean }>;
    eligible_battles?: number;
    excluded_battles?: number;
  };
  deck_analysis: {
    current_deck: Card[];
    current_deck_key?: string[];
    average_elixir: number;
    composition: { troops: number; spells: number; buildings: number; unknown?: number };
    most_used_cards: Array<{ card: string; used: number; wins: number; losses: number; win_rate: number }>;
    most_common_deck: { cards: string[]; uses: number };
    recent_main_deck?: { cards: string[]; uses: number; key?: string[] };
    current_matches_recent_main_deck?: boolean;
    eligible_battle_history?: { eligible_matches: number; excluded_matches: number; note: string };
    estimated_deck_style: string;
    deck_identity_score: number;
    structural_issues?: Array<{ label: string; explanation: string }>;
    structural_issue_count?: number;
    metadata_unknown_count?: number;
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
    current_matches_recent_main_deck?: boolean;
  };
  matchup_analysis: {
    traumatic_cards: Array<{ card: string; faced: number; losses: number; wins: number; win_rate_against: number; loss_rate: number; baseline_loss_rate?: number; excess_loss_rate?: number; confidence: Confidence; evidence?: string[] }>;
    who_hurt_you: { card: string; faced: number; losses: number; win_rate_against: number; loss_rate?: number; baseline_loss_rate?: number; excess_loss_rate?: number; confidence: Confidence; evidence?: string[] } | null;
    one_match_trauma: Record<string, any> | null;
    complaint_without_proof: Record<string, any> | null;
    natural_predator: { label: string; core_cards: string[]; losses: number; matches: number; loss_rate?: number; baseline_loss_rate?: number; excess_loss_rate?: number; confidence: Confidence; evidence?: string[] };
    baseline_loss_rate?: number;
    confidence?: Confidence;
  };
  level_analysis: {
    loss_counts: { underlevelled: number; even: number; overlevelled: number };
    total_losses_with_levels?: number;
    eligible_level_matches?: number;
    meaningful_level_advantage_losses?: number;
    average_level_difference?: number;
    confidence?: Confidence;
    evidence?: string[];
    percentages: { matchmaking_conspiracy: number; fair_fight_failure: number; certified_skill_issue: number };
    overlevelled_fraud_score: number;
    tier: string;
  };
  behaviour_analysis: {
    title: string;
    classification?: string;
    eligible_battles?: number;
    excluded_battles?: number;
    unique_decks: number;
    materially_distinct_deck_cores?: number;
    same_core_percentage?: number;
    exact_same_deck_percentage: number;
    core_deck_similarity_score: number;
    major_deck_changes: number;
    post_loss_opportunities?: number;
    changes_after_losses: number;
    main_deck: string[];
    main_deck_games: number;
    main_deck_win_rate: number;
    emergency_deck_games: number;
    emergency_deck_win_rate: number;
    confidence?: Confidence;
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
  favourite_card_analysis: {
    detected?: boolean;
    favourite_card?: Card | null;
    favourite_card_name?: string | null;
    favourite_card_usage_count: number;
    favourite_card_usage_rate: number;
    favourite_card_win_rate: number;
    player_baseline_win_rate: number;
    favourite_card_performance_delta: number;
    favourite_card_confidence: Confidence;
    favourite_card_reason: string;
    is_true_single_card_favourite: boolean;
    is_full_deck_loyalist_case: boolean;
    eligible_match_count: number;
    roast?: string;
    evidence: string[];
  };
  feared_card_analysis: {
    feared_card?: Card | null;
    feared_card_name?: string | null;
    feared_card_image?: string | null;
    leading_candidate?: Card | null;
    leading_candidate_name?: string | null;
    games_against: number;
    wins_against: number;
    losses_against: number;
    loss_rate_against: number;
    baseline_loss_rate: number;
    excess_loss_rate: number;
    feared_card_confidence: Confidence;
    evidence_summary: string;
    is_insufficient_evidence: boolean;
    roast?: string;
    evidence: string[];
  };
  win_rate_verdict: {
    total_eligible_matches: number;
    wins: number;
    losses: number;
    draws: number;
    win_rate: number;
    loss_rate: number;
    close_wins: number;
    close_losses: number;
    close_game_win_rate?: number | null;
    main_deck_win_rate?: number | null;
    main_deck_games?: number | null;
    replacement_deck_win_rate?: number | null;
    replacement_deck_games?: number | null;
    confidence: Confidence;
    trend: string;
    trend_delta: number;
    band?: string;
    roast?: string;
    evidence: string[];
  };
  roast_narrative: {
    opening_charge: string;
    opening_evidence: string[];
    favourite_card_indictment: string;
    feared_card_trauma: string;
    win_rate_verdict: string;
    deck_personality: string;
    final_title: string;
    final_verdict: string;
    arc: string[];
  };
  roast_modules: RoastModule[];
  card_evidence_gallery: CardEvidenceGalleryItem[];
  fraud_score: {
    score: number;
    tier: string;
    tier_key: string;
    tier_description: string;
    headline_roast: string;
    confidence: Confidence;
    overall_confidence_note?: string;
    contributors: Array<{ label: string; group?: string; raw_candidate_points?: number; applied_points?: number; points: number; description: string; evidence: string[]; evidence_count: number; sample_size?: number; confidence?: Confidence; excluded?: boolean; roast: string }>;
    score_receipts: string[];
    group_caps?: Record<string, number>;
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
  level?: number | null;
  elixir?: number | null;
  type: string;
  rarity: string;
  traits: string[];
  icon_url?: string | null;
  iconUrls?: { medium?: string; evolutionMedium?: string };
}
