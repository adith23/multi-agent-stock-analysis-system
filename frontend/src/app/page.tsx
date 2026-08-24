"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Search,
  Radio,
  Database,
  BarChart3,
  Newspaper,
  Swords,
  ShieldCheck,
  ShieldAlert,
  Scale,
  TrendingUp,
  Minus,
  ArrowUpRight,
  ArrowDownRight,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Layers,
  Lock,
  Target,
  Calendar,
  FileText,
  Gavel,
  Globe,
} from "lucide-react";

/* ------------------------------------------------------------------ */
/* Design tokens — Bloomberg-terminal shell wrapping IC-memo documents */
/* ------------------------------------------------------------------ */
const C = {
  void: "#0A0B0D",
  panel: "#111318",
  panelRaised: "#181B21",
  inset: "#0C0E12",
  hairline: "#242830",
  hairlineBright: "#3A3F4A",
  text: "#E7E3D9",
  textDim: "#9BA0AA",
  textFaint: "#5C616B",
  amber: "#E0A730",
  amberDim: "#7A5E22",
  green: "#3FB968",
  greenDim: "#1B4A2C",
  red: "#F0554A",
  redDim: "#5A2420",
  blue: "#6FA8DC",
  parchment: "#C9A66B",
};

const FONT_STACK = {
  serif: "'Source Serif 4', Georgia, serif",
  mono: "'IBM Plex Mono', 'SFMono-Regular', Menlo, monospace",
  sans: "'Inter', -apple-system, sans-serif",
};

/* ------------------------------------------------------------------ */
/* Mock domain data — mirrors the SRS's agent/output contracts         */
/* ------------------------------------------------------------------ */
const STAGES = [
  {
    id: "data",
    layer: "Data",
    label: "Data Collector",
    icon: Database,
    ref: "FR-001–007",
  },
  {
    id: "macro",
    layer: "Analysis",
    label: "Macro / Regime",
    icon: Globe,
    ref: "FR-008–013",
  },
  {
    id: "fundamental",
    layer: "Analysis",
    label: "Fundamental Research",
    icon: FileText,
    ref: "FR-014–020",
  },
  {
    id: "technical",
    layer: "Analysis",
    label: "Technical Analyst",
    icon: BarChart3,
    ref: "FR-021–026",
  },
  {
    id: "sentiment",
    layer: "Analysis",
    label: "Sentiment & News",
    icon: Newspaper,
    ref: "FR-027–033",
  },
  {
    id: "bullbear",
    layer: "Synthesis",
    label: "Bull vs. Bear",
    icon: Swords,
    ref: "FR-034–039",
  },
  {
    id: "risk",
    layer: "Decision",
    label: "Risk Manager",
    icon: ShieldAlert,
    ref: "FR-040–046",
  },
  {
    id: "compliance",
    layer: "Decision",
    label: "Compliance",
    icon: Gavel,
    ref: "NFR-018–020",
  },
  {
    id: "pm",
    layer: "Decision",
    label: "Portfolio Manager",
    icon: Scale,
    ref: "FR-047–052",
  },
];
const LAYERS = ["Data", "Analysis", "Synthesis", "Decision"];

const ROLES = [
  { id: "pm", label: "Portfolio Manager" },
  { id: "risk", label: "Risk Officer" },
  { id: "compliance", label: "Compliance Reviewer" },
  { id: "analyst", label: "Research Analyst" },
];

const SIGNAL_META = {
  "STRONG BUY": { color: C.green, dir: 1 },
  BUY: { color: C.green, dir: 1 },
  ACCUMULATE: { color: C.green, dir: 1 },
  HOLD: { color: C.amber, dir: 0 },
  REDUCE: { color: C.red, dir: -1 },
  SELL: { color: C.red, dir: -1 },
  "STRONG SELL": { color: C.red, dir: -1 },
  "NOT BUY": { color: C.textDim, dir: 0 },
  "NOT SELL": { color: C.textDim, dir: 0 },
};

const REC = {
  ticker: "HLXD",
  company: "Helios Dynamics, Inc.",
  price: 214.62,
  change: 3.18,
  changePct: 1.51,
  action: "BUY",
  conviction: 78,
  convictionLabel: "78th percentile",
  timeHorizon: "Medium-Term (1–6 mo)",
  horizonDriver: "Catalyst-driven — Q3 data-center revenue print",
  catalyst: { name: "Q3 Earnings", date: "Nov 20, 2026", probability: 68 },
  expectedReturn: { bear: -8, base: 19, bull: 34 },
  positionSizing: "2.4% NAV target, phased in 3 tranches over 5 sessions",
  keyRisk: "Data-center revenue growth decelerates below 22% YoY",
  invalidation: "Two consecutive quarters of gross-margin compression > 150bps",
  thesis:
    "Data-center compute demand and margin mix outweigh near-term tariff exposure. Initiate a standard-weight position ahead of the Q3 print; scale on confirmation of backlog conversion.",
};

const AGREEMENT = [
  { agent: "Macro / Regime", stance: "bullish" },
  { agent: "Fundamental", stance: "bullish" },
  { agent: "Technical", stance: "neutral" },
  { agent: "Sentiment", stance: "bullish" },
];

const SPECIALISTS = {
  macro: {
    regime: "Risk-On / Late-Cycle",
    summary:
      "Easing rate-cut expectations and stable credit spreads support risk assets. Liquidity conditions remain constructive for high-beta growth names, though a hawkish surprise from the next policy meeting is the primary tail risk.",
    points: [
      "10Y–2Y curve re-steepening consistent with late-cycle, not recessionary, positioning",
      "Semiconductor capex cycle historically outperforms in this regime bucket",
      "USD strength is a modest headwind to non-US revenue mix",
    ],
    evidence: [
      {
        src: "FOMC Statement",
        type: "Policy Event",
        ts: "Jun 18, 2026",
        conf: "High",
      },
      {
        src: "Bloomberg Macro Feed",
        type: "Market Data",
        ts: "09:41 today",
        conf: "High",
      },
    ],
  },
  fundamental: {
    thesis:
      "Durable moat in AI-accelerator interconnects with expanding gross margin.",
    grade: "B+",
    bull: [
      "Backlog coverage extends 4 quarters at current book-to-bill",
      "Gross margin expansion from mix-shift toward high-end SKUs",
      "Net cash position funds buyback without diluting R&D",
    ],
    bear: [
      "Customer concentration — top 3 customers are 41% of revenue",
      "Capacity constraints could cap near-term unit shipments",
    ],
    fairValue: { low: 195, mid: 236, high: 268 },
    evidence: [
      {
        src: "10-Q Filing",
        type: "SEC Filing",
        ts: "May 2, 2026",
        conf: "High",
      },
      {
        src: "Earnings Call Transcript",
        type: "Transcript",
        ts: "May 2, 2026",
        conf: "Med",
      },
    ],
  },
  technical: {
    trend: { short: "Uptrend", medium: "Uptrend", long: "Uptrend" },
    momentum: 64,
    levels: { support: 198.4, resistance: 224.0 },
    flags: [
      "No breakout/breakdown risk detected",
      "RSI approaching overbought (68)",
    ],
    evidence: [
      {
        src: "OHLCV Daily Bars",
        type: "Market Data",
        ts: "09:41 today",
        conf: "High",
      },
    ],
  },
  sentiment: {
    score: 42,
    direction: "Improving",
    attention: "Elevated",
    tags: ["AI capex", "Export licensing", "Analyst day (Sep)"],
    evidence: [
      {
        src: "Newswire Aggregate",
        type: "News",
        ts: "08:55 today",
        conf: "Med",
      },
      {
        src: "Social Mention Volume",
        type: "Alt-Data",
        ts: "09:10 today",
        conf: "Low",
      },
    ],
  },
};

const BULLBEAR = {
  bull: [
    "Data-center accelerator demand outstrips current supply through FY27",
    "Gross margin trajectory supports multiple expansion, not compression",
    "Net-cash balance sheet provides optionality for buybacks or tuck-in M&A",
  ],
  bear: [
    "Customer concentration risk is understated in consensus models",
    "Export licensing changes could delay international shipments",
    "Valuation already prices in high-20s% revenue growth",
  ],
  weakAssumptions: [
    "Backlog-to-revenue conversion rate assumed flat vs. prior cycle — untested at this scale",
    "Tariff exposure modeled as static; no scenario for escalation",
  ],
  preMortem: [
    "If Q3 data-center revenue growth prints below 22% YoY, thesis breaks",
    "If two largest customers signal dual-sourcing, re-rate risk increases materially",
  ],
  unknowns: ["Next-gen node yield rates", "Competitor capacity ramp timeline"],
};

const RISK = {
  status: "PASS WITH CONDITIONS",
  exposures: [
    { label: "Concentration", value: 62, limit: 80 },
    { label: "Leverage", value: 34, limit: 100 },
    { label: "Liquidity (days to exit)", value: 48, limit: 100 },
    { label: "Factor Correlation", value: 71, limit: 80 },
  ],
  stress: [
    { scenario: "Rates +100bps", impact: "-1.8% portfolio NAV" },
    { scenario: "AI capex growth -30%", impact: "-3.1% position-level" },
    { scenario: "Sector rotation to value", impact: "-0.9% portfolio NAV" },
  ],
  note: "Concentration and correlation exposure are elevated but within hard limits. Recommend phased entry to avoid single-day liquidity impact.",
};

const COMPLIANCE = {
  restricted: "CLEAR",
  checks: [
    { label: "Restricted list screen", pass: true },
    { label: "Insider window check", pass: true },
    { label: "Mandate / style-box fit", pass: true },
    { label: "Concentration policy (single name ≤ 5% NAV)", pass: true },
  ],
  escalation: "NONE",
};

const INITIAL_AUDIT = [
  {
    ts: "09:41:22",
    actor: "SYSTEM",
    action: "PM Agent produced recommendation for HLXD",
    ref: "FR-052",
  },
  {
    ts: "09:41:18",
    actor: "SYSTEM",
    action: "Risk Manager Agent evaluated against portfolio risk budget",
    ref: "FR-041",
  },
  {
    ts: "09:41:09",
    actor: "SYSTEM",
    action: "Bull vs. Bear Agent generated decision memo",
    ref: "FR-038",
  },
  {
    ts: "09:40:51",
    actor: "SYSTEM",
    action:
      "Specialist agents (Macro, Fundamental, Technical, Sentiment) completed",
    ref: "FR-008–033",
  },
  {
    ts: "09:40:12",
    actor: "SYSTEM",
    action: "Data Collector normalized 1,204 records from 14 sources",
    ref: "FR-003",
  },
];

const SOURCES = [
  { name: "Market Data Feed", status: "ok", sync: "09:41:31" },
  { name: "SEC EDGAR", status: "delayed", sync: "09:27:04" },
  { name: "Newswire Aggregate", status: "ok", sync: "09:41:12" },
  { name: "Portfolio System (internal)", status: "ok", sync: "09:41:30" },
];

/* ------------------------------------------------------------------ */
/* Small shared UI primitives                                          */
/* ------------------------------------------------------------------ */
function Chip({
  children,
  color = C.textDim,
  bg = "transparent",
  border = true,
}) {
  return (
    <span
      style={{
        color,
        background: bg,
        border: border ? `1px solid ${color}55` : "none",
        fontFamily: FONT_STACK.mono,
        fontSize: 10.5,
        letterSpacing: "0.04em",
        padding: "2.5px 7px",
        borderRadius: 3,
        textTransform: "uppercase",
        whiteSpace: "nowrap",
        display: "inline-block",
      }}
    >
      {children}
    </span>
  );
}

function SectionLabel({ children, icon: Icon }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 6,
        marginBottom: 10,
        color: C.textFaint,
        fontFamily: FONT_STACK.mono,
        fontSize: 10.5,
        letterSpacing: "0.12em",
        textTransform: "uppercase",
      }}
    >
      {Icon && <Icon size={11} />}
      {children}
    </div>
  );
}

function Meter({ value, limit = 100, height = 6 }) {
  const pct = Math.min(100, (value / limit) * 100);
  const color = pct > 90 ? C.red : pct > 70 ? C.amber : C.green;
  return (
    <div
      style={{
        background: C.inset,
        height,
        borderRadius: 3,
        overflow: "hidden",
        border: `1px solid ${C.hairline}`,
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          background: color,
          transition: "width 0.6s ease",
        }}
      />
    </div>
  );
}

function StanceIcon({ stance }) {
  if (stance === "bullish") return <ArrowUpRight size={13} color={C.green} />;
  if (stance === "bearish") return <ArrowDownRight size={13} color={C.red} />;
  return <Minus size={13} color={C.textDim} />;
}

function Panel({ children, style }) {
  return (
    <div
      style={{
        background: C.panel,
        border: `1px solid ${C.hairline}`,
        borderRadius: 4,
        padding: 16,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function EvidenceList({ items }) {
  return (
    <div
      style={{
        marginTop: 12,
        borderTop: `1px solid ${C.hairline}`,
        paddingTop: 8,
      }}
    >
      <div
        style={{
          fontFamily: FONT_STACK.mono,
          fontSize: 9.5,
          letterSpacing: "0.1em",
          color: C.textFaint,
          marginBottom: 5,
          textTransform: "uppercase",
        }}
      >
        Evidence &amp; Provenance
      </div>
      {items.map((e, i) => (
        <div
          key={i}
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontFamily: FONT_STACK.mono,
            fontSize: 10.5,
            color: C.textDim,
            padding: "2px 0",
          }}
        >
          <span>
            {e.src} <span style={{ color: C.textFaint }}>· {e.type}</span>
          </span>
          <span>
            {e.ts}{" "}
            <span
              style={{
                color:
                  e.conf === "High"
                    ? C.green
                    : e.conf === "Med"
                      ? C.amber
                      : C.textFaint,
              }}
            >
              [{e.conf}]
            </span>
          </span>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Main component                                                       */
/* ------------------------------------------------------------------ */
export default function ConclaveTerminal() {
  const [role, setRole] = useState("pm");
  const [tickerInput, setTickerInput] = useState("HLXD");
  const [activeTab, setActiveTab] = useState("overview");
  const [activeSpecialist, setActiveSpecialist] = useState("macro");
  const [systemState, setSystemState] = useState("ready"); // idle | running | ready
  const [stageStatus, setStageStatus] = useState(() => {
    const s = {};
    STAGES.forEach((st) => (s[st.id] = "done"));
    return s;
  });
  const [decision, setDecision] = useState("pending_review");
  const [audit, setAudit] = useState(INITIAL_AUDIT);
  const [clock, setClock] = useState(new Date());
  const timers = useRef([]);

  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => () => timers.current.forEach(clearTimeout), []);

  function logAudit(actor, action, ref) {
    setAudit((prev) => [
      {
        ts: new Date().toLocaleTimeString("en-US", { hour12: false }),
        actor,
        action,
        ref,
      },
      ...prev,
    ]);
  }

  function runAnalysis(tk) {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    const clean = (tk || "HLXD").toUpperCase().trim();
    setSystemState("running");
    setDecision("pending_review");
    const reset = {};
    STAGES.forEach((s) => (reset[s.id] = "pending"));
    setStageStatus(reset);

    STAGES.forEach((s, i) => {
      timers.current.push(
        setTimeout(
          () => setStageStatus((p) => ({ ...p, [s.id]: "running" })),
          i * 340,
        ),
      );
      timers.current.push(
        setTimeout(
          () => setStageStatus((p) => ({ ...p, [s.id]: "done" })),
          i * 340 + 280,
        ),
      );
    });
    timers.current.push(
      setTimeout(
        () => {
          setSystemState("ready");
          setActiveTab("overview");
          logAudit(
            "SYSTEM",
            `Analysis pipeline completed for ${clean}`,
            "FR-053",
          );
        },
        STAGES.length * 340 + 350,
      ),
    );
  }

  function handleDecision(action) {
    setDecision(action);
    logAudit(
      ROLES.find((r) => r.id === role)?.label.toUpperCase() || "USER",
      `PM decision recorded: ${action.toUpperCase()}`,
      "FR-048",
    );
  }
  function handleOverride() {
    logAudit("RISK OFFICER", "Risk constraint override applied", "NFR-020");
  }
  function handleEscalate() {
    logAudit(
      "COMPLIANCE REVIEWER",
      "Recommendation escalated for secondary review",
      "NFR-018",
    );
  }

  const sig = SIGNAL_META[REC.action] || SIGNAL_META.HOLD;
  const decisionChip = {
    pending_review: { label: "PENDING REVIEW", color: C.amber },
    approved: { label: "APPROVED", color: C.green },
    rejected: { label: "REJECTED", color: C.red },
    deferred: { label: "DEFERRED", color: C.textDim },
  }[decision];

  return (
    <div
      style={{
        fontFamily: FONT_STACK.sans,
        background: C.void,
        color: C.text,
        minWidth: 1080,
        height: "100vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-thumb { background: ${C.hairlineBright}; border-radius: 4px; }
        ::-webkit-scrollbar-track { background: ${C.inset}; }
        button:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid ${C.amber}; outline-offset: 1px; }
        @keyframes stampIn { 0% { opacity: 0; transform: rotate(-14deg) scale(0.7); } 60% { opacity: 1; transform: rotate(-7deg) scale(1.08); } 100% { opacity: 1; transform: rotate(-8deg) scale(1); } }
        @keyframes marquee { from { transform: translateX(0); } to { transform: translateX(-50%); } }
        @keyframes runPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
        .stamp { animation: stampIn 0.5s cubic-bezier(.2,.8,.3,1.2); }
        .marquee-track { animation: marquee 28s linear infinite; }
        .run-pulse { animation: runPulse 1s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .stamp, .marquee-track, .run-pulse { animation: none !important; }
        }
        select { color-scheme: dark; }
      `}</style>

      {/* ---------------- Header ---------------- */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 20,
          padding: "0 16px",
          height: 52,
          borderBottom: `1px solid ${C.hairline}`,
          flexShrink: 0,
          background: C.panel,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Radio
            size={15}
            color={systemState === "running" ? C.amber : C.green}
            className={systemState === "running" ? "run-pulse" : ""}
          />
          <div>
            <div
              style={{
                fontFamily: FONT_STACK.serif,
                fontWeight: 700,
                fontSize: 16,
                letterSpacing: "0.02em",
                lineHeight: 1,
              }}
            >
              CONCLAVE
            </div>
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: 8.5,
                letterSpacing: "0.16em",
                color: C.textFaint,
              }}
            >
              MULTI-AGENT RESEARCH TERMINAL
            </div>
          </div>
        </div>

        <div
          style={{
            flex: 1,
            maxWidth: 420,
            display: "flex",
            alignItems: "center",
            background: C.inset,
            border: `1px solid ${C.hairline}`,
            borderRadius: 3,
            padding: "0 10px",
            height: 32,
          }}
        >
          <Search size={13} color={C.textFaint} />
          <input
            value={tickerInput}
            onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && runAnalysis(tickerInput)}
            placeholder="TICKER <GO>"
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: C.text,
              fontFamily: FONT_STACK.mono,
              fontSize: 12.5,
              marginLeft: 8,
              width: "100%",
              letterSpacing: "0.03em",
            }}
          />
          <button
            onClick={() => runAnalysis(tickerInput)}
            disabled={systemState === "running"}
            style={{
              background: "none",
              border: "none",
              color: C.amber,
              fontFamily: FONT_STACK.mono,
              fontSize: 11,
              fontWeight: 700,
              cursor: systemState === "running" ? "default" : "pointer",
              opacity: systemState === "running" ? 0.4 : 1,
              padding: "2px 4px",
            }}
          >
            {systemState === "running" ? "RUNNING…" : "GO ▶"}
          </button>
        </div>

        <div style={{ flex: 1 }} />

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontFamily: FONT_STACK.mono,
            fontSize: 11,
            color: C.textDim,
          }}
        >
          <Lock size={12} />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            style={{
              background: C.inset,
              color: C.text,
              border: `1px solid ${C.hairline}`,
              borderRadius: 3,
              fontFamily: FONT_STACK.mono,
              fontSize: 11,
              padding: "4px 6px",
            }}
          >
            {ROLES.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
        </div>

        <div
          style={{
            fontFamily: FONT_STACK.mono,
            fontSize: 12,
            color: C.textDim,
            minWidth: 68,
            textAlign: "right",
          }}
        >
          {clock.toLocaleTimeString("en-US", { hour12: false })}
        </div>
      </div>

      {/* ---------------- Sub-header: ticker strip ---------------- */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 18,
          padding: "8px 16px",
          borderBottom: `1px solid ${C.hairline}`,
          flexShrink: 0,
          background: C.void,
        }}
      >
        <div
          style={{ fontFamily: FONT_STACK.mono, fontSize: 20, fontWeight: 700 }}
        >
          {REC.ticker}
        </div>
        <div
          style={{
            fontFamily: FONT_STACK.sans,
            fontSize: 12.5,
            color: C.textDim,
          }}
        >
          {REC.company}
        </div>
        <div style={{ fontFamily: FONT_STACK.mono, fontSize: 15 }}>
          {REC.price.toFixed(2)}
        </div>
        <div
          style={{
            fontFamily: FONT_STACK.mono,
            fontSize: 12.5,
            color: C.green,
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <ArrowUpRight size={13} /> +{REC.change.toFixed(2)} ({REC.changePct}%)
        </div>
        <svg
          width="90"
          height="24"
          viewBox="0 0 90 24"
          style={{ opacity: 0.9 }}
        >
          <polyline
            points="0,18 12,15 24,17 36,10 48,12 60,6 72,8 90,2"
            fill="none"
            stroke={C.green}
            strokeWidth="1.5"
          />
        </svg>
        <div style={{ flex: 1 }} />
        <Chip color={C.amber}>SEC EDGAR — DELAYED 14M</Chip>
        <Chip color={C.green}>ALL AGENTS NOMINAL</Chip>
      </div>

      {/* ---------------- Body ---------------- */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* Left rail: pipeline */}
        <div
          style={{
            width: 226,
            borderRight: `1px solid ${C.hairline}`,
            padding: 14,
            overflowY: "auto",
            flexShrink: 0,
          }}
        >
          <SectionLabel icon={Layers}>Agent Pipeline</SectionLabel>
          {LAYERS.map((layer) => (
            <div key={layer} style={{ marginBottom: 14 }}>
              <div
                style={{
                  fontFamily: FONT_STACK.mono,
                  fontSize: 9,
                  color: C.textFaint,
                  letterSpacing: "0.1em",
                  marginBottom: 6,
                }}
              >
                {layer.toUpperCase()}
              </div>
              {STAGES.filter((s) => s.layer === layer).map((s) => {
                const status = stageStatus[s.id];
                const Icon = s.icon;
                const dotColor =
                  status === "done"
                    ? C.green
                    : status === "running"
                      ? C.amber
                      : C.textFaint;
                const clickable = [
                  "macro",
                  "fundamental",
                  "technical",
                  "sentiment",
                  "bullbear",
                  "risk",
                  "compliance",
                  "pm",
                ].includes(s.id);
                const goTo = () => {
                  if (
                    ["macro", "fundamental", "technical", "sentiment"].includes(
                      s.id,
                    )
                  ) {
                    setActiveTab("specialists");
                    setActiveSpecialist(s.id);
                  } else if (s.id === "bullbear") setActiveTab("adversarial");
                  else if (s.id === "risk" || s.id === "compliance")
                    setActiveTab("risk");
                  else if (s.id === "pm") setActiveTab("overview");
                };
                return (
                  <button
                    key={s.id}
                    onClick={clickable ? goTo : undefined}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 7,
                      width: "100%",
                      background: "transparent",
                      border: "none",
                      cursor: clickable ? "pointer" : "default",
                      padding: "5px 4px",
                      borderRadius: 3,
                      textAlign: "left",
                    }}
                    onMouseEnter={(e) =>
                      (e.currentTarget.style.background = C.panelRaised)
                    }
                    onMouseLeave={(e) =>
                      (e.currentTarget.style.background = "transparent")
                    }
                  >
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        background: dotColor,
                        flexShrink: 0,
                        boxShadow:
                          status === "running" ? `0 0 6px ${C.amber}` : "none",
                      }}
                      className={status === "running" ? "run-pulse" : ""}
                    />
                    <Icon size={12} color={C.textDim} />
                    <span
                      style={{
                        fontFamily: FONT_STACK.mono,
                        fontSize: 11,
                        color: status === "pending" ? C.textFaint : C.text,
                      }}
                    >
                      {s.label}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}
          <div
            style={{
              marginTop: 6,
              fontFamily: FONT_STACK.mono,
              fontSize: 10,
              color: C.textFaint,
              borderTop: `1px solid ${C.hairline}`,
              paddingTop: 10,
            }}
          >
            14 sources · 1,204 records normalized
          </div>
        </div>

        {/* Center content */}
        <div
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          {/* Tabs */}
          <div
            style={{
              display: "flex",
              gap: 2,
              borderBottom: `1px solid ${C.hairline}`,
              padding: "0 16px",
              flexShrink: 0,
            }}
          >
            {[
              ["overview", "IC Memo"],
              ["specialists", "Specialist Reports"],
              ["adversarial", "Bull vs. Bear"],
              ["risk", "Risk & Compliance"],
              ["audit", "Audit Trail"],
            ].map(([id, label]) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: "12px 14px",
                  fontFamily: FONT_STACK.mono,
                  fontSize: 11.5,
                  letterSpacing: "0.04em",
                  textTransform: "uppercase",
                  color: activeTab === id ? C.text : C.textFaint,
                  borderBottom:
                    activeTab === id
                      ? `2px solid ${C.amber}`
                      : "2px solid transparent",
                }}
              >
                {label}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: 18 }}>
            {/* ---- Overview / IC Memo ---- */}
            {activeTab === "overview" && (
              <Panel style={{ position: "relative", maxWidth: 900 }}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    borderBottom: `1px solid ${C.hairline}`,
                    paddingBottom: 12,
                    marginBottom: 14,
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontFamily: FONT_STACK.serif,
                        fontSize: 19,
                        fontWeight: 600,
                      }}
                    >
                      Investment Committee Memo
                    </div>
                    <div
                      style={{
                        fontFamily: FONT_STACK.mono,
                        fontSize: 10.5,
                        color: C.textFaint,
                        marginTop: 3,
                      }}
                    >
                      {REC.ticker} · {REC.company} · prepared by CONCLAVE v2.3 ·{" "}
                      {clock.toLocaleDateString()}
                    </div>
                  </div>
                  <Chip color={C.parchment}>
                    INTERNAL — DECISION SUPPORT ONLY
                  </Chip>
                </div>

                {/* Stamp */}
                <div
                  className="stamp"
                  style={{
                    position: "absolute",
                    top: 14,
                    right: 20,
                    transform: "rotate(-8deg)",
                    border: `3px double ${sig.color}`,
                    borderRadius: "50%",
                    width: 104,
                    height: 104,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    color: sig.color,
                    opacity: 0.92,
                  }}
                >
                  <div
                    style={{
                      fontFamily: FONT_STACK.mono,
                      fontWeight: 700,
                      fontSize: 13,
                      letterSpacing: "0.03em",
                      textAlign: "center",
                      lineHeight: 1.1,
                    }}
                  >
                    {REC.action}
                  </div>
                  <div
                    style={{
                      fontFamily: FONT_STACK.mono,
                      fontSize: 9,
                      marginTop: 3,
                    }}
                  >
                    CONV {REC.conviction}
                  </div>
                </div>

                <p
                  style={{
                    fontFamily: FONT_STACK.serif,
                    fontSize: 14.5,
                    lineHeight: 1.6,
                    color: C.text,
                    maxWidth: 620,
                    marginBottom: 18,
                  }}
                >
                  {REC.thesis}
                </p>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 14,
                    marginBottom: 18,
                  }}
                >
                  <div>
                    <SectionLabel icon={Calendar}>Time Horizon</SectionLabel>
                    <div
                      style={{ fontFamily: FONT_STACK.mono, fontSize: 12.5 }}
                    >
                      {REC.timeHorizon}
                    </div>
                    <div
                      style={{
                        fontFamily: FONT_STACK.sans,
                        fontSize: 11,
                        color: C.textDim,
                        marginTop: 2,
                      }}
                    >
                      {REC.horizonDriver}
                    </div>
                  </div>
                  <div>
                    <SectionLabel icon={Target}>Primary Catalyst</SectionLabel>
                    <div
                      style={{ fontFamily: FONT_STACK.mono, fontSize: 12.5 }}
                    >
                      {REC.catalyst.name} — {REC.catalyst.date}
                    </div>
                    <div
                      style={{
                        fontFamily: FONT_STACK.sans,
                        fontSize: 11,
                        color: C.textDim,
                        marginTop: 2,
                      }}
                    >
                      {REC.catalyst.probability}% probability priced by options
                      market
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: 18 }}>
                  <SectionLabel icon={TrendingUp}>
                    Expected Return Range
                  </SectionLabel>
                  <div
                    style={{
                      position: "relative",
                      height: 26,
                      background: C.inset,
                      borderRadius: 3,
                      border: `1px solid ${C.hairline}`,
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        left: "0%",
                        width: `${((REC.expectedReturn.base - REC.expectedReturn.bear) / (REC.expectedReturn.bull - REC.expectedReturn.bear)) * 100}%`,
                        top: 0,
                        bottom: 0,
                        background: `${C.green}22`,
                        borderRight: `1px solid ${C.green}`,
                      }}
                    />
                    <div
                      style={{
                        position: "absolute",
                        left: 8,
                        top: 5,
                        fontFamily: FONT_STACK.mono,
                        fontSize: 10.5,
                        color: C.red,
                      }}
                    >
                      BEAR {REC.expectedReturn.bear}%
                    </div>
                    <div
                      style={{
                        position: "absolute",
                        left: "50%",
                        transform: "translateX(-50%)",
                        top: 5,
                        fontFamily: FONT_STACK.mono,
                        fontSize: 10.5,
                        color: C.text,
                        fontWeight: 700,
                      }}
                    >
                      BASE +{REC.expectedReturn.base}%
                    </div>
                    <div
                      style={{
                        position: "absolute",
                        right: 8,
                        top: 5,
                        fontFamily: FONT_STACK.mono,
                        fontSize: 10.5,
                        color: C.green,
                      }}
                    >
                      BULL +{REC.expectedReturn.bull}%
                    </div>
                  </div>
                </div>

                <div style={{ marginBottom: 18 }}>
                  <SectionLabel>Position Sizing</SectionLabel>
                  <div style={{ fontFamily: FONT_STACK.mono, fontSize: 12.5 }}>
                    {REC.positionSizing}
                  </div>
                </div>

                <div style={{ marginBottom: 18 }}>
                  <SectionLabel>Signal Agreement Matrix</SectionLabel>
                  <div style={{ display: "flex", gap: 18, flexWrap: "wrap" }}>
                    {AGREEMENT.map((a) => (
                      <div
                        key={a.agent}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 5,
                          fontFamily: FONT_STACK.mono,
                          fontSize: 11,
                        }}
                      >
                        <StanceIcon stance={a.stance} /> {a.agent}
                      </div>
                    ))}
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 5,
                        fontFamily: FONT_STACK.mono,
                        fontSize: 11,
                      }}
                    >
                      <ShieldCheck size={13} color={C.green} /> Risk: Pass
                    </div>
                  </div>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 14,
                    marginBottom: 20,
                  }}
                >
                  <div>
                    <SectionLabel icon={AlertTriangle}>Key Risk</SectionLabel>
                    <div
                      style={{
                        fontFamily: FONT_STACK.sans,
                        fontSize: 12,
                        color: C.textDim,
                      }}
                    >
                      {REC.keyRisk}
                    </div>
                  </div>
                  <div>
                    <SectionLabel icon={XCircle}>
                      Invalidation Trigger
                    </SectionLabel>
                    <div
                      style={{
                        fontFamily: FONT_STACK.sans,
                        fontSize: 12,
                        color: C.textDim,
                      }}
                    >
                      {REC.invalidation}
                    </div>
                  </div>
                </div>

                {/* Decision row */}
                <div
                  style={{
                    borderTop: `1px solid ${C.hairline}`,
                    paddingTop: 14,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <Chip
                    color={decisionChip.color}
                    bg={`${decisionChip.color}18`}
                  >
                    {decisionChip.label}
                  </Chip>
                  {role === "pm" ? (
                    <>
                      <ActionButton
                        onClick={() => handleDecision("approved")}
                        color={C.green}
                      >
                        Approve
                      </ActionButton>
                      <ActionButton
                        onClick={() => handleDecision("rejected")}
                        color={C.red}
                      >
                        Reject
                      </ActionButton>
                      <ActionButton
                        onClick={() => handleDecision("deferred")}
                        color={C.textDim}
                      >
                        Defer
                      </ActionButton>
                    </>
                  ) : (
                    <span
                      style={{
                        fontFamily: FONT_STACK.mono,
                        fontSize: 10.5,
                        color: C.textFaint,
                      }}
                    >
                      Read-only — switch role to Portfolio Manager to record a
                      decision
                    </span>
                  )}
                </div>
              </Panel>
            )}

            {/* ---- Specialist Reports ---- */}
            {activeTab === "specialists" && (
              <div style={{ maxWidth: 900 }}>
                <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
                  {Object.keys(SPECIALISTS).map((k) => (
                    <button
                      key={k}
                      onClick={() => setActiveSpecialist(k)}
                      style={{
                        background:
                          activeSpecialist === k
                            ? C.panelRaised
                            : "transparent",
                        border: `1px solid ${C.hairline}`,
                        color: activeSpecialist === k ? C.text : C.textDim,
                        fontFamily: FONT_STACK.mono,
                        fontSize: 11,
                        textTransform: "capitalize",
                        padding: "6px 12px",
                        borderRadius: 3,
                        cursor: "pointer",
                      }}
                    >
                      {k}
                    </button>
                  ))}
                </div>

                {activeSpecialist === "macro" && (
                  <Panel>
                    <SectionLabel icon={Globe}>
                      Regime Classification
                    </SectionLabel>
                    <Chip color={C.blue} bg={`${C.blue}18`}>
                      {SPECIALISTS.macro.regime}
                    </Chip>
                    <p
                      style={{
                        fontFamily: FONT_STACK.sans,
                        fontSize: 12.5,
                        color: C.textDim,
                        lineHeight: 1.6,
                        marginTop: 12,
                      }}
                    >
                      {SPECIALISTS.macro.summary}
                    </p>
                    <ul
                      style={{
                        margin: "10px 0 0",
                        paddingLeft: 18,
                        fontFamily: FONT_STACK.sans,
                        fontSize: 12,
                        color: C.textDim,
                        lineHeight: 1.8,
                      }}
                    >
                      {SPECIALISTS.macro.points.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                    <EvidenceList items={SPECIALISTS.macro.evidence} />
                  </Panel>
                )}

                {activeSpecialist === "fundamental" && (
                  <Panel>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                    >
                      <SectionLabel icon={FileText}>
                        Investment Thesis
                      </SectionLabel>
                      <Chip color={C.blue}>
                        QUALITY GRADE {SPECIALISTS.fundamental.grade}
                      </Chip>
                    </div>
                    <p
                      style={{
                        fontFamily: FONT_STACK.serif,
                        fontSize: 13.5,
                        color: C.text,
                        marginBottom: 14,
                      }}
                    >
                      {SPECIALISTS.fundamental.thesis}
                    </p>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: 16,
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontFamily: FONT_STACK.mono,
                            fontSize: 10.5,
                            color: C.green,
                            marginBottom: 6,
                            textTransform: "uppercase",
                          }}
                        >
                          Bull Drivers
                        </div>
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: 16,
                            fontSize: 12,
                            color: C.textDim,
                            lineHeight: 1.8,
                          }}
                        >
                          {SPECIALISTS.fundamental.bull.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div
                          style={{
                            fontFamily: FONT_STACK.mono,
                            fontSize: 10.5,
                            color: C.red,
                            marginBottom: 6,
                            textTransform: "uppercase",
                          }}
                        >
                          Bear Drivers
                        </div>
                        <ul
                          style={{
                            margin: 0,
                            paddingLeft: 16,
                            fontSize: 12,
                            color: C.textDim,
                            lineHeight: 1.8,
                          }}
                        >
                          {SPECIALISTS.fundamental.bear.map((p, i) => (
                            <li key={i}>{p}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    <div style={{ marginTop: 16 }}>
                      <SectionLabel>Fair Value Range</SectionLabel>
                      <div
                        style={{ fontFamily: FONT_STACK.mono, fontSize: 12.5 }}
                      >
                        ${SPECIALISTS.fundamental.fairValue.low} —{" "}
                        <span style={{ color: C.amber }}>
                          ${SPECIALISTS.fundamental.fairValue.mid}
                        </span>{" "}
                        — ${SPECIALISTS.fundamental.fairValue.high}
                      </div>
                    </div>
                    <EvidenceList items={SPECIALISTS.fundamental.evidence} />
                  </Panel>
                )}

                {activeSpecialist === "technical" && (
                  <Panel>
                    <SectionLabel icon={BarChart3}>Trend State</SectionLabel>
                    <div style={{ display: "flex", gap: 20, marginBottom: 14 }}>
                      {Object.entries(SPECIALISTS.technical.trend).map(
                        ([k, v]) => (
                          <div key={k}>
                            <div
                              style={{
                                fontFamily: FONT_STACK.mono,
                                fontSize: 9.5,
                                color: C.textFaint,
                                textTransform: "uppercase",
                              }}
                            >
                              {k}
                            </div>
                            <div
                              style={{
                                fontFamily: FONT_STACK.mono,
                                fontSize: 12.5,
                                color: C.green,
                              }}
                            >
                              {v}
                            </div>
                          </div>
                        ),
                      )}
                    </div>
                    <SectionLabel>Momentum</SectionLabel>
                    <div style={{ maxWidth: 260, marginBottom: 14 }}>
                      <Meter value={SPECIALISTS.technical.momentum} />
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: 24,
                        marginBottom: 14,
                        fontFamily: FONT_STACK.mono,
                        fontSize: 12.5,
                      }}
                    >
                      <div>
                        Support{" "}
                        <span style={{ color: C.textDim }}>
                          ${SPECIALISTS.technical.levels.support}
                        </span>
                      </div>
                      <div>
                        Resistance{" "}
                        <span style={{ color: C.textDim }}>
                          ${SPECIALISTS.technical.levels.resistance}
                        </span>
                      </div>
                    </div>
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: 18,
                        fontSize: 12,
                        color: C.textDim,
                        lineHeight: 1.8,
                      }}
                    >
                      {SPECIALISTS.technical.flags.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                    <EvidenceList items={SPECIALISTS.technical.evidence} />
                  </Panel>
                )}

                {activeSpecialist === "sentiment" && (
                  <Panel>
                    <SectionLabel icon={Newspaper}>
                      Sentiment Score
                    </SectionLabel>
                    <div style={{ maxWidth: 300, marginBottom: 14 }}>
                      <Meter
                        value={SPECIALISTS.sentiment.score + 100}
                        limit={200}
                      />
                      <div
                        style={{
                          fontFamily: FONT_STACK.mono,
                          fontSize: 11,
                          color: C.textDim,
                          marginTop: 4,
                        }}
                      >
                        Score: +{SPECIALISTS.sentiment.score} / 100 ·{" "}
                        {SPECIALISTS.sentiment.direction}
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: 16, marginBottom: 14 }}>
                      <Chip color={C.amber}>
                        ATTENTION:{" "}
                        {SPECIALISTS.sentiment.attention.toUpperCase()}
                      </Chip>
                    </div>
                    <SectionLabel>Event Tags</SectionLabel>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {SPECIALISTS.sentiment.tags.map((t, i) => (
                        <Chip key={i}>{t}</Chip>
                      ))}
                    </div>
                    <EvidenceList items={SPECIALISTS.sentiment.evidence} />
                  </Panel>
                )}
              </div>
            )}

            {/* ---- Bull vs Bear ---- */}
            {activeTab === "adversarial" && (
              <div style={{ maxWidth: 900 }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 14,
                    marginBottom: 14,
                  }}
                >
                  <Panel style={{ borderColor: `${C.green}44` }}>
                    <SectionLabel icon={ArrowUpRight}>Bull Case</SectionLabel>
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: 18,
                        fontSize: 12.5,
                        color: C.text,
                        lineHeight: 1.9,
                      }}
                    >
                      {BULLBEAR.bull.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  </Panel>
                  <Panel style={{ borderColor: `${C.red}44` }}>
                    <SectionLabel icon={ArrowDownRight}>Bear Case</SectionLabel>
                    <ul
                      style={{
                        margin: 0,
                        paddingLeft: 18,
                        fontSize: 12.5,
                        color: C.text,
                        lineHeight: 1.9,
                      }}
                    >
                      {BULLBEAR.bear.map((p, i) => (
                        <li key={i}>{p}</li>
                      ))}
                    </ul>
                  </Panel>
                </div>
                <Panel style={{ marginBottom: 14 }}>
                  <SectionLabel icon={AlertTriangle}>
                    Weak Assumptions &amp; Contradictions
                  </SectionLabel>
                  <ul
                    style={{
                      margin: 0,
                      paddingLeft: 18,
                      fontSize: 12,
                      color: C.textDim,
                      lineHeight: 1.8,
                    }}
                  >
                    {BULLBEAR.weakAssumptions.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </Panel>
                <Panel style={{ marginBottom: 14 }}>
                  <SectionLabel icon={XCircle}>
                    Pre-Mortem — Conditions For Failure
                  </SectionLabel>
                  <ul
                    style={{
                      margin: 0,
                      paddingLeft: 18,
                      fontSize: 12,
                      color: C.textDim,
                      lineHeight: 1.8,
                    }}
                  >
                    {BULLBEAR.preMortem.map((p, i) => (
                      <li key={i}>{p}</li>
                    ))}
                  </ul>
                </Panel>
                <Panel>
                  <SectionLabel>Material Unknowns</SectionLabel>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {BULLBEAR.unknowns.map((u, i) => (
                      <Chip key={i}>{u}</Chip>
                    ))}
                  </div>
                </Panel>
              </div>
            )}

            {/* ---- Risk & Compliance ---- */}
            {activeTab === "risk" && (
              <div style={{ maxWidth: 900 }}>
                <Panel
                  style={{
                    marginBottom: 14,
                    borderColor: `${C.amber}55`,
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                  }}
                >
                  <ShieldAlert size={18} color={C.amber} />
                  <div
                    style={{
                      fontFamily: FONT_STACK.mono,
                      fontSize: 13,
                      letterSpacing: "0.03em",
                    }}
                  >
                    {RISK.status}
                  </div>
                  <div style={{ flex: 1 }} />
                  {role === "risk" && (
                    <ActionButton onClick={handleOverride} color={C.amber}>
                      Override Constraint
                    </ActionButton>
                  )}
                </Panel>

                <Panel style={{ marginBottom: 14 }}>
                  <SectionLabel>Exposure vs. Limit</SectionLabel>
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: 16,
                    }}
                  >
                    {RISK.exposures.map((e) => (
                      <div key={e.label}>
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            fontFamily: FONT_STACK.mono,
                            fontSize: 11,
                            marginBottom: 4,
                          }}
                        >
                          <span>{e.label}</span>
                          <span style={{ color: C.textDim }}>
                            {e.value} / {e.limit}
                          </span>
                        </div>
                        <Meter value={e.value} limit={e.limit} />
                      </div>
                    ))}
                  </div>
                  <p
                    style={{
                      fontSize: 12,
                      color: C.textDim,
                      marginTop: 14,
                      lineHeight: 1.6,
                    }}
                  >
                    {RISK.note}
                  </p>
                </Panel>

                <Panel style={{ marginBottom: 14 }}>
                  <SectionLabel>Stress Test Scenarios</SectionLabel>
                  {RISK.stress.map((s, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        padding: "6px 0",
                        borderBottom:
                          i < RISK.stress.length - 1
                            ? `1px solid ${C.hairline}`
                            : "none",
                        fontFamily: FONT_STACK.mono,
                        fontSize: 12,
                      }}
                    >
                      <span style={{ color: C.textDim }}>{s.scenario}</span>
                      <span style={{ color: C.red }}>{s.impact}</span>
                    </div>
                  ))}
                </Panel>

                <Panel>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 10,
                    }}
                  >
                    <SectionLabel icon={Gavel}>Compliance</SectionLabel>
                    <Chip color={C.green}>
                      RESTRICTED LIST: {COMPLIANCE.restricted}
                    </Chip>
                  </div>
                  {COMPLIANCE.checks.map((c, i) => (
                    <div
                      key={i}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        padding: "4px 0",
                        fontSize: 12.5,
                      }}
                    >
                      <CheckCircle2 size={13} color={C.green} /> {c.label}
                    </div>
                  ))}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 10,
                      marginTop: 12,
                    }}
                  >
                    <Chip color={C.textDim}>
                      ESCALATION: {COMPLIANCE.escalation}
                    </Chip>
                    {role === "compliance" && (
                      <ActionButton onClick={handleEscalate} color={C.red}>
                        Escalate
                      </ActionButton>
                    )}
                  </div>
                </Panel>
              </div>
            )}

            {/* ---- Audit Trail ---- */}
            {activeTab === "audit" && (
              <Panel style={{ maxWidth: 900 }}>
                <SectionLabel icon={Clock}>Audit Trail</SectionLabel>
                {audit.map((a, i) => (
                  <div
                    key={i}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "70px 150px 1fr 90px",
                      gap: 10,
                      padding: "7px 4px",
                      background: i % 2 ? "transparent" : C.inset,
                      fontFamily: FONT_STACK.mono,
                      fontSize: 11.5,
                      alignItems: "center",
                    }}
                  >
                    <span style={{ color: C.textFaint }}>{a.ts}</span>
                    <span style={{ color: C.blue }}>{a.actor}</span>
                    <span style={{ color: C.text }}>{a.action}</span>
                    <span style={{ color: C.textFaint, textAlign: "right" }}>
                      {a.ref}
                    </span>
                  </div>
                ))}
              </Panel>
            )}
          </div>
        </div>

        {/* Right rail: portfolio context */}
        <div
          style={{
            width: 250,
            borderLeft: `1px solid ${C.hairline}`,
            padding: 14,
            overflowY: "auto",
            flexShrink: 0,
          }}
        >
          <SectionLabel icon={Scale}>Portfolio Context</SectionLabel>
          <Panel style={{ marginBottom: 12, padding: 12 }}>
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: 10,
                color: C.textFaint,
                textTransform: "uppercase",
                marginBottom: 6,
              }}
            >
              Current Position
            </div>
            <div style={{ fontFamily: FONT_STACK.mono, fontSize: 12.5 }}>
              0.0% NAV · No open position
            </div>
          </Panel>
          <Panel style={{ marginBottom: 12, padding: 12 }}>
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: 10,
                color: C.textFaint,
                textTransform: "uppercase",
                marginBottom: 8,
              }}
            >
              Risk Budget Utilization
            </div>
            <Meter value={41} />
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: 11,
                color: C.textDim,
                marginTop: 4,
              }}
            >
              41% of desk risk budget allocated
            </div>
          </Panel>
          <Panel style={{ marginBottom: 12, padding: 12 }}>
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: 10,
                color: C.textFaint,
                textTransform: "uppercase",
                marginBottom: 6,
              }}
            >
              Mandate Fit
            </div>
            <Chip color={C.green} bg={`${C.green}18`}>
              WITHIN STYLE BOX
            </Chip>
          </Panel>
          <Panel style={{ padding: 12 }}>
            <div
              style={{
                fontFamily: FONT_STACK.mono,
                fontSize: 10,
                color: C.textFaint,
                textTransform: "uppercase",
                marginBottom: 8,
              }}
            >
              Data Source Health
            </div>
            {SOURCES.map((s) => (
              <div
                key={s.name}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "4px 0",
                  fontFamily: FONT_STACK.mono,
                  fontSize: 10.5,
                }}
              >
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: s.status === "ok" ? C.green : C.amber,
                    flexShrink: 0,
                  }}
                />
                <span style={{ color: C.textDim, flex: 1 }}>{s.name}</span>
                <span style={{ color: C.textFaint }}>{s.sync}</span>
              </div>
            ))}
          </Panel>
        </div>
      </div>

      {/* ---------------- Footer ticker tape ---------------- */}
      <div
        style={{
          height: 26,
          borderTop: `1px solid ${C.hairline}`,
          overflow: "hidden",
          flexShrink: 0,
          background: C.panel,
          display: "flex",
          alignItems: "center",
        }}
      >
        <div
          className="marquee-track"
          style={{
            display: "flex",
            whiteSpace: "nowrap",
            fontFamily: FONT_STACK.mono,
            fontSize: 10.5,
            color: C.textFaint,
          }}
        >
          {[0, 1].map((rep) => (
            <span key={rep} style={{ paddingRight: 60 }}>
              AGENT VERSIONS: FUNDAMENTAL v1.4 · TECHNICAL v2.1 · RISK v3.0 · PM
              v1.1 &nbsp;|&nbsp; LAST FULL AUDIT SYNC {audit[0]?.ts}{" "}
              &nbsp;|&nbsp; DATA ISOLATION: PUBLIC / INTERNAL BOUNDARY ENFORCED
              &nbsp;|&nbsp; RETENTION POLICY: 400 DAYS &nbsp;|&nbsp; ROLE
              ACTIVE: {ROLES.find((r) => r.id === role)?.label.toUpperCase()}{" "}
              &nbsp;|&nbsp;
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function ActionButton({ children, onClick, color }) {
  return (
    <button
      onClick={onClick}
      style={{
        background: `${color}18`,
        border: `1px solid ${color}66`,
        color,
        fontFamily: FONT_STACK.mono,
        fontSize: 11,
        letterSpacing: "0.03em",
        padding: "6px 14px",
        borderRadius: 3,
        cursor: "pointer",
        textTransform: "uppercase",
      }}
      onMouseEnter={(e) => (e.currentTarget.style.background = `${color}30`)}
      onMouseLeave={(e) => (e.currentTarget.style.background = `${color}18`)}
    >
      {children}
    </button>
  );
}
