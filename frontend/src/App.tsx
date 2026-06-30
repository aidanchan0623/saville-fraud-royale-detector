import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  BadgeAlert,
  Copy,
  Crown,
  Download,
  ReceiptText,
  RotateCcw,
  Search,
  Share2,
  ShieldAlert,
  Sparkles,
  Swords,
  Trophy,
  Zap,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDemoVictims, getReport } from "./lib/api";
import type { Card, DemoVictim, Report, Roast } from "./types";

function initials(name: string) {
  return name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .replace(/[^A-Z]/gi, "")
    .slice(0, 3)
    .toUpperCase();
}

function copyText(text: string) {
  void navigator.clipboard?.writeText(text);
}

function downloadSummary(report: Report) {
  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="675" viewBox="0 0 1200 675">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#111827"/>
        <stop offset="0.55" stop-color="#1e1b4b"/>
        <stop offset="1" stop-color="#450a0a"/>
      </linearGradient>
    </defs>
    <rect width="1200" height="675" fill="url(#bg)"/>
    <rect x="70" y="70" width="1060" height="535" rx="8" fill="rgba(15,23,42,.86)" stroke="#facc15" stroke-width="4"/>
    <text x="105" y="140" fill="#facc15" font-size="34" font-family="Arial" font-weight="700">SAVILLE FRAUD ROYALE DETECTOR</text>
    <text x="105" y="215" fill="#ffffff" font-size="54" font-family="Arial" font-weight="800">${report.player_summary.name}</text>
    <text x="105" y="270" fill="#93c5fd" font-size="30" font-family="Arial">${report.player_summary.tag} - ${report.player_summary.arena}</text>
    <text x="105" y="360" fill="#ffffff" font-size="44" font-family="Arial" font-weight="800">${report.roast_report.title}</text>
    <text x="105" y="440" fill="#fb7185" font-size="82" font-family="Arial" font-weight="900">${report.roast_report.troll_score}/100</text>
    <text x="105" y="510" fill="#e5e7eb" font-size="28" font-family="Arial">${report.roast_report.score_label}</text>
    <text x="105" y="560" fill="#fef3c7" font-size="24" font-family="Arial">${report.roast_report.headline_roast.slice(0, 105)}</text>
  </svg>`;
  const blob = new Blob([svg], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${report.player_summary.name}-fraud-report.svg`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function shareReport(report: Report) {
  const text = `${report.player_summary.name}: ${report.roast_report.title} (${report.roast_report.troll_score}/100). ${report.roast_report.headline_roast}`;
  if (navigator.share) {
    void navigator.share({ title: "Saville Fraud Royale Detector", text });
  } else {
    copyText(text);
  }
}

function Button({
  children,
  onClick,
  type = "button",
  variant = "primary",
  disabled = false,
}: {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  variant?: "primary" | "ghost" | "danger";
  disabled?: boolean;
}) {
  const styles = {
    primary: "border-amber-300 bg-amber-300 text-slate-950 hover:bg-amber-200",
    ghost: "border-white/20 bg-white/10 text-white hover:bg-white/20",
    danger: "border-rose-300 bg-rose-400 text-slate-950 hover:bg-rose-300",
  };
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`inline-flex h-11 items-center justify-center gap-2 rounded-lg border px-4 text-sm font-black uppercase tracking-normal transition disabled:cursor-not-allowed disabled:opacity-50 ${styles[variant]}`}
    >
      {children}
    </button>
  );
}

function Metric({ label, value, tone = "blue" }: { label: string; value: string | number; tone?: "blue" | "gold" | "red" | "green" }) {
  const tones = {
    blue: "border-blue-300/25 bg-blue-400/10 text-blue-100",
    gold: "border-amber-300/25 bg-amber-300/10 text-amber-100",
    red: "border-rose-300/25 bg-rose-400/10 text-rose-100",
    green: "border-emerald-300/25 bg-emerald-300/10 text-emerald-100",
  };
  return (
    <div className={`rounded-lg border p-4 ${tones[tone]}`}>
      <div className="text-xs font-bold uppercase text-white/60">{label}</div>
      <div className="mt-2 text-2xl font-black text-white">{value}</div>
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: ReactNode; children: ReactNode }) {
  return (
    <section className="mx-auto w-full max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/20 bg-white/10 text-amber-200">{icon}</div>
        <h2 className="text-xl font-black uppercase text-white sm:text-2xl">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function CardToken({ card }: { card: Card | string }) {
  const name = typeof card === "string" ? card : card.name;
  const iconUrl = typeof card === "string" ? "" : card.icon_url ?? card.iconUrls?.medium ?? "";
  return (
    <div className="flex min-w-0 items-center gap-3 rounded-lg border border-white/10 bg-slate-950/55 p-2.5">
      {iconUrl ? (
        <img src={iconUrl} alt="" className="h-11 w-11 shrink-0 rounded-md object-contain" loading="lazy" />
      ) : (
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-md border border-amber-300/25 bg-amber-300/10 text-[11px] font-black text-amber-100">
          {initials(name)}
        </div>
      )}
      <div className="min-w-0">
        <div className="truncate text-sm font-extrabold text-white">{name}</div>
        {typeof card !== "string" && (
          <div className="mt-1 flex flex-wrap gap-1 text-[11px] font-bold uppercase text-white/55">
            <span>{card.elixir} elixir</span>
            <span>-</span>
            <span>{card.type}</span>
          </div>
        )}
      </div>
    </div>
  );
}

function Evidence({ evidence }: { evidence: string[] }) {
  if (!evidence?.length) return null;
  return (
    <details className="mt-4 rounded-lg border border-amber-300/25 bg-amber-300/10 p-3">
      <summary className="flex cursor-pointer items-center gap-2 text-sm font-black uppercase text-amber-100">
        <ReceiptText size={16} /> Show Receipts
      </summary>
      <ul className="mt-3 space-y-2 text-sm text-amber-50/80">
        {evidence.map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </details>
  );
}

function RoastPanel({ roast }: { roast: Roast }) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="rounded-lg border border-white/10 bg-slate-950/70 p-5 shadow-glow"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-xs font-black uppercase text-amber-200">{roast.confidence} confidence</div>
          <h3 className="mt-1 text-lg font-black uppercase text-white">{roast.title}</h3>
        </div>
        <button
          title="Copy roast"
          onClick={() => copyText(roast.text)}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-white/20 bg-white/10 text-white hover:bg-white/20"
        >
          <Copy size={16} />
        </button>
      </div>
      <p className="mt-4 text-base font-semibold leading-7 text-white/90">"{roast.text}"</p>
      {roast.relevant_cards.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {roast.relevant_cards.map((card) => (
            <span key={card} className="rounded-md border border-sky-300/25 bg-sky-400/10 px-2 py-1 text-xs font-bold text-sky-100">
              {card}
            </span>
          ))}
        </div>
      )}
      <Evidence evidence={roast.evidence} />
    </motion.article>
  );
}

function Landing({
  tag,
  setTag,
  onSubmit,
  loading,
  demos,
  onPickDemo,
  goblinMode,
  setGoblinMode,
  mockMode,
}: {
  tag: string;
  setTag: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  loading: boolean;
  demos: DemoVictim[];
  onPickDemo: (tag: string) => void;
  goblinMode: boolean;
  setGoblinMode: (value: boolean) => void;
  mockMode: boolean;
}) {
  return (
    <section className="relative min-h-screen overflow-hidden px-4 py-10 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(56,189,248,.2),transparent_32%),radial-gradient(circle_at_80%_15%,rgba(250,204,21,.18),transparent_30%),linear-gradient(135deg,#0f172a,#1e1b4b_50%,#450a0a)]" />
      <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.06)_1px,transparent_1px)] [background-size:46px_46px]" />
      {[Crown, Trophy, Swords, Zap].map((Icon, index) => (
        <motion.div
          key={index}
          animate={{ y: [0, -18, 0], rotate: [0, 7, -4, 0] }}
          transition={{ duration: 5 + index, repeat: Infinity, delay: index * 0.45 }}
          className="absolute hidden rounded-lg border border-white/10 bg-white/10 p-4 text-amber-200 backdrop-blur sm:block"
          style={{ left: `${12 + index * 22}%`, top: `${18 + (index % 2) * 18}%` }}
        >
          <Icon size={34} />
        </motion.div>
      ))}

      <div className="relative z-10 mx-auto flex min-h-[calc(100vh-5rem)] max-w-7xl items-center">
        <div className="grid w-full gap-8 lg:grid-cols-[1.05fr_.95fr] lg:items-center">
          <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }}>
            <div className="mb-5 inline-flex items-center gap-2 rounded-lg border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-sm font-black uppercase text-amber-100">
              <Sparkles size={16} /> No LLMs. Only receipts.
            </div>
            <h1 className="max-w-4xl text-5xl font-black uppercase leading-none text-white sm:text-7xl lg:text-8xl">
              Saville Fraud Royale Detector
            </h1>
            <p className="mt-6 max-w-2xl text-xl font-semibold leading-8 text-white/75">
              A statistically questionable but emotionally accurate analysis of your Clash Royale career.
            </p>
            <p className="mt-5 max-w-xl rounded-lg border border-white/10 bg-black/20 p-4 text-sm font-semibold leading-6 text-white/70">
              We analyse decks and recent battle outcomes, not actual gameplay. Unfortunately, that is already enough evidence.
            </p>
            {mockMode && (
              <p className="mt-4 max-w-xl rounded-lg border border-sky-300/30 bg-sky-400/10 p-4 text-sm font-bold leading-6 text-sky-50">
                Mock mode is active. Real player tags need `USE_MOCK_DATA=false` and a backend Clash Royale API key.
              </p>
            )}
          </motion.div>

          <motion.form
            onSubmit={onSubmit}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.08 }}
            className="rounded-lg border border-white/10 bg-slate-950/75 p-5 shadow-2xl backdrop-blur"
          >
            <label className="text-xs font-black uppercase text-white/60">Player tag</label>
            <div className="mt-2 flex flex-col gap-3 sm:flex-row">
              <input
                value={tag}
                onChange={(event) => setTag(event.target.value)}
                placeholder="#MID001"
                className="h-12 min-w-0 flex-1 rounded-lg border border-white/10 bg-white/10 px-4 text-lg font-black uppercase text-white outline-none placeholder:text-white/40 focus:border-amber-300"
              />
              <Button type="submit" disabled={loading}>
                <Search size={17} /> Expose Me
              </Button>
            </div>

            <div className="mt-5 flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/10 p-3">
              <div>
                <div className="text-sm font-black text-white">Goblin Mode</div>
                <div className="text-xs font-semibold text-white/50">Stronger roasts, same safety rails.</div>
              </div>
              <button
                type="button"
                onClick={() => setGoblinMode(!goblinMode)}
                className={`h-9 rounded-lg border px-3 text-xs font-black uppercase ${goblinMode ? "border-rose-300 bg-rose-400 text-slate-950" : "border-white/20 bg-white/10 text-white"}`}
              >
                {goblinMode ? "On" : "Off"}
              </button>
            </div>

            {demos.length > 0 && (
              <div className="mt-6">
                <div className="mb-3 text-xs font-black uppercase text-white/60">Choose demo victim</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {demos.map((demo) => (
                    <button
                      type="button"
                      key={demo.key}
                      onClick={() => onPickDemo(demo.tag)}
                      className="rounded-lg border border-white/10 bg-white/10 p-3 text-left transition hover:border-amber-300/60 hover:bg-amber-300/10"
                    >
                      <div className="text-sm font-black text-white">{demo.label}</div>
                      <div className="mt-1 text-xs font-semibold text-white/50">{demo.tag} - {demo.name}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </motion.form>
        </div>
      </div>
    </section>
  );
}

function ReportDashboard({ report, onReset }: { report: Report; onReset: () => void }) {
  const traumaData = report.matchup_analysis.traumatic_cards.slice(0, 6).map((item) => ({
    card: item.card,
    lossRate: item.loss_rate,
    faced: item.faced,
  }));
  const usedData = report.deck_analysis.most_used_cards.slice(0, 7).map((item) => ({
    card: item.card,
    used: item.used,
    winRate: item.win_rate,
  }));
  const contributorData = report.fraud_score.contributors.map((item) => ({
    label: item.label,
    points: item.points,
  }));
  const levelData = [
    {
      name: "Loss type",
      Underlevelled: report.level_analysis.loss_counts.underlevelled,
      "Even level": report.level_analysis.loss_counts.even,
      Overlevelled: report.level_analysis.loss_counts.overlevelled,
    },
  ];
  const trendData = report.battle_summary.timeline.slice(0, 12).reverse().map((battle, index) => ({
    match: index + 1,
    result: battle.result === "win" ? 1 : battle.result === "loss" ? -1 : 0,
    crowns: `${battle.playerCrowns}-${battle.opponentCrowns}`,
  }));

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="relative overflow-hidden border-b border-white/10 bg-[linear-gradient(135deg,#0f172a,#172554_48%,#3f0b1c)]">
        <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.08)_1px,transparent_1px)] [background-size:44px_44px]" />
        <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-lg border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-sm font-black uppercase text-amber-100">
                <Crown size={16} /> Hero Verdict
              </div>
              <h1 className="text-4xl font-black uppercase leading-tight sm:text-6xl">{report.player_summary.name}</h1>
              <div className="mt-4 flex flex-wrap gap-2 text-sm font-bold text-white/70">
                <span>{report.player_summary.tag}</span><span>-</span>
                <span>{report.player_summary.arena}</span><span>-</span>
                <span>{report.player_summary.clan}</span>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button onClick={() => shareReport(report)} variant="ghost"><Share2 size={17} /> Share</Button>
              <Button onClick={() => copyText(report.fraud_score.headline_roast)} variant="ghost"><Copy size={17} /> Copy Roast</Button>
              <Button onClick={() => downloadSummary(report)} variant="ghost"><Download size={17} /> Download</Button>
              <Button onClick={onReset} variant="danger"><RotateCcw size={17} /> Another Player</Button>
            </div>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-[.95fr_1.05fr]">
            <div className="rounded-lg border border-white/10 bg-slate-950/70 p-5">
              <div className="text-xs font-black uppercase text-white/50">Verdict</div>
              <h2 className="mt-2 text-3xl font-black uppercase leading-tight text-white">{report.personality_report.title}</h2>
              <p className="mt-4 text-lg font-semibold leading-8 text-white/80">{report.personality_report.summary}</p>
              <Evidence evidence={report.personality_report.evidence} />
            </div>

            <div className="rounded-lg border border-amber-300/30 bg-slate-950/80 p-6 shadow-glow">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="text-xs font-black uppercase text-amber-200">Fraud Score</div>
                  <div className="mt-2 text-7xl font-black leading-none text-rose-300 sm:text-8xl">{report.fraud_score.score}<span className="text-3xl text-white/55">/100</span></div>
                </div>
                <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-right">
                  <div className="text-xs font-black uppercase text-white/50">Confidence</div>
                  <div className="text-lg font-black uppercase text-emerald-200">{report.fraud_score.confidence}</div>
                </div>
              </div>
              <div className="mt-5 h-4 overflow-hidden rounded-full bg-white/10">
                <div className="h-full bg-gradient-to-r from-emerald-300 via-amber-300 to-rose-400" style={{ width: `${report.fraud_score.score}%` }} />
              </div>
              <h3 className="mt-5 text-3xl font-black uppercase text-white">{report.fraud_score.tier}</h3>
              <p className="mt-2 text-sm font-semibold leading-6 text-white/70">{report.fraud_score.tier_description}</p>
              <p className="mt-4 text-xl font-black leading-8 text-amber-100">"{report.fraud_score.headline_roast}"</p>
              <div className="mt-5 space-y-3">
                {report.fraud_score.contributors.slice(0, 5).map((item) => (
                  <div key={item.label} className="rounded-lg border border-white/10 bg-white/5 p-3">
                    <div className="flex items-center justify-between gap-4">
                      <div className="font-black text-white">{item.label}</div>
                      <div className="text-lg font-black text-rose-300">+{item.points}</div>
                    </div>
                    <p className="mt-1 text-sm font-semibold leading-6 text-white/60">{item.description}</p>
                  </div>
                ))}
              </div>
              <details className="mt-5 rounded-lg border border-amber-300/25 bg-amber-300/10 p-3">
                <summary className="cursor-pointer text-sm font-black uppercase text-amber-100">Show Score Receipts</summary>
                <ul className="mt-3 space-y-2 text-sm text-amber-50/80">
                  {report.fraud_score.score_receipts.map((item) => <li key={item}>- {item}</li>)}
                </ul>
              </details>
            </div>
          </div>
        </div>
      </section>

      <Section title={report.personality_report.section_title} icon={<Sparkles size={20} />}>
        <div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-black uppercase text-white/50">Overall Personality Summary</div>
            <h2 className="mt-2 text-3xl font-black uppercase text-white">{report.personality_report.title}</h2>
            <p className="mt-4 text-lg font-semibold leading-8 text-white/80">{report.personality_report.summary}</p>
            <div className="mt-5 rounded-lg border border-sky-300/20 bg-sky-400/10 p-4">
              <div className="text-sm font-black uppercase text-sky-100">Final Diagnosis</div>
              <p className="mt-2 text-xl font-black text-white">{report.personality_report.diagnosis}</p>
              <p className="mt-3 text-sm font-semibold leading-6 text-sky-50/80">{report.personality_report.scope_note}</p>
            </div>
          </div>
          <div className="space-y-3">
            {report.personality_report.traits.map((trait) => (
              <div key={trait.label} className="rounded-lg border border-white/10 bg-slate-950/60 p-4">
                <div className="text-xs font-black uppercase text-white/50">{trait.label}</div>
                <div className="mt-2 text-xl font-black text-white">{trait.value}</div>
              </div>
            ))}
            <div className="rounded-lg border border-amber-300/25 bg-amber-300/10 p-4">
              <div className="text-xs font-black uppercase text-amber-100">Recommended Intervention</div>
              <p className="mt-2 text-lg font-black leading-7 text-white">{report.personality_report.intervention_tip}</p>
            </div>
          </div>
        </div>
      </Section>

      <Section title="Deck Personality" icon={<BadgeAlert size={20} />}>
        <div className="grid gap-5 lg:grid-cols-[.92fr_1.08fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-black uppercase text-white/50">Deck Style Estimate</div>
            <h2 className="mt-2 text-4xl font-black uppercase text-white">{report.deck_personality.title}</h2>
            <p className="mt-4 text-base font-semibold leading-7 text-white/70">{report.deck_personality.plain_explanation}</p>
            <p className="mt-4 rounded-lg border border-rose-300/20 bg-rose-400/10 p-4 text-lg font-black leading-7 text-rose-50">"{report.deck_personality.roast}"</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              {report.deck_personality.traits.map((trait) => (
                <div key={trait.label} className="rounded-lg border border-white/10 bg-slate-950/60 p-3">
                  <div className="font-black text-white">{trait.label}</div>
                  <p className="mt-1 text-sm font-semibold leading-6 text-white/60">{trait.explanation}</p>
                </div>
              ))}
            </div>
            <Evidence evidence={report.deck_personality.evidence} />
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="grid gap-3 sm:grid-cols-4">
              <Metric label="Avg Elixir" value={report.deck_analysis.average_elixir} tone="gold" />
              <Metric label="Troops" value={report.deck_analysis.composition.troops} tone="blue" />
              <Metric label="Spells" value={report.deck_analysis.composition.spells} tone="red" />
              <Metric label="Buildings" value={report.deck_analysis.composition.buildings} tone="green" />
            </div>
            <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
              {report.deck_analysis.current_deck.map((card) => <CardToken key={card.name} card={card} />)}
            </div>
          </div>
        </div>
      </Section>

      <Section title="Matchup Trauma" icon={<ShieldAlert size={20} />}>
        <div className="grid gap-5 lg:grid-cols-[.9fr_1.1fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-black uppercase text-rose-200">Who hurt you?</div>
            <h3 className="mt-2 text-4xl font-black uppercase text-white">{report.matchup_analysis.who_hurt_you?.card ?? "No clear suspect"}</h3>
            {report.matchup_analysis.who_hurt_you && (
              <div className="mt-5 grid gap-3 sm:grid-cols-2">
                <Metric label="Faced" value={report.matchup_analysis.who_hurt_you.faced} tone="blue" />
                <Metric label="Lost" value={report.matchup_analysis.who_hurt_you.losses} tone="red" />
                <Metric label="Win Rate Against" value={`${report.matchup_analysis.who_hurt_you.win_rate_against}%`} tone="gold" />
                <Metric label="Confidence" value={report.matchup_analysis.who_hurt_you.confidence} tone="green" />
              </div>
            )}
            <div className="mt-6 border-t border-white/10 pt-5">
              <div className="text-xs font-black uppercase text-sky-200">Natural Predator</div>
              <div className="mt-2 text-2xl font-black uppercase text-white">{report.matchup_analysis.natural_predator.label}</div>
              <p className="mt-2 text-sm font-semibold leading-6 text-white/60">Lost {report.matchup_analysis.natural_predator.losses} of {report.matchup_analysis.natural_predator.matches} recent battles against this detected card core.</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {report.matchup_analysis.natural_predator.core_cards.map((card) => <CardToken key={card} card={card} />)}
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <h3 className="text-lg font-black uppercase text-white">Opponent cards appearing in losses</h3>
            <p className="mt-1 text-sm font-semibold text-white/55">Shows which opponent cards appear most often in losses, with sample-size confidence kept visible.</p>
            <div className="mt-4 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={traumaData} layout="vertical" margin={{ left: 18, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.08)" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="card" type="category" width={120} stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="lossRate" name="Loss rate %" fill="#fb7185" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </Section>

      <Section title="Behaviour Patterns" icon={<Zap size={20} />}>
        <div className="grid gap-5 lg:grid-cols-[1.1fr_.9fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <h3 className="text-2xl font-black uppercase text-white">{report.behaviour_analysis.title}</h3>
            <p className="mt-2 text-sm font-semibold leading-6 text-white/60">Deck-change behaviour is measured by comparing sequential battle decks. A panic switch means at least three cards changed after a loss.</p>
            <div className="mt-5 grid gap-3 sm:grid-cols-4">
              <Metric label="Unique Decks" value={report.behaviour_analysis.unique_decks} tone="blue" />
              <Metric label="Post-Loss Changes" value={report.behaviour_analysis.changes_after_losses} tone="red" />
              <Metric label="Main Deck WR" value={`${report.behaviour_analysis.main_deck_win_rate}%`} tone="gold" />
              <Metric label="Core Similarity" value={`${report.behaviour_analysis.core_deck_similarity_score}%`} tone="green" />
            </div>
            <Evidence evidence={report.behaviour_analysis.evidence} />
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-black uppercase text-white/50">Overlevelled Fraud Score</div>
            <div className="mt-2 text-6xl font-black text-rose-300">{report.level_analysis.overlevelled_fraud_score}%</div>
            <div className="mt-2 text-lg font-black uppercase text-white">{report.level_analysis.tier}</div>
            <p className="mt-3 text-sm font-semibold leading-6 text-white/60">Measures losses where your average card level was materially higher than the opponent's. It is a joke metric, not proof that you are actually bad.</p>
            <div className="mt-5 h-4 overflow-hidden rounded-full bg-white/10">
              <div className="h-full bg-rose-400" style={{ width: `${report.level_analysis.overlevelled_fraud_score}%` }} />
            </div>
          </div>
        </div>
      </Section>

      <Section title="Supporting Evidence" icon={<Swords size={20} />}>
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <h3 className="text-lg font-black uppercase text-white">Fraud Score Contributors</h3>
            <p className="mt-1 text-sm font-semibold text-white/55">Shows which rule-based factors added the most to the total Fraud Score.</p>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={contributorData} layout="vertical" margin={{ left: 18, right: 20 }}>
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="label" type="category" width={122} stroke="#94a3b8" tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="points" fill="#facc15" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <h3 className="text-lg font-black uppercase text-white">Loss Type Breakdown</h3>
            <p className="mt-1 text-sm font-semibold text-white/55">Shows whether level disadvantage explains losses, or whether the cards did their part and the result still went sideways.</p>
            <div className="mt-4 h-52">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={levelData} layout="vertical">
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis type="category" dataKey="name" width={70} stroke="#94a3b8" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="Underlevelled" stackId="a" fill="#60a5fa" />
                  <Bar dataKey="Even level" stackId="a" fill="#facc15" />
                  <Bar dataKey="Overlevelled" stackId="a" fill="#fb7185" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <h3 className="text-lg font-black uppercase text-white">Most-Used Cards</h3>
            <p className="mt-1 text-sm font-semibold text-white/55">Shows which cards appear most in recent player decks and whether they are returning value.</p>
            <div className="mt-4 h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={usedData} layout="vertical" margin={{ left: 18, right: 20 }}>
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="card" type="category" width={100} stroke="#94a3b8" tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Bar dataKey="used" fill="#38bdf8" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        <div className="mt-5 rounded-lg border border-white/10 bg-white/5 p-5">
          <h3 className="text-lg font-black uppercase text-white">Recent Match Trend</h3>
          <p className="mt-1 text-sm font-semibold text-white/55">Win is +1, draw is 0, loss is -1. This keeps the trend readable without pretending to know replay details.</p>
          <div className="mt-4 grid gap-2 sm:grid-cols-6 lg:grid-cols-12">
            {trendData.map((battle) => (
              <div key={battle.match} className={`rounded-lg border p-3 text-center ${battle.result > 0 ? "border-emerald-300/25 bg-emerald-300/10" : battle.result < 0 ? "border-rose-300/25 bg-rose-400/10" : "border-sky-300/25 bg-sky-400/10"}`}>
                <div className="text-xs font-black uppercase text-white/50">#{battle.match}</div>
                <div className="mt-1 text-sm font-black text-white">{battle.result > 0 ? "Win" : battle.result < 0 ? "Loss" : "Draw"}</div>
                <div className="mt-1 text-xs font-semibold text-white/55">{battle.crowns}</div>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section title="Final Verdict" icon={<Trophy size={20} />}>
        <div className="rounded-lg border border-amber-300/25 bg-[linear-gradient(135deg,rgba(15,23,42,.92),rgba(76,5,25,.64))] p-6 shadow-glow">
          <div className="grid gap-6 lg:grid-cols-[1fr_.9fr]">
            <div>
              <div className="text-xs font-black uppercase text-amber-100">Final Verdict</div>
              <h2 className="mt-2 text-4xl font-black uppercase leading-tight text-white">{report.fraud_score.tier}</h2>
              <p className="mt-4 text-xl font-black leading-8 text-amber-50">"{report.fraud_score.headline_roast}"</p>
              <p className="mt-4 text-sm font-semibold leading-6 text-white/60">{report.disclaimer}</p>
            </div>
            <div className="rounded-lg border border-white/10 bg-slate-950/60 p-5">
              <div className="text-xs font-black uppercase text-white/50">Recommended Intervention</div>
              <p className="mt-2 text-2xl font-black leading-8 text-white">{report.personality_report.intervention_tip}</p>
              <div className="mt-5 text-xs font-black uppercase text-white/50">Most Damning Evidence</div>
              <ul className="mt-3 space-y-2 text-sm font-semibold text-white/70">
                {report.fraud_score.contributors.slice(0, 3).map((item) => <li key={item.label}>+{item.points}: {item.label}</li>)}
              </ul>
              <Evidence evidence={report.fraud_score.score_receipts} />
            </div>
          </div>
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {report.roasts.slice(0, 4).map((roast) => <RoastPanel key={`${roast.rule_id}-${roast.title}`} roast={roast} />)}
        </div>
      </Section>
    </main>
  );
}

export default function App() {
  const [tag, setTag] = useState("#MID001");
  const [goblinMode, setGoblinMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [demos, setDemos] = useState<DemoVictim[]>([]);
  const [mockMode, setMockMode] = useState(true);
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    getDemoVictims()
      .then((payload) => {
        setMockMode(payload.mock_mode);
        setDemos(payload.victims);
      })
      .catch(() => setDemos([]));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      setReport(await getReport(tag, goblinMode));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Report failed.");
    } finally {
      setLoading(false);
    }
  }

  function pickDemo(nextTag: string) {
    setTag(nextTag);
  }

  if (report) {
    return <ReportDashboard report={report} onReset={() => setReport(null)} />;
  }

  return (
    <div className="min-h-screen bg-slate-950">
      <Landing
        tag={tag}
        setTag={setTag}
        onSubmit={submit}
        loading={loading}
        demos={demos}
        onPickDemo={pickDemo}
        goblinMode={goblinMode}
        setGoblinMode={setGoblinMode}
        mockMode={mockMode}
      />
      {error && (
        <div className="fixed bottom-5 left-1/2 z-50 w-[min(92vw,720px)] -translate-x-1/2 rounded-lg border border-rose-300/40 bg-rose-950/90 p-4 text-sm font-bold text-rose-50 shadow-2xl">
          {error}
        </div>
      )}
    </div>
  );
}
