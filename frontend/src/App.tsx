import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  BadgeAlert,
  Copy,
  Crown,
  Download,
  Flame,
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
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDemoVictims, getReport } from "./lib/api";
import type { Card, DemoVictim, Report, Roast } from "./types";

const resultColors: Record<string, string> = {
  Wins: "#4ade80",
  Losses: "#fb7185",
  Draws: "#60a5fa",
};

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
  return (
    <div className="flex min-w-0 items-center gap-2 rounded-lg border border-white/10 bg-slate-950/50 p-2">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-amber-300 via-sky-300 to-rose-400 text-[11px] font-black text-slate-950">
        {initials(name)}
      </div>
      <div className="min-w-0">
        <div className="truncate text-sm font-extrabold text-white">{name}</div>
        {typeof card !== "string" && <div className="text-xs text-white/50">{card.elixir} elixir - {card.type}</div>}
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
}: {
  tag: string;
  setTag: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  loading: boolean;
  demos: DemoVictim[];
  onPickDemo: (tag: string) => void;
  goblinMode: boolean;
  setGoblinMode: (value: boolean) => void;
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
  const pieData = useMemo(
    () => [
      { name: "Wins", value: report.battle_summary.wins },
      { name: "Losses", value: report.battle_summary.losses },
      { name: "Draws", value: report.battle_summary.draws },
    ],
    [report],
  );
  const traumaData = report.matchup_analysis.traumatic_cards.slice(0, 7).map((item) => ({
    card: item.card,
    winRate: item.win_rate_against,
    lossRate: item.loss_rate,
  }));
  const usedData = report.deck_analysis.most_used_cards.slice(0, 8).map((item) => ({
    card: item.card,
    used: item.used,
    winRate: item.win_rate,
  }));
  const levelData = [
    {
      name: "Losses",
      Underlevelled: report.level_analysis.loss_counts.underlevelled,
      Even: report.level_analysis.loss_counts.even,
      Overlevelled: report.level_analysis.loss_counts.overlevelled,
    },
  ];

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <section className="relative overflow-hidden border-b border-white/10 bg-[linear-gradient(135deg,#0f172a,#172554_42%,#4c0519)]">
        <div className="absolute inset-0 opacity-35 [background-image:linear-gradient(rgba(255,255,255,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.08)_1px,transparent_1px)] [background-size:42px_42px]" />
        <div className="relative mx-auto grid max-w-7xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[1.1fr_.9fr] lg:px-8">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-lg border border-amber-300/30 bg-amber-300/10 px-3 py-2 text-sm font-black uppercase text-amber-100">
              <Crown size={16} /> Player Report
            </div>
            <h1 className="text-4xl font-black uppercase leading-tight sm:text-6xl">{report.player_summary.name}</h1>
            <div className="mt-4 flex flex-wrap gap-2 text-sm font-bold text-white/70">
              <span>{report.player_summary.tag}</span>
              <span>-</span>
              <span>{report.player_summary.arena}</span>
              <span>-</span>
              <span>{report.player_summary.clan}</span>
            </div>
            <div className="mt-7 grid gap-3 sm:grid-cols-4">
              <Metric label="Trophies" value={report.player_summary.trophies} tone="gold" />
              <Metric label="Level" value={report.player_summary.player_level} tone="blue" />
              <Metric label="Battles" value={report.player_summary.battles_analysed} tone="green" />
              <Metric label="Win Rate" value={`${report.battle_summary.win_rate}%`} tone={report.battle_summary.win_rate >= 50 ? "green" : "red"} />
            </div>
          </div>

          <div className="rounded-lg border border-amber-300/25 bg-slate-950/75 p-5 shadow-glow">
            <div className="text-xs font-black uppercase text-amber-200">Title</div>
            <h2 className="mt-2 text-3xl font-black uppercase leading-tight text-white">{report.roast_report.title}</h2>
            <div className="mt-6 flex items-end gap-4">
              <div className="text-7xl font-black text-rose-300">{report.roast_report.troll_score}</div>
              <div className="pb-3 text-2xl font-black text-white/60">/ 100</div>
            </div>
            <div className="mt-3 h-3 overflow-hidden rounded-full bg-white/10">
              <div className="h-full bg-gradient-to-r from-emerald-300 via-amber-300 to-rose-400" style={{ width: `${report.roast_report.troll_score}%` }} />
            </div>
            <p className="mt-5 text-lg font-semibold leading-7 text-white/80">"{report.roast_report.headline_roast}"</p>
            <Evidence evidence={report.roast_report.evidence} />
            <div className="mt-5 flex flex-wrap gap-3">
              <Button onClick={() => shareReport(report)} variant="ghost"><Share2 size={17} /> Share</Button>
              <Button onClick={() => copyText(report.roast_report.headline_roast)} variant="ghost"><Copy size={17} /> Copy Roast</Button>
              <Button onClick={() => downloadSummary(report)} variant="ghost"><Download size={17} /> Download Image</Button>
              <Button onClick={onReset} variant="danger"><RotateCcw size={17} /> Expose Another</Button>
            </div>
          </div>
        </div>
      </section>

      <Section title="Immediate Roast" icon={<Flame size={20} />}>
        <div className="grid gap-4 lg:grid-cols-2">
          {report.roasts.slice(0, 4).map((roast) => <RoastPanel key={`${roast.rule_id}-${roast.title}`} roast={roast} />)}
        </div>
      </Section>

      <Section title="Battle Summary" icon={<Swords size={20} />}>
        <div className="grid gap-4 lg:grid-cols-[.85fr_1.15fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={104} paddingAngle={4}>
                  {pieData.map((entry) => <Cell key={entry.name} fill={resultColors[entry.name]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <Metric label="Wins" value={report.battle_summary.wins} tone="green" />
            <Metric label="Losses" value={report.battle_summary.losses} tone="red" />
            <Metric label="Draws" value={report.battle_summary.draws} tone="blue" />
            <Metric label="3-Crown Wins" value={report.battle_summary.three_crown_wins} tone="gold" />
            <Metric label="3-Crown Losses" value={report.battle_summary.three_crown_losses} tone="red" />
            <Metric label="Current Streak" value={`${report.battle_summary.current_streak.count} ${report.battle_summary.current_streak.type}`} tone="blue" />
          </div>
        </div>
      </Section>

      <Section title="Deck Personality" icon={<BadgeAlert size={20} />}>
        <div className="grid gap-5 lg:grid-cols-[1fr_.9fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
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
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <div className="text-xs font-black uppercase text-white/50">Deck Style Estimate</div>
            <div className="mt-2 text-3xl font-black uppercase text-white">{report.deck_analysis.estimated_deck_style}</div>
            <div className="mt-5 text-sm font-bold uppercase text-white/50">Deck Identity Score</div>
            <div className="mt-2 h-3 overflow-hidden rounded-full bg-white/10">
              <div className="h-full bg-gradient-to-r from-rose-400 via-amber-300 to-emerald-300" style={{ width: `${report.deck_analysis.deck_identity_score}%` }} />
            </div>
            <div className="mt-2 text-2xl font-black text-white">{report.deck_analysis.deck_identity_score}/100</div>
            <div className="mt-6">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={usedData} layout="vertical" margin={{ left: 12, right: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.08)" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="card" type="category" width={110} stroke="#94a3b8" tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="used" fill="#facc15" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
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
                <Metric label="Win Rate" value={`${report.matchup_analysis.who_hurt_you.win_rate_against}%`} tone="gold" />
                <Metric label="Confidence" value={report.matchup_analysis.who_hurt_you.confidence} tone="green" />
              </div>
            )}
            <div className="mt-6 border-t border-white/10 pt-5">
              <div className="text-xs font-black uppercase text-sky-200">Natural Predator</div>
              <div className="mt-2 text-2xl font-black uppercase text-white">{report.matchup_analysis.natural_predator.label}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {report.matchup_analysis.natural_predator.core_cards.map((card) => <CardToken key={card} card={card} />)}
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-4">
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={traumaData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.08)" />
                <XAxis dataKey="card" stroke="#94a3b8" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={76} />
                <YAxis stroke="#94a3b8" />
                <Tooltip />
                <Legend />
                <Bar dataKey="lossRate" name="Loss rate" fill="#fb7185" radius={[6, 6, 0, 0]} />
                <Bar dataKey="winRate" name="Win rate" fill="#38bdf8" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </Section>

      <Section title="Behaviour Patterns" icon={<Zap size={20} />}>
        <div className="grid gap-5 lg:grid-cols-3">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5 lg:col-span-2">
            <div className="grid gap-3 sm:grid-cols-4">
              <Metric label="Detector" value={report.behaviour_analysis.title} tone="gold" />
              <Metric label="Unique Decks" value={report.behaviour_analysis.unique_decks} tone="blue" />
              <Metric label="After-Loss Changes" value={report.behaviour_analysis.changes_after_losses} tone="red" />
              <Metric label="Core Similarity" value={`${report.behaviour_analysis.core_deck_similarity_score}%`} tone="green" />
            </div>
            <div className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
              {report.battle_summary.timeline.slice(0, 12).map((battle, index) => (
                <div key={`${battle.battleTime}-${index}`} className="rounded-lg border border-white/10 bg-slate-950/50 p-3">
                  <div className={`text-sm font-black uppercase ${battle.result === "win" ? "text-emerald-300" : battle.result === "loss" ? "text-rose-300" : "text-sky-300"}`}>
                    {battle.result}
                  </div>
                  <div className="mt-1 text-xs font-semibold text-white/60">{battle.playerCrowns}-{battle.opponentCrowns}</div>
                  <div className="mt-2 truncate text-xs text-white/50">{battle.deck.slice(0, 3).join(" / ")}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-black uppercase text-white/50">Overlevelled Fraud Score</div>
            <div className="mt-3 text-6xl font-black text-rose-300">{report.level_analysis.overlevelled_fraud_score}%</div>
            <div className="mt-2 text-lg font-black uppercase text-white">{report.level_analysis.tier}</div>
            <div className="mt-6 h-4 overflow-hidden rounded-full bg-white/10">
              <div className="h-full bg-rose-400" style={{ width: `${report.level_analysis.overlevelled_fraud_score}%` }} />
            </div>
            <div className="mt-6 h-44">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={levelData} layout="vertical">
                  <XAxis type="number" hide />
                  <YAxis type="category" dataKey="name" hide />
                  <Tooltip />
                  <Bar dataKey="Underlevelled" stackId="a" fill="#60a5fa" />
                  <Bar dataKey="Even" stackId="a" fill="#facc15" />
                  <Bar dataKey="Overlevelled" stackId="a" fill="#fb7185" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </Section>

      <Section title="Final Verdict" icon={<Trophy size={20} />}>
        <div className="grid gap-5 lg:grid-cols-[.8fr_1.2fr]">
          <div className="rounded-lg border border-white/10 bg-white/5 p-5">
            <div className="text-xs font-black uppercase text-white/50">Score Breakdown</div>
            <div className="mt-4 space-y-3">
              {report.roast_report.score_breakdown.map((item) => (
                <div key={item.label}>
                  <div className="mb-1 flex items-center justify-between gap-3 text-sm font-bold text-white/78">
                    <span>{item.label}</span>
                    <span>+{item.points}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full bg-amber-300" style={{ width: `${Math.min(100, item.points * 6)}%` }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-6 text-sm font-semibold leading-6 text-white/60">{report.disclaimer}</p>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            {report.roasts.slice(4).map((roast) => <RoastPanel key={`${roast.rule_id}-${roast.title}`} roast={roast} />)}
          </div>
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
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    getDemoVictims()
      .then((payload) => setDemos(payload.victims))
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
      />
      {error && (
        <div className="fixed bottom-5 left-1/2 z-50 w-[min(92vw,720px)] -translate-x-1/2 rounded-lg border border-rose-300/40 bg-rose-950/90 p-4 text-sm font-bold text-rose-50 shadow-2xl">
          {error}
        </div>
      )}
    </div>
  );
}
