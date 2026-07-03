"use client";

import React, { useState, useEffect, useRef } from "react";

// ==========================================
// 1. INSTITUTIONAL MOCK DATA FOR 4 EQUITIES
// ==========================================
interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  sector: string;
  marketCap: string;
  volume: string;
  averageVolume: string;
  
  // Pipeline status and log script for simulation
  pipelineLogs: { timestamp: string; source: string; message: string; type: "info" | "success" | "warning" | "error" }[];

  // Macro Agent
  macro: {
    regime: string;
    details: string;
    threatLevel: "Low" | "Medium" | "High";
    pmi: number;
    cpi: number;
    yieldSpread10Y2Y: number;
    rates: string;
    volatilityIndex: number;
  };

  // Fundamental Agent
  fundamentals: {
    thesisSummary: string;
    fairValueLow: number;
    fairValueHigh: number;
    beneishMScore: number; // Forensic Accounting flag
    beneishInterpretation: string;
    altmanZScore: number;
    revenueGrowthYoY: number;
    grossMargin: number;
    netMargin: number;
    debtToEquity: number;
    accrualCheck: "Pass" | "Warning" | "Fail";
  };

  // Technical Agent
  technicals: {
    trendState: "Bullish" | "Bearish" | "Neutral";
    rsi: number;
    macdState: "Bullish Crossover" | "Bearish Crossover" | "Neutral/Consolidating";
    atr: number;
    support: number;
    resistance: number;
    timingCue: string;
    chartPoints: number[]; // Points for drawing our SVG line chart
  };

  // Sentiment Agent
  sentiment: {
    score: number; // -1.0 to +1.0
    attentionLevel: number; // 0 to 100
    crowdingWarning: string;
    newsFeed: { title: string; source: string; age: string; sentiment: number; relevance: number }[];
  };

  // Bull vs Bear Adversarial Agent
  adversarial: {
    bullCase: string[];
    bearCase: string[];
    weakAssumptions: string[];
    invalidationTriggers: string[];
    catalysts: { event: string; date: string; importance: "High" | "Medium" | "Low"; probability: number }[];
  };

  // Risk Manager Agent
  risk: {
    var1d95: number; // Value-at-Risk percentage
    concentrationCheck: string;
    restrictedListCheck: "Passed" | "Restricted";
    kellyAllocation: number; // Kelly criterion suggestion
    volAllocation: number; // Volatility targeting suggestion
    riskParityAllocation: number;
    stopLoss: number;
    profitTarget: number;
    timeHorizonDays: number;
  };

  // PM Default Actions
  pmDefaults: {
    action: "Strong Buy" | "Buy" | "Accumulate" | "Hold" | "Reduce" | "Sell" | "Strong Sell" | "Not Buy" | "Not Sell";
    conviction: number; // 0-100%
    sizing: number; // allocation percent
    timeHorizon: "Tactical" | "Medium-term" | "Strategic";
    rationale: string;
  };

  // Lineage metadata
  lineage: {
    dataSources: string[];
    modelsUsed: string[];
    promptVersions: { agent: string; version: string; file: string }[];
  };
}

const STOCKS_DATA: Record<string, StockData> = {
  NVDA: {
    symbol: "NVDA",
    name: "NVIDIA Corporation",
    price: 127.40,
    change: 4.00,
    changePercent: 3.24,
    sector: "Technology / Semiconductors",
    marketCap: "$3.13T",
    volume: "42.5M",
    averageVolume: "38.2M",
    pipelineLogs: [
      { timestamp: "08:30:02", source: "Data Collector", message: "Successfully connected to SEC EDGAR API & NASDAQ price feeds.", type: "success" },
      { timestamp: "08:30:05", source: "Data Collector", message: "Ingested 10-Q filing (Q1 2026), 18 earnings transcripts, and 450 news documents.", type: "info" },
      { timestamp: "08:30:08", source: "Data Collector", message: "Normalized tick data and removed 12 duplicate social sentiments.", type: "success" },
      { timestamp: "08:30:12", source: "Macro Agent", message: "Detected High-Growth regime with high equity beta sensitivity. VIX currently at 14.2.", type: "info" },
      { timestamp: "08:30:15", source: "Fundamental Agent", message: "Completed analysis of 10-Q. Revenue +78% YoY. Operating margin stable at 62%.", type: "success" },
      { timestamp: "08:30:17", source: "Fundamental Agent", message: "Forensic Accounting Check: Beneish M-Score at -2.18 (Accrual warning flag detected).", type: "warning" },
      { timestamp: "08:30:20", source: "Technical Agent", message: "Computed 50-day SMA ($119.50) and 200-day SMA ($98.20). RSI at 68 (near overbought).", type: "info" },
      { timestamp: "08:30:23", source: "Sentiment Agent", message: "Processed 120 social articles. Net sentiment +0.72. Unusual attention volume spike (+220%).", type: "warning" },
      { timestamp: "08:30:26", source: "Bull vs Bear Agent", message: "Created adversarial decision memo. Contradiction flag: fundamental growth capacity vs technical crowding.", type: "warning" },
      { timestamp: "08:30:30", source: "Risk Manager", message: "Restricted list check passed. 1-day 95% VaR evaluated at 2.85%. Kelly sizing limits calculated.", type: "success" },
      { timestamp: "08:30:35", source: "PM Agent", message: "Generated final recommendation memo: Buy. Conviction 85%. Recommended size 4.2%.", type: "success" }
    ],
    macro: {
      regime: "Growth Expansion & Easing",
      details: "Central banks maintaining dovish posture. Tech sector benefiting from continuous liquidity inflows.",
      threatLevel: "Low",
      pmi: 52.4,
      cpi: 2.8,
      yieldSpread10Y2Y: -0.08,
      rates: "4.75% - 5.00%",
      volatilityIndex: 14.2
    },
    fundamentals: {
      thesisSummary: "Dominance in enterprise AI hardware remains unchallenged. Hyperscaler capital expenditure continues to expand, providing secure multi-quarter demand visible in backlog numbers.",
      fairValueLow: 135.00,
      fairValueHigh: 155.00,
      beneishMScore: -2.18,
      beneishInterpretation: "Accrual Warning (potential front-loading of contract revenue). Monitor accounts receivable trend.",
      altmanZScore: 8.42,
      revenueGrowthYoY: 78.5,
      grossMargin: 75.2,
      netMargin: 51.4,
      debtToEquity: 0.18,
      accrualCheck: "Warning"
    },
    technicals: {
      trendState: "Bullish",
      rsi: 68,
      macdState: "Bullish Crossover",
      atr: 3.85,
      support: 118.00,
      resistance: 132.50,
      timingCue: "Enter on minor pullback to 20-day EMA ($124.50) or current breakouts supported by volume.",
      chartPoints: [110, 112, 109, 115, 118, 122, 120, 125, 127.4]
    },
    sentiment: {
      score: 0.72,
      attentionLevel: 88,
      crowdingWarning: "Elevated retail crowding and call-option leverage concentration. High probability of volatility shakeout.",
      newsFeed: [
        { title: "Hyperscalers lift cloud capex guidance again, fueling hardware rally", source: "Bloomberg", age: "2h ago", sentiment: 0.85, relevance: 0.95 },
        { title: "NVIDIA supplier reports production capacity expansion", source: "Reuters", age: "5h ago", sentiment: 0.60, relevance: 0.80 },
        { title: "Short interest in semiconductor ETF hits multi-month low", source: "Financial Times", age: "1d ago", sentiment: 0.45, relevance: 0.70 }
      ]
    },
    adversarial: {
      bullCase: [
        "Unprecedented demand visibility with contract backlogs extending into Q4.",
        "Monopolistic ecosystem lock-in via proprietary CUDA software suite.",
        "High free cash flow generation enables aggressive share buybacks."
      ],
      bearCase: [
        "Customer concentration risk: Top 4 hyperscalers represent 42% of revenue.",
        "Supply constraints in CoWoS packaging could cap short-term delivery upside.",
        "Extremely high valuation multiples leave no margin for execution errors."
      ],
      weakAssumptions: [
        "Assumes hyperscaler software margins justify continuous hardware builds.",
        "Assumes internal chip architectures of customers will not gain material market share before 2027."
      ],
      invalidationTriggers: [
        "Any major hyperscaler announcing a reduction in 2026 capital expenditure budgets.",
        "Beneish M-Score worsening past -1.49 indicating aggressive accounting accruals."
      ],
      catalysts: [
        { event: "TSMC Monthly Revenue Report", date: "Jul 10, 2026", importance: "High", probability: 0.80 },
        { event: "Industry AI Developers Summit", date: "Jul 22, 2026", importance: "Medium", probability: 0.65 },
        { event: "Q2 Earnings & Guidance Update", date: "Aug 18, 2026", importance: "High", probability: 0.95 }
      ]
    },
    risk: {
      var1d95: 2.85,
      concentrationCheck: "Within standard limits (<5% portfolio weight limit). Current exposure 1.2%.",
      restrictedListCheck: "Passed",
      kellyAllocation: 5.8,
      volAllocation: 3.5,
      riskParityAllocation: 4.2,
      stopLoss: 114.00,
      profitTarget: 155.00,
      timeHorizonDays: 90
    },
    pmDefaults: {
      action: "Buy",
      conviction: 85,
      sizing: 4.2,
      timeHorizon: "Medium-term",
      rationale: "Solid fundamental backlog, positive macro tailwinds, and strong sentiment support a standard position entry. Setting stop-loss at $114.00 to protect against volatile shakes."
    },
    lineage: {
      dataSources: [
        "SEC EDGAR Company Filings Repository (10-Q, 10-K)",
        "NASDAQ Global Market Connection (Consolidated Quote Feed)",
        "DOW JONES News service & Financial Sentiment API"
      ],
      modelsUsed: [
        "Reasoning/Synthesis: Gemini 1.5 Pro & GPT-4o",
        "Sentiment Extractor: Fine-tuned FinBERT",
        "Deterministic Valuation: Internal DCF Engine v4.2"
      ],
      promptVersions: [
        { agent: "Fundamental Agent", version: "v2.4.1", file: "prompts/fundamental_v2.json" },
        { agent: "Bull vs Bear Devil's Advocate", version: "v1.9.0", file: "prompts/adversarial_review.json" },
        { agent: "Risk Evaluator", version: "v3.0.2", file: "prompts/risk_constraints.json" }
      ]
    }
  },
  AAPL: {
    symbol: "AAPL",
    name: "Apple Inc.",
    price: 182.30,
    change: -0.80,
    changePercent: -0.44,
    sector: "Technology / Consumer Hardware",
    marketCap: "$2.82T",
    volume: "24.1M",
    averageVolume: "28.5M",
    pipelineLogs: [
      { timestamp: "08:31:01", source: "Data Collector", message: "Connected to SEC filings database & global pricing API.", type: "success" },
      { timestamp: "08:31:03", source: "Data Collector", message: "Ingested SEC Form 4 (insider selling) and news feeds.", type: "info" },
      { timestamp: "08:31:06", source: "Macro Agent", message: "Dovish regime favors premium consumer names. Moderate beta exposure.", type: "info" },
      { timestamp: "08:31:10", source: "Fundamental Agent", message: "Completed fundamental analysis. Balance sheet cash position remains superior. Services revenue growth slowing to +8% YoY.", type: "info" },
      { timestamp: "08:31:12", source: "Fundamental Agent", message: "Accounting Quality: Beneish M-Score at -2.92 (Safe range).", type: "success" },
      { timestamp: "08:31:15", source: "Technical Agent", message: "RSI at 46 (neutral). 200-day SMA ($178.20) acting as major support boundary.", type: "info" },
      { timestamp: "08:31:18", source: "Sentiment Agent", message: "Net sentiment neutral (+0.12). Low social interest crowding.", type: "success" },
      { timestamp: "08:31:22", source: "Bull vs Bear Agent", message: "Identified flat hardware upgrade cycles vs margin resiliency.", type: "info" },
      { timestamp: "08:31:25", source: "Risk Manager", message: "Passed restricted list filter. 1-day 95% VaR at 1.45% (Low risk profile).", type: "success" },
      { timestamp: "08:31:30", source: "PM Agent", message: "Hold rating confirmed. Sizing suggested at current portfolio weight of 2.1%.", type: "success" }
    ],
    macro: {
      regime: "Growth Expansion & Easing",
      details: "Favorable consumer credit conditions, though premium hardware demand faces headwinds in overseas markets.",
      threatLevel: "Low",
      pmi: 52.4,
      cpi: 2.8,
      yieldSpread10Y2Y: -0.08,
      rates: "4.75% - 5.00%",
      volatilityIndex: 14.2
    },
    fundamentals: {
      thesisSummary: "Core hardware business is mature but highly cash-generative. Strong pricing power and massive services ecosystem protect earnings downside, though short-term catalysts for high growth are limited.",
      fairValueLow: 172.00,
      fairValueHigh: 192.00,
      beneishMScore: -2.92,
      beneishInterpretation: "Highly Safe (excellent accounting hygiene and minimal accrual variance).",
      altmanZScore: 5.12,
      revenueGrowthYoY: 4.2,
      grossMargin: 44.8,
      netMargin: 26.1,
      debtToEquity: 1.42,
      accrualCheck: "Pass"
    },
    technicals: {
      trendState: "Neutral",
      rsi: 46,
      macdState: "Neutral/Consolidating",
      atr: 2.10,
      support: 176.00,
      resistance: 188.00,
      timingCue: "Hold current positions. Initiate fresh buying only on deep pullbacks close to major support ($176.00).",
      chartPoints: [185, 184, 186, 183, 182, 180, 181, 183, 182.3]
    },
    sentiment: {
      score: 0.12,
      attentionLevel: 52,
      crowdingWarning: "No crowding alert. Subdued narrative intensity and normal retail participation levels.",
      newsFeed: [
        { title: "App Store margins holding up despite European regulatory actions", source: "Reuters", age: "8h ago", sentiment: 0.30, relevance: 0.85 },
        { title: "Smartphone shipments in major Asian market decline slightly", source: "Nikkei", age: "1d ago", sentiment: -0.25, relevance: 0.90 },
        { title: "Company expands credit lines and buyback program size", source: "Wall Street Journal", age: "3d ago", sentiment: 0.40, relevance: 0.75 }
      ]
    },
    adversarial: {
      bullCase: [
        "Unrivaled hardware customer retention rate (>90% ecosystem stickiness).",
        "High-margin Services division (72% gross margins) growing faster than hardware.",
        "Cash return framework (buybacks and dividends) consistently supports stock floor."
      ],
      bearCase: [
        "Lack of breakthrough consumer hardware updates causing cycle stagnation.",
        "Regulatory antitrust cases in US & EU present structural fee-model risk.",
        "Premium valuation multiple (27x P/E) does not match low single-digit revenue growth."
      ],
      weakAssumptions: [
        "Assumes consumer willingness to pay higher prices for incremental hardware features remains infinite.",
        "Assumes services division will not be structurally decoupled by regulatory force."
      ],
      invalidationTriggers: [
        "Any judicial ruling mandating the full opening of alternative app stores without royalty collections.",
        "Consolidated revenue growth dropping below 0% for consecutive quarters."
      ],
      catalysts: [
        { event: "EU Regulatory Ruling on App Store Fees", date: "Jul 15, 2026", importance: "High", probability: 0.75 },
        { event: "Autumn Product Launch Event", date: "Sep 12, 2026", importance: "Medium", probability: 0.95 },
        { event: "Q3 Earnings Announcement", date: "Oct 26, 2026", importance: "Medium", probability: 0.95 }
      ]
    },
    risk: {
      var1d95: 1.45,
      concentrationCheck: "Within standard limits. Current portfolio weight 2.1%.",
      restrictedListCheck: "Passed",
      kellyAllocation: 3.2,
      volAllocation: 2.8,
      riskParityAllocation: 2.1,
      stopLoss: 172.00,
      profitTarget: 195.00,
      timeHorizonDays: 180
    },
    pmDefaults: {
      action: "Hold",
      conviction: 60,
      sizing: 2.1,
      timeHorizon: "Strategic",
      rationale: "Favorable fundamentals but low immediate catalysts. Hold existing allocation, keeping capital dry for better risk-adjusted growth opportunities elsewhere."
    },
    lineage: {
      dataSources: [
        "SEC EDGAR regulatory portal (10-K, Form 4)",
        "Consolidated Exchange Quote data feeds",
        "Alternative app store tracking databases"
      ],
      modelsUsed: [
        "Reasoning/Synthesis: Claude 3.5 Sonnet",
        "Sentiment Extractor: FinBERT",
        "Deterministic engines: Internal DCF Engine v4.2"
      ],
      promptVersions: [
        { agent: "Fundamental Agent", version: "v2.4.1", file: "prompts/fundamental_v2.json" },
        { agent: "Bull vs Bear Devil's Advocate", version: "v1.9.0", file: "prompts/adversarial_review.json" },
        { agent: "Risk Evaluator", version: "v3.0.2", file: "prompts/risk_constraints.json" }
      ]
    }
  },
  TSLA: {
    symbol: "TSLA",
    name: "Tesla, Inc.",
    price: 178.50,
    change: -3.82,
    changePercent: -2.10,
    sector: "Automotive / Clean Energy",
    marketCap: "$560B",
    volume: "58.2M",
    averageVolume: "62.1M",
    pipelineLogs: [
      { timestamp: "08:32:00", source: "Data Collector", message: "Connected to SEC servers & insurance registry data feeds.", type: "success" },
      { timestamp: "08:32:02", source: "Data Collector", message: "Ingested Chinese EV insurance registry data & social media feeds.", type: "info" },
      { timestamp: "08:32:04", source: "Macro Agent", message: "Tightening policy in primary export markets. Auto loan rates elevated.", type: "warning" },
      { timestamp: "08:32:08", source: "Fundamental Agent", message: "Gross automotive margins dropped to 14.6% (excluding regulatory credits).", type: "warning" },
      { timestamp: "08:32:10", source: "Fundamental Agent", message: "Forensic Accounting: Beneish M-Score is -1.82 (Accrual/Manipulation Alert). High risk threshold.", type: "error" },
      { timestamp: "08:32:13", source: "Technical Agent", message: "RSI at 34 (near oversold). Strong bearish trend below 50-day and 200-day SMAs.", type: "warning" },
      { timestamp: "08:32:16", source: "Sentiment Agent", message: "Net sentiment bearish (-0.45). Extremely high attention index (92/100).", type: "warning" },
      { timestamp: "08:32:20", source: "Bull vs Bear Agent", message: "Identified conflict: Autonomous FSD long-term valuation vs structural automotive margins contraction.", type: "warning" },
      { timestamp: "08:32:23", source: "Risk Manager", message: "Restricted List check passed. 1-day 95% VaR at 3.92% (High Volatility risk). Sizing limits reduced.", type: "warning" },
      { timestamp: "08:32:28", source: "PM Agent", message: "Generate output: Not Buy. Thesis invalidated on automotive margins drop and accounting warnings.", type: "error" }
    ],
    macro: {
      regime: "Tightening Policy & High Beta Threat",
      details: "High interest rates impacting auto financing terms, slowing down consumer discretionary vehicle cycles.",
      threatLevel: "High",
      pmi: 49.8,
      cpi: 3.2,
      yieldSpread10Y2Y: -0.15,
      rates: "5.25% - 5.50%",
      volatilityIndex: 18.5
    },
    fundamentals: {
      thesisSummary: "Core automotive margins are deteriorating due to aggressive pricing discounting globally. While long-term autonomous driving tech and energy storage present call options, near-term capital demands remain massive.",
      fairValueLow: 140.00,
      fairValueHigh: 165.00,
      beneishMScore: -1.82,
      beneishInterpretation: "High Manipulation Risk (unusual deferred revenue releases and capitalized R&D items).",
      altmanZScore: 3.82,
      revenueGrowthYoY: -1.5,
      grossMargin: 16.2,
      netMargin: 8.4,
      debtToEquity: 0.05,
      accrualCheck: "Fail"
    },
    technicals: {
      trendState: "Bearish",
      rsi: 34,
      macdState: "Bearish Expansion",
      atr: 5.60,
      support: 170.00,
      resistance: 198.00,
      timingCue: "Stay sidelines. Severe technical breakdown. Do not attempt to catch falling knife.",
      chartPoints: [205, 198, 192, 185, 180, 183, 175, 181, 178.5]
    },
    sentiment: {
      score: -0.45,
      attentionLevel: 92,
      crowdingWarning: "Extreme retail option activity and public controversy exposure. Highly crowded negative consensus.",
      newsFeed: [
        { title: "EV insurance registrations in major Asian hub decline 12% MoM", source: "Reuters", age: "4h ago", sentiment: -0.65, relevance: 0.95 },
        { title: "Price cuts announced for premium Model S and Y configurations in Europe", source: "Bloomberg", age: "12h ago", sentiment: -0.40, relevance: 0.85 },
        { title: "CEO reiterates commitment to autonomous robotaxi launch timeline", source: "CNBC", age: "2d ago", sentiment: 0.50, relevance: 0.70 }
      ]
    },
    adversarial: {
      bullCase: [
        "Energy Storage division growing at triple digits, adding higher margin recurring mix.",
        "Proprietary Dojo compute and massive real-world video training data speed up FSD solutions.",
        "Virtually debt-free balance sheet allows self-funding of future Gigafactory expansions."
      ],
      bearCase: [
        "Automotive gross margins continue compression, dropping cash flow run-rates.",
        "Overcapacity in global EV manufacturing forcing industry-wide price wars.",
        "Corporate governance risks and CEO distraction distract from product roadmap."
      ],
      weakAssumptions: [
        "Assumes autonomous software regulatory approvals will occur in all major geographies within 12 months.",
        "Assumes legacy auto margins will stabilize above 15%."
      ],
      invalidationTriggers: [
        "Quarterly automotive gross margins (excluding credits) falling below 12%.",
        "Key artificial intelligence engineering personnel departures."
      ],
      catalysts: [
        { event: "Monthly Delivery Reports", date: "Jul 02, 2026", importance: "High", probability: 0.90 },
        { event: "Robotaxi Official Design Reveal", date: "Aug 08, 2026", importance: "High", probability: 0.85 },
        { event: "Q2 Cash Flow & Margin Update", date: "Oct 18, 2026", importance: "High", probability: 0.95 }
      ]
    },
    risk: {
      var1d95: 3.92,
      concentrationCheck: "High correlation to broader momentum factor. Restrict to <2.5% max size.",
      restrictedListCheck: "Passed",
      kellyAllocation: 0.0,
      volAllocation: 1.2,
      riskParityAllocation: 0.8,
      stopLoss: 165.00,
      profitTarget: 210.00,
      timeHorizonDays: 45
    },
    pmDefaults: {
      action: "Not Buy",
      conviction: 20,
      sizing: 0.0,
      timeHorizon: "Tactical",
      rationale: "Fails multiple critical fundamental tests (automotive margins compression and Beneish M-Score warning). High beta market environment and bearish technicals suggest significant risk. Recommend Not Buy."
    },
    lineage: {
      dataSources: [
        "SEC filing retrieval service (Form 10-Q)",
        "Global automotive registration dashboards",
        "Social text scraped from retail trading forums"
      ],
      modelsUsed: [
        "Reasoning/Synthesis: Llama-3-70b-instruct",
        "Risk checks: Deterministic Python optimizer v2.1"
      ],
      promptVersions: [
        { agent: "Fundamental Agent", version: "v2.4.1", file: "prompts/fundamental_v2.json" },
        { agent: "Bull vs Bear Devil's Advocate", version: "v1.9.0", file: "prompts/adversarial_review.json" },
        { agent: "Risk Evaluator", version: "v3.0.2", file: "prompts/risk_constraints.json" }
      ]
    }
  },
  MSFT: {
    symbol: "MSFT",
    name: "Microsoft Corporation",
    price: 418.60,
    change: 5.10,
    changePercent: 1.23,
    sector: "Technology / Infrastructure & SaaS",
    marketCap: "$3.12T",
    volume: "18.4M",
    averageVolume: "20.1M",
    pipelineLogs: [
      { timestamp: "08:33:00", source: "Data Collector", message: "Initialized endpoints to SEC filings and Azure cloud data portals.", type: "success" },
      { timestamp: "08:33:02", source: "Data Collector", message: "Ingested 10-Q filing, Office Copilot metrics, and developer surveys.", type: "info" },
      { timestamp: "08:33:05", source: "Macro Agent", message: "Dovish rate regime supports high SaaS cash multiples. Low beta relative to tech peers.", type: "info" },
      { timestamp: "08:33:08", source: "Fundamental Agent", message: "Azure cloud revenues growing +29% YoY. Copilot adoption expanding in enterprise.", type: "success" },
      { timestamp: "08:33:10", source: "Fundamental Agent", message: "Forensic Accounting: Beneish M-Score at -2.85 (Safe range).", type: "success" },
      { timestamp: "08:33:13", source: "Technical Agent", message: "RSI at 56. Consolidated structure breakout above 50-day SMA ($412.00).", type: "success" },
      { timestamp: "08:33:16", source: "Sentiment Agent", message: "Net sentiment bullish (+0.58). Moderate retail and high institutional interest.", type: "success" },
      { timestamp: "08:33:20", source: "Bull vs Bear Agent", message: "Adversarial review balanced: Azure market share gains vs CAPEX spend velocity.", type: "info" },
      { timestamp: "08:33:24", source: "Risk Manager", message: "Restricted List check passed. 1-day 95% VaR at 1.82%. Kelly allocation at 6.1%.", type: "success" },
      { timestamp: "08:33:29", source: "PM Agent", message: "Generated signal: Buy. Conviction 82%. Sizing suggestion 4.5%.", type: "success" }
    ],
    macro: {
      regime: "Growth Expansion & Easing",
      details: "Stable corporate IT spend budgets and supportive rate environments benefit SaaS valuation models.",
      threatLevel: "Low",
      pmi: 52.4,
      cpi: 2.8,
      yieldSpread10Y2Y: -0.08,
      rates: "4.75% - 5.00%",
      volatilityIndex: 14.2
    },
    fundamentals: {
      thesisSummary: "Dominant enterprise software suite remains highly sticky. Azure cloud gains continuous share in enterprise AI migrations, offsetting mature legacy software licensing declines.",
      fairValueLow: 410.00,
      fairValueHigh: 460.00,
      beneishMScore: -2.85,
      beneishInterpretation: "Highly Safe (stable, predictable software recurring margins).",
      altmanZScore: 6.94,
      revenueGrowthYoY: 14.8,
      grossMargin: 69.4,
      netMargin: 35.2,
      debtToEquity: 0.24,
      accrualCheck: "Pass"
    },
    technicals: {
      trendState: "Bullish",
      rsi: 56,
      macdState: "Bullish Crossover",
      atr: 6.80,
      support: 405.00,
      resistance: 432.00,
      timingCue: "Safe to initiate/add positions at current price or on minor consolidations around the $412.00 breakout support level.",
      chartPoints: [395, 398, 402, 401, 405, 410, 408, 415, 418.6]
    },
    sentiment: {
      score: 0.58,
      attentionLevel: 68,
      crowdingWarning: "Moderate institutional consolidation. Low retail speculative bubble risk.",
      newsFeed: [
        { title: "Azure cloud wins multi-billion dollar enterprise migration contract", source: "Bloomberg", age: "6h ago", sentiment: 0.80, relevance: 0.90 },
        { title: "Survey shows 70% of Fortune 500 active users upgraded to AI Copilot features", source: "Reuters", age: "18h ago", sentiment: 0.65, relevance: 0.85 },
        { title: "Enterprise software licensing spending expected to grow 8% globally in 2026", source: "Gartner", age: "2d ago", sentiment: 0.40, relevance: 0.70 }
      ]
    },
    adversarial: {
      bullCase: [
        "Uncontested pricing power in enterprise suite with high-margin AI Copilot additions ($30/user/mo).",
        "Consistent cloud infrastructure growth powered by massive enterprise database migration stickiness.",
        "Superior credit rating and cash flow profile shields company from macro shocks."
      ],
      bearCase: [
        "Unprecedented capital expenditure requirements to build custom data centers.",
        "Increased competitive pressure in cloud AI from open-source LLMs.",
        "Slow growth in consumer-facing hardware and gaming divisions."
      ],
      weakAssumptions: [
        "Assumes corporate clients will achieve measurable ROI on Copilot features before contract renewals.",
        "Assumes server hardware efficiency improvements will keep pace with compute demand."
      ],
      invalidationTriggers: [
        "Azure growth decelerating below 25% YoY for two consecutive periods.",
        "Beneish M-Score slipping below -1.49 indicating accounting manipulation risk."
      ],
      catalysts: [
        { event: "Global Developer Conference Keynote", date: "Jul 18, 2026", importance: "Medium", probability: 0.90 },
        { event: "Q2 Financial Earnings Report", date: "Jul 28, 2026", importance: "High", probability: 0.95 },
        { event: "Corporate IT Spend Annual Survey", date: "Sep 05, 2026", importance: "Medium", probability: 0.80 }
      ]
    },
    risk: {
      var1d95: 1.82,
      concentrationCheck: "Within standard limits. Current portfolio weight 3.5%.",
      restrictedListCheck: "Passed",
      kellyAllocation: 6.1,
      volAllocation: 4.8,
      riskParityAllocation: 4.5,
      stopLoss: 395.00,
      profitTarget: 470.00,
      timeHorizonDays: 120
    },
    pmDefaults: {
      action: "Buy",
      conviction: 82,
      sizing: 4.5,
      timeHorizon: "Strategic",
      rationale: "Favorable fundamentals, stable recurring software base, and strong cloud momentum justify a strategic long allocation. Sizing at 4.5% to target risk budget limits with a stop-loss set at $395.00."
    },
    lineage: {
      dataSources: [
        "SEC EDGAR database service (10-Q)",
        "Consolidated Exchange Quote data feeds",
        "SaaS developer telemetry data repositories"
      ],
      modelsUsed: [
        "Reasoning/Synthesis: Gemini 1.5 Pro",
        "Sentiment Extractor: FinBERT",
        "Risk models: Deterministic Python optimizer v2.1"
      ],
      promptVersions: [
        { agent: "Fundamental Agent", version: "v2.4.1", file: "prompts/fundamental_v2.json" },
        { agent: "Bull vs Bear Devil's Advocate", version: "v1.9.0", file: "prompts/adversarial_review.json" },
        { agent: "Risk Evaluator", version: "v3.0.2", file: "prompts/risk_constraints.json" }
      ]
    }
  }
};

export default function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>("NVDA");
  const [activeTab, setActiveTab] = useState<string>("specialists"); // specialists, adversarial, risk, pm
  
  // Pipeline simulation states
  const [pipelineStep, setPipelineStep] = useState<number>(5); // 0 to 5 (0: Data, 1: Signal, 2: Specialist, 3: Adv, 4: Risk, 5: PM)
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [consoleLogs, setConsoleLogs] = useState<typeof STOCKS_DATA["NVDA"]["pipelineLogs"]>([]);
  
  // PM Interactive Overrides
  const [selectedAction, setSelectedAction] = useState<string>("Buy");
  const [selectedConviction, setSelectedConviction] = useState<number>(85);
  const [selectedSizing, setSelectedSizing] = useState<number>(4.2);
  const [selectedHorizon, setSelectedHorizon] = useState<string>("Medium-term");
  const [selectedStopLoss, setSelectedStopLoss] = useState<number>(114.00);
  const [selectedProfitTarget, setSelectedProfitTarget] = useState<number>(155.00);
  const [auditComment, setAuditComment] = useState<string>("");
  const [invalidationChecks, setInvalidationChecks] = useState<Record<string, boolean>>({});

  const consoleEndRef = useRef<HTMLDivElement>(null);
  const currentStock = STOCKS_DATA[selectedSymbol];

  // Sync state when stock selection changes
  useEffect(() => {
    const stock = STOCKS_DATA[selectedSymbol];
    setSelectedAction(stock.pmDefaults.action);
    setSelectedConviction(stock.pmDefaults.conviction);
    setSelectedSizing(stock.pmDefaults.sizing);
    setSelectedHorizon(stock.pmDefaults.timeHorizon);
    setSelectedStopLoss(stock.risk.stopLoss);
    setSelectedProfitTarget(stock.risk.profitTarget);
    setConsoleLogs(stock.pipelineLogs);
    setPipelineStep(5);
    setIsSimulating(false);
    
    // Clear invalidation checkboxes
    const checks: Record<string, boolean> = {};
    stock.adversarial.invalidationTriggers.forEach((_, index) => {
      checks[`${selectedSymbol}_${index}`] = false;
    });
    setInvalidationChecks(checks);
  }, [selectedSymbol]);

  // Scroll console to bottom
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [consoleLogs]);

  // Simulate Pipeline Run
  const handleRunSimulation = () => {
    setIsSimulating(true);
    setPipelineStep(0);
    setConsoleLogs([]);
    
    let currentStep = 0;
    const interval = setInterval(() => {
      if (currentStep > 5) {
        clearInterval(interval);
        setIsSimulating(false);
        return;
      }
      
      setPipelineStep(currentStep);
      
      // Append logs corresponding to this step
      const stepLogs = currentStock.pipelineLogs.filter((log, index) => {
        if (currentStep === 0 && index <= 2) return true; // Data ingest
        if (currentStep === 1 && index === 3) return true; // Signal Ingest / Macro
        if (currentStep === 2 && index >= 4 && index <= 7) return true; // Specialists
        if (currentStep === 3 && index === 8) return true; // Adversarial
        if (currentStep === 4 && index === 9) return true; // Risk
        if (currentStep === 5 && index === 10) return true; // PM Decision
        return false;
      });

      setConsoleLogs(prev => [...prev, ...stepLogs]);
      currentStep += 1;
    }, 1200);
  };

  const handleCheckboxChange = (key: string) => {
    setInvalidationChecks(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Calculate dynamic parameters based on Sizing override
  // Sizing changes update concentration risk level and portfolio volatility
  const computedRiskContribution = (selectedSizing * 0.35).toFixed(2);
  const getRiskLabel = (size: number) => {
    if (size === 0) return { label: "No Exposure", color: "text-slate-400 bg-slate-800/40" };
    if (size < 2.5) return { label: "Low Risk Contribution", color: "text-emerald-400 bg-emerald-950/30" };
    if (size <= 5.0) return { label: "Moderate Risk Contribution", color: "text-amber-400 bg-amber-950/30" };
    return { label: "CRITICAL Concentration Override Flagged", color: "text-red-400 bg-red-950/30 font-bold border border-red-800/30 animate-pulse-glow" };
  };
  const currentRiskStatus = getRiskLabel(selectedSizing);

  // Stop loss and target pricing risk-reward calculation
  const distanceToStop = currentStock.price - selectedStopLoss;
  const distanceToTarget = selectedProfitTarget - currentStock.price;
  const riskRewardRatio = distanceToStop > 0 ? (distanceToTarget / distanceToStop).toFixed(2) : "0.00";

  return (
    <div className="min-h-screen bg-[#0b0f19] flex flex-col antialiased selection:bg-blue-600 selection:text-white">
      
      {/* ==========================================
          HEADER PANEL & STOCK SELECTOR
          ========================================== */}
      <header className="border-b border-slate-800/60 bg-[#0e1526]/80 backdrop-blur-md sticky top-0 z-40 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-sm tracking-wider text-white shadow-lg shadow-blue-500/20">
            AG
          </div>
          <div>
            <h1 className="text-lg font-bold font-outfit bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">
              Antigravity Multi-Agent Research Desk
            </h1>
            <p className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold">
              Institutional AI Equity Decision System
            </p>
          </div>
        </div>

        {/* Global Stock Ingestion Controller */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 bg-[#0f172a] rounded-lg p-1 border border-slate-800/80">
            {Object.keys(STOCKS_DATA).map((sym) => (
              <button
                key={sym}
                onClick={() => setSelectedSymbol(sym)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold tracking-wide transition-all ${
                  selectedSymbol === sym
                    ? "bg-slate-800 text-slate-100 shadow-sm border border-slate-700/60"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                {sym}
              </button>
            ))}
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={isSimulating}
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white disabled:opacity-50 transition-all shadow-md shadow-blue-500/10 active:scale-95"
          >
            {isSimulating ? (
              <>
                <svg className="animate-spin h-3.5 w-3.5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <span>Orchestrating...</span>
              </>
            ) : (
              <>
                <svg className="w-3.5 h-3.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
                <span>Run Orchestration</span>
              </>
            )}
          </button>

          <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-400 bg-slate-900 border border-slate-800/80 rounded-lg px-3 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>PORT 8000 LIVE</span>
          </div>
        </div>
      </header>

      {/* ==========================================
          PIPELINE STEPS ORCHESTRATOR
          ========================================== */}
      <section className="bg-[#0f172a]/40 border-b border-slate-800/40 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 overflow-x-auto">
          {[
            { label: "Data Ingestion", desc: "API Ingest & Deduplicate" },
            { label: "Signal Extraction", desc: "Regime & Quant Filters" },
            { label: "Specialist Agents", desc: "Macro, Fund, Tech, Sent" },
            { label: "Adversarial review", desc: "Bull vs Bear Debate" },
            { label: "Risk & Compliance", desc: "Limits & Sizing Engine" },
            { label: "PM Decision", desc: "Consensus Synthesis" }
          ].map((step, idx) => {
            const isCompleted = idx < pipelineStep;
            const isActive = idx === pipelineStep;
            return (
              <div key={idx} className="flex-1 min-w-[130px] flex items-center gap-3">
                <div className="flex flex-col gap-1 w-full">
                  <div className="flex items-center justify-between">
                    <span className={`text-[10px] uppercase font-bold tracking-wider ${
                      isActive ? "text-blue-400 font-extrabold" : isCompleted ? "text-slate-400" : "text-slate-600"
                    }`}>
                      Stage 0{idx + 1}
                    </span>
                    {isCompleted ? (
                      <span className="text-emerald-500">
                        <svg className="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      </span>
                    ) : isActive ? (
                      <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse-glow" />
                    ) : (
                      <span className="w-1.5 h-1.5 bg-slate-800 rounded-full" />
                    )}
                  </div>
                  <div className="h-1 w-full rounded-full bg-slate-800 overflow-hidden">
                    <div className={`h-full transition-all duration-700 ${
                      isActive ? "w-1/2 bg-blue-500 animate-pulse" : isCompleted ? "w-full bg-emerald-500" : "w-0"
                    }`} />
                  </div>
                  <div>
                    <h4 className={`text-xs font-semibold ${isActive ? "text-blue-400" : "text-slate-200"}`}>
                      {step.label}
                    </h4>
                    <p className="text-[10px] text-slate-500 truncate">{step.desc}</p>
                  </div>
                </div>
                {idx < 5 && (
                  <span className="text-slate-800 hidden md:block select-none text-lg font-bold">
                    &rarr;
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ==========================================
          MAIN LAYOUT GRID
          ========================================== */}
      <main className="flex-1 max-w-[1700px] w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* ==========================================
            LEFT COLUMN (WIDER): DETAILED STAGES
            ========================================== */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          
          {/* ACTIVE STOCK CARD HERO */}
          <div className="gradient-border-panel p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="px-4 py-2.5 bg-slate-800/80 rounded-xl border border-slate-700/60 font-outfit font-extrabold text-2xl tracking-wider text-slate-100 shadow-inner">
                {currentStock.symbol}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold font-outfit text-slate-100">{currentStock.name}</h2>
                  <span className="text-xs text-slate-400 font-semibold px-2 py-0.5 bg-slate-900 border border-slate-800/60 rounded">
                    {currentStock.sector}
                  </span>
                </div>
                <div className="flex items-center gap-3 mt-1 text-sm font-semibold">
                  <span className="text-slate-400 font-medium">Cap: {currentStock.marketCap}</span>
                  <span className="w-1 h-1 rounded-full bg-slate-700" />
                  <span className="text-slate-400 font-medium">Vol: {currentStock.volume} / {currentStock.averageVolume} avg</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 sm:text-right">
              <div>
                <div className="text-2xl font-black font-outfit tracking-tight text-slate-50">
                  ${currentStock.price.toFixed(2)}
                </div>
                <div className={`flex items-center gap-1.5 text-sm font-bold justify-end ${
                  currentStock.change >= 0 ? "text-emerald-400" : "text-red-400"
                }`}>
                  <span>{currentStock.change >= 0 ? "+" : ""}{currentStock.change.toFixed(2)}</span>
                  <span>({currentStock.changePercent >= 0 ? "+" : ""}{currentStock.changePercent.toFixed(2)}%)</span>
                </div>
              </div>
            </div>
          </div>

          {/* MAIN WORKING TABS CONTROL */}
          <div className="flex border-b border-slate-800">
            {[
              { id: "specialists", label: "Specialist Agents", badge: "04" },
              { id: "adversarial", label: "Adversarial Review", badge: "DEBATE" },
              { id: "risk", label: "Risk & Position Sizing", badge: "LIMITS" },
              { id: "pm", label: "PM Decision Terminal", badge: "COMMIT" }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-3 border-b-2 text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-400 bg-blue-500/5 font-extrabold"
                    : "border-transparent text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>{tab.label}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                  activeTab === tab.id ? "bg-blue-950 text-blue-400 border border-blue-800/40" : "bg-slate-900 text-slate-500"
                }`}>
                  {tab.badge}
                </span>
              </button>
            ))}
          </div>

          {/* TAB CONTENT: 1. SPECIALIST AGENTS */}
          {activeTab === "specialists" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* FUNDAMENTAL AGENT CARD */}
              <div className="gradient-border-panel p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="p-1 rounded bg-indigo-950 text-indigo-400 border border-indigo-900/40">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </span>
                      <h3 className="font-bold text-sm tracking-wide text-slate-100">Fundamental Research Agent</h3>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">FR-014 - FR-020</span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-medium">
                    {currentStock.fundamentals.thesisSummary}
                  </p>

                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div className="bg-[#0f172a] p-3 rounded-lg border border-slate-800">
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">DCF Fair Value Range</span>
                      <span className="text-sm font-extrabold text-slate-200 mt-1 block">
                        ${currentStock.fundamentals.fairValueLow.toFixed(2)} - ${currentStock.fundamentals.fairValueHigh.toFixed(2)}
                      </span>
                    </div>

                    <div className="bg-[#0f172a] p-3 rounded-lg border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Beneish M-Score</span>
                        <span className={`w-2 h-2 rounded-full ${
                          currentStock.fundamentals.accrualCheck === "Pass"
                            ? "bg-emerald-500"
                            : currentStock.fundamentals.accrualCheck === "Warning"
                            ? "bg-amber-500"
                            : "bg-red-500 animate-pulse"
                        }`} />
                      </div>
                      <span className="text-sm font-extrabold text-slate-200 mt-1 block">
                        {currentStock.fundamentals.beneishMScore.toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Accounting red flag note */}
                  <div className="mt-3 px-3 py-2 bg-slate-900 border border-slate-800/80 rounded-md">
                    <p className="text-[11px] text-slate-400 font-semibold leading-relaxed">
                      <span className="text-amber-400 font-bold">Accounting Audit:</span> {currentStock.fundamentals.beneishInterpretation}
                    </p>
                  </div>
                </div>

                <div className="mt-5 border-t border-slate-800/60 pt-3 flex justify-between text-[11px] font-mono text-slate-500">
                  <span>Growth: +{currentStock.fundamentals.revenueGrowthYoY}% YoY</span>
                  <span>Gross Margin: {currentStock.fundamentals.grossMargin}%</span>
                  <span>D/E: {currentStock.fundamentals.debtToEquity}</span>
                </div>
              </div>

              {/* MACRO / REGIME AGENT CARD */}
              <div className="gradient-border-panel p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="p-1 rounded bg-teal-950 text-teal-400 border border-teal-900/40">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                        </svg>
                      </span>
                      <h3 className="font-bold text-sm tracking-wide text-slate-100">Macro / Regime Agent</h3>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">FR-008 - FR-013</span>
                  </div>

                  <div className="mb-4">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Current Classified Regime</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-base font-extrabold font-outfit text-slate-200">
                        {currentStock.macro.regime}
                      </span>
                      <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                        currentStock.macro.threatLevel === "Low" 
                          ? "bg-emerald-950/40 text-emerald-400 border border-emerald-800/30"
                          : "bg-red-950/40 text-red-400 border border-red-800/30"
                      }`}>
                        Threat: {currentStock.macro.threatLevel}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-medium">
                    {currentStock.macro.details}
                  </p>

                  <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                    <div className="bg-[#0f172a] p-2.5 rounded border border-slate-800/60">
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wide block">PMI Index</span>
                      <span className="text-xs font-black text-slate-200 block mt-0.5">{currentStock.macro.pmi}</span>
                    </div>
                    <div className="bg-[#0f172a] p-2.5 rounded border border-slate-800/60">
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wide block">Core CPI</span>
                      <span className="text-xs font-black text-slate-200 block mt-0.5">{currentStock.macro.cpi}%</span>
                    </div>
                    <div className="bg-[#0f172a] p-2.5 rounded border border-slate-800/60">
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wide block">10Y-2Y Spread</span>
                      <span className="text-xs font-black text-slate-200 block mt-0.5">{currentStock.macro.yieldSpread10Y2Y}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 border-t border-slate-800/60 pt-3 flex justify-between text-[11px] font-mono text-slate-500">
                  <span>Policy Rates: {currentStock.macro.rates}</span>
                  <span>VIX: {currentStock.macro.volatilityIndex}</span>
                </div>
              </div>

              {/* TECHNICAL ANALYST AGENT CARD */}
              <div className="gradient-border-panel p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="p-1 rounded bg-blue-950 text-blue-400 border border-blue-900/40">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M7 12l3-3 3 3 4-4M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                      </span>
                      <h3 className="font-bold text-sm tracking-wide text-slate-100">Technical Analyst Agent</h3>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">FR-021 - FR-026</span>
                  </div>

                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Trend Direction</span>
                      <span className={`text-sm font-extrabold block mt-0.5 ${
                        currentStock.technicals.trendState === "Bullish" ? "text-emerald-400" : currentStock.technicals.trendState === "Bearish" ? "text-red-400" : "text-slate-400"
                      }`}>
                        {currentStock.technicals.trendState}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">RSI (14)</span>
                      <span className={`text-sm font-extrabold block mt-0.5 ${
                        currentStock.technicals.rsi >= 70 ? "text-red-400" : currentStock.technicals.rsi <= 30 ? "text-emerald-400" : "text-slate-200"
                      }`}>
                        {currentStock.technicals.rsi}
                      </span>
                    </div>
                  </div>

                  {/* MINI SVG PRICE SPARKLINE CHART */}
                  <div className="bg-[#0b0f19] h-20 rounded border border-slate-800/80 p-1 flex items-center relative overflow-hidden">
                    <div className="absolute top-2 left-2 text-[9px] text-slate-500 font-mono uppercase">9-Day Sparkline</div>
                    <svg className="w-full h-full pt-4 overflow-visible" viewBox="0 0 100 30" preserveAspectRatio="none">
                      <polyline
                        fill="none"
                        stroke="#3b82f6"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        points={currentStock.technicals.chartPoints
                          .map((val, idx) => {
                            const minVal = Math.min(...currentStock.technicals.chartPoints);
                            const maxVal = Math.max(...currentStock.technicals.chartPoints);
                            const x = (idx / (currentStock.technicals.chartPoints.length - 1)) * 100;
                            const y = 30 - ((val - minVal) / (maxVal - minVal)) * 22 - 4; // Margin adjustments
                            return `${x},${y}`;
                          })
                          .join(" ")}
                      />
                    </svg>
                  </div>

                  <div className="mt-3 px-3 py-2 bg-slate-900 border border-slate-800/80 rounded-md">
                    <p className="text-[11px] text-slate-400 font-semibold leading-relaxed">
                      <span className="text-blue-400 font-bold">Timing Cue:</span> {currentStock.technicals.timingCue}
                    </p>
                  </div>
                </div>

                <div className="mt-5 border-t border-slate-800/60 pt-3 flex justify-between text-[11px] font-mono text-slate-500">
                  <span>Support: ${currentStock.technicals.support.toFixed(2)}</span>
                  <span>Resistance: ${currentStock.technicals.resistance.toFixed(2)}</span>
                  <span>ATR: {currentStock.technicals.atr}</span>
                </div>
              </div>

              {/* SENTIMENT & NEWS ANALYST AGENT CARD */}
              <div className="gradient-border-panel p-5 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="p-1 rounded bg-pink-950 text-pink-400 border border-pink-900/40">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1M19 20a2 2 0 002-2V8a2 2 0 00-2-2h-5" />
                        </svg>
                      </span>
                      <h3 className="font-bold text-sm tracking-wide text-slate-100">Sentiment & News Agent</h3>
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono">FR-027 - FR-033</span>
                  </div>

                  <div className="mb-4 grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Net Sentiment Score</span>
                      <div className="flex items-center gap-1.5 mt-0.5">
                        <span className={`text-base font-extrabold ${
                          currentStock.sentiment.score > 0.3 ? "text-emerald-400" : currentStock.sentiment.score < -0.2 ? "text-red-400" : "text-slate-400"
                        }`}>
                          {currentStock.sentiment.score > 0 ? "+" : ""}{currentStock.sentiment.score.toFixed(2)}
                        </span>
                        <span className="text-xs text-slate-500">(-1 to +1)</span>
                      </div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Crowding Attention</span>
                      <span className="text-base font-extrabold text-slate-200 block mt-0.5">
                        {currentStock.sentiment.attentionLevel} <span className="text-xs text-slate-500">/ 100</span>
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-2">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">Key Narrative Headlines</span>
                    {currentStock.sentiment.newsFeed.map((news, index) => (
                      <div key={index} className="bg-[#0f172a] p-2 rounded border border-slate-800/80 flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <p className="text-[11px] font-semibold text-slate-300 line-clamp-1">{news.title}</p>
                          <div className="flex items-center gap-1 text-[9px] text-slate-500 font-mono mt-0.5">
                            <span>{news.source}</span>
                            <span>&bull;</span>
                            <span>{news.age}</span>
                          </div>
                        </div>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                          news.sentiment > 0.2 ? "bg-emerald-950 text-emerald-400" : news.sentiment < -0.1 ? "bg-red-950 text-red-400" : "bg-slate-900 text-slate-400"
                        }`}>
                          {news.sentiment > 0 ? "+" : ""}{news.sentiment.toFixed(2)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-4 pt-2 border-t border-slate-800/40 text-[10px] text-slate-500 font-semibold leading-relaxed">
                  <span className="text-pink-400">Crowding Index:</span> {currentStock.sentiment.crowdingWarning}
                </div>
              </div>

            </div>
          )}

          {/* TAB CONTENT: 2. ADVERSARIAL BULL VS BEAR */}
          {activeTab === "adversarial" && (
            <div className="flex flex-col gap-6">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* BULL CASE PANEL */}
                <div className="gradient-border-panel p-5 gradient-border-panel-bullish">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
                    <span className="text-emerald-500 text-sm font-bold">▲</span>
                    <h3 className="font-bold text-sm tracking-wide text-slate-100">Optimistic Consensus (Bull Thesis)</h3>
                  </div>
                  <ul className="flex flex-col gap-3 list-disc pl-4 text-xs text-slate-300 leading-relaxed font-medium">
                    {currentStock.adversarial.bullCase.map((pt, idx) => (
                      <li key={idx}>{pt}</li>
                    ))}
                  </ul>
                </div>

                {/* BEAR CASE PANEL */}
                <div className="gradient-border-panel p-5 gradient-border-panel-bearish">
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-3 mb-4">
                    <span className="text-red-500 text-sm font-bold">▼</span>
                    <h3 className="font-bold text-sm tracking-wide text-slate-100">Adversarial Challenges (Bear Thesis)</h3>
                  </div>
                  <ul className="flex flex-col gap-3 list-disc pl-4 text-xs text-slate-300 leading-relaxed font-medium">
                    {currentStock.adversarial.bearCase.map((pt, idx) => (
                      <li key={idx}>{pt}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* CRITICAL THESIS ASSUMPTIONS & INVALIDATIONS */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* WEAK ASSUMPTIONS */}
                <div className="bg-[#0f172a]/60 border border-slate-800 rounded-xl p-5">
                  <h4 className="text-xs uppercase tracking-wider font-extrabold text-amber-400 mb-3">
                    Unverified Thesis Vulnerabilities
                  </h4>
                  <ul className="flex flex-col gap-2.5">
                    {currentStock.adversarial.weakAssumptions.map((item, idx) => (
                      <div key={idx} className="bg-slate-900 border border-slate-800/80 rounded p-3 flex gap-2.5 items-start">
                        <span className="text-amber-500 text-xs font-bold font-mono">#{idx+1}</span>
                        <p className="text-xs text-slate-300 font-medium leading-normal">{item}</p>
                      </div>
                    ))}
                  </ul>
                </div>

                {/* THESIS INVALIDATION CHECKS */}
                <div className="bg-[#0f172a]/60 border border-slate-800 rounded-xl p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs uppercase tracking-wider font-extrabold text-red-400">
                      Thesis Invalidation Triggers
                    </h4>
                    <span className="text-[10px] text-slate-500 font-semibold uppercase">PM Checklist</span>
                  </div>
                  <div className="flex flex-col gap-2.5">
                    {currentStock.adversarial.invalidationTriggers.map((trigger, idx) => {
                      const checkKey = `${selectedSymbol}_${idx}`;
                      const isChecked = invalidationChecks[checkKey] || false;
                      return (
                        <div
                          key={idx}
                          onClick={() => handleCheckboxChange(checkKey)}
                          className={`border rounded p-3 flex items-center justify-between cursor-pointer transition-all ${
                            isChecked
                              ? "bg-red-950/20 border-red-800/80 text-red-200"
                              : "bg-slate-900 border-slate-800/80 hover:border-slate-700/60 text-slate-300"
                          }`}
                        >
                          <p className="text-xs font-semibold select-none pr-4">{trigger}</p>
                          <div className={`w-4 h-4 rounded flex items-center justify-center border transition-all ${
                            isChecked ? "bg-red-500 border-red-500 text-white" : "border-slate-700"
                          }`}>
                            {isChecked && (
                              <svg className="w-3 h-3 text-white" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

              </div>

              {/* CATALYST TIMELINE */}
              <div className="bg-[#0f172a]/60 border border-slate-800 rounded-xl p-5">
                <h4 className="text-xs uppercase tracking-wider font-extrabold text-blue-400 mb-4">
                  Upcoming Catalyst Event Timelines (FR-067)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {currentStock.adversarial.catalysts.map((cat, idx) => (
                    <div key={idx} className="bg-slate-900 border border-slate-800/80 p-3.5 rounded-lg flex flex-col justify-between h-28">
                      <div>
                        <div className="flex items-center justify-between">
                          <span className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
                            cat.importance === "High" ? "bg-red-950 text-red-400" : "bg-slate-800 text-slate-400"
                          }`}>
                            {cat.importance}
                          </span>
                          <span className="text-[10px] text-slate-500 font-mono">Prob: {(cat.probability*100).toFixed(0)}%</span>
                        </div>
                        <h5 className="text-xs font-bold text-slate-200 mt-2 line-clamp-1">{cat.event}</h5>
                      </div>
                      <span className="text-[11px] font-mono text-blue-400 font-bold block mt-3">{cat.date}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}

          {/* TAB CONTENT: 3. RISK & COMPLIANCE */}
          {activeTab === "risk" && (
            <div className="flex flex-col gap-6">
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* VALUE AT RISK */}
                <div className="bg-[#0f172a]/60 border border-slate-800 p-5 rounded-xl text-center">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">Value-at-Risk (1d 95%)</span>
                  <div className="inline-flex items-center justify-center p-4 border border-slate-800 bg-[#0b0f19] rounded-full w-24 h-24 mb-3">
                    <span className="text-2xl font-black text-slate-100 font-outfit">{currentStock.risk.var1d95}%</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-semibold px-2">
                    Estimate of max potential losses over a 24h holding period at 95% confidence bounds.
                  </p>
                </div>

                {/* CONCENTRATION LIMITS */}
                <div className="bg-[#0f172a]/60 border border-slate-800 p-5 rounded-xl">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-3">Portfolio Concentration Rule</span>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-3">
                    <span className="text-xs text-slate-400 font-semibold">Asset Limit</span>
                    <span className="text-xs font-bold text-slate-200">5.00% Max</span>
                  </div>
                  <div className="flex items-center justify-between border-b border-slate-800/80 pb-2 mb-3">
                    <span className="text-xs text-slate-400 font-semibold">Active Weight</span>
                    <span className="text-xs font-bold text-slate-200">1.20%</span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-semibold leading-relaxed mt-4">
                    <span className="text-emerald-500 font-bold">Status:</span> {currentStock.risk.concentrationCheck}
                  </p>
                </div>

                {/* COMPLIANCE GATEWAY */}
                <div className="bg-[#0f172a]/60 border border-slate-800 p-5 rounded-xl">
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-3">Compliance restricted List</span>
                  <div className="flex flex-col items-center justify-center h-28 border border-dashed border-slate-800 bg-slate-900/30 rounded-lg">
                    {currentStock.risk.restrictedListCheck === "Passed" ? (
                      <>
                        <span className="w-8 h-8 rounded-full bg-emerald-950 flex items-center justify-center text-emerald-400 border border-emerald-800/40 text-sm mb-2 shadow">
                          ✓
                        </span>
                        <span className="text-xs font-black uppercase text-emerald-400 tracking-wider">
                          Restricted List Pass
                        </span>
                        <span className="text-[10px] text-slate-500 mt-0.5">Asset eligible for acquisition</span>
                      </>
                    ) : (
                      <>
                        <span className="w-8 h-8 rounded-full bg-red-950 flex items-center justify-center text-red-400 border border-red-800/40 text-sm mb-2 shadow">
                          🗙
                        </span>
                        <span className="text-xs font-black uppercase text-red-400 tracking-wider">
                          RESTRICTED GATE BLOCKED
                        </span>
                        <span className="text-[10px] text-slate-500 mt-0.5">Trading strictly prohibited</span>
                      </>
                    )}
                  </div>
                </div>

              </div>

              {/* AUTOMATED ALLOCATION BUDGET calculator */}
              <div className="gradient-border-panel p-5">
                <h4 className="text-xs uppercase tracking-wider font-extrabold text-indigo-400 mb-3">
                  Optimal Position Sizing Estimates (FR-069)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-lg flex flex-col justify-between">
                    <div>
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Kelly Criterion (2x Leverage)</span>
                      <p className="text-xs text-slate-400 mt-1 font-semibold leading-relaxed">
                        Sizing optimized to maximize expected log wealth returns.
                      </p>
                    </div>
                    <span className="text-xl font-black text-slate-200 mt-3 block">
                      {currentStock.risk.kellyAllocation}%
                    </span>
                  </div>

                  <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-lg flex flex-col justify-between">
                    <div>
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Volatility Targeting (8% Cap)</span>
                      <p className="text-xs text-slate-400 mt-1 font-semibold leading-relaxed">
                        Adjusts weight dynamically to match target asset volatility.
                      </p>
                    </div>
                    <span className="text-xl font-black text-slate-200 mt-3 block">
                      {currentStock.risk.volAllocation}%
                    </span>
                  </div>

                  <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-lg flex flex-col justify-between">
                    <div>
                      <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider block">Risk Parity Model Sizing</span>
                      <p className="text-xs text-slate-400 mt-1 font-semibold leading-relaxed">
                        Sizing focused on equal risk contribution allocation budgets.
                      </p>
                    </div>
                    <span className="text-xl font-black text-slate-200 mt-3 block">
                      {currentStock.risk.riskParityAllocation}%
                    </span>
                  </div>
                </div>
              </div>

              {/* EXIT STRATEGY CONTROLLER */}
              <div className="bg-[#0f172a]/60 border border-slate-800 p-5 rounded-xl">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-xs uppercase tracking-wider font-extrabold text-slate-300">
                    Exit & Protection Plan (FR-072)
                  </h4>
                  <div className="text-[10px] text-slate-500 font-mono">
                    Entry Price: ${currentStock.price.toFixed(2)}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  
                  {/* STOP LOSS SLIDER */}
                  <div className="bg-slate-900/60 p-4 rounded border border-slate-800/80 flex flex-col gap-2">
                    <div className="flex justify-between text-xs font-semibold text-slate-400">
                      <span>Stop-Loss Floor</span>
                      <span className="text-red-400 font-bold font-mono">${selectedStopLoss.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min={currentStock.price * 0.75}
                      max={currentStock.price * 0.98}
                      step={0.5}
                      value={selectedStopLoss}
                      onChange={(e) => setSelectedStopLoss(parseFloat(e.target.value))}
                      className="w-full accent-red-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-[9px] text-slate-500 font-semibold block text-right">
                      Max loss: {(((currentStock.price - selectedStopLoss) / currentStock.price) * 100).toFixed(1)}% from entry
                    </span>
                  </div>

                  {/* PROFIT TARGET SLIDER */}
                  <div className="bg-slate-900/60 p-4 rounded border border-slate-800/80 flex flex-col gap-2">
                    <div className="flex justify-between text-xs font-semibold text-slate-400">
                      <span>Profit Target Ceiling</span>
                      <span className="text-emerald-400 font-bold font-mono">${selectedProfitTarget.toFixed(2)}</span>
                    </div>
                    <input
                      type="range"
                      min={currentStock.price * 1.02}
                      max={currentStock.price * 1.4}
                      step={0.5}
                      value={selectedProfitTarget}
                      onChange={(e) => setSelectedProfitTarget(parseFloat(e.target.value))}
                      className="w-full accent-emerald-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                    />
                    <span className="text-[9px] text-slate-500 font-semibold block text-right">
                      Upside: {(((selectedProfitTarget - currentStock.price) / currentStock.price) * 100).toFixed(1)}% to target
                    </span>
                  </div>

                  {/* COMPUTED RISK REWARD SUMMARY */}
                  <div className="bg-[#0b0f19] p-4 rounded border border-slate-800/80 flex flex-col justify-between h-20">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Risk-Reward Ratio</span>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xl font-black ${
                        parseFloat(riskRewardRatio) >= 2.5 ? "text-emerald-400" : parseFloat(riskRewardRatio) >= 1.5 ? "text-amber-400" : "text-red-400"
                      }`}>
                        {riskRewardRatio}x
                      </span>
                      <span className="text-[10px] text-slate-500">
                        ({distanceToTarget.toFixed(2)} vs {distanceToStop.toFixed(2)})
                      </span>
                    </div>
                  </div>

                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-semibold text-slate-400">
                  <span>Time-Based Exit Gate: {currentStock.risk.timeHorizonDays} days</span>
                  <span className="text-slate-500">Exceeding this triggers automatic position audit reviews</span>
                </div>
              </div>

            </div>
          )}

          {/* TAB CONTENT: 4. PORTFOLIO MANAGER TERMINAL */}
          {activeTab === "pm" && (
            <div className="gradient-border-panel p-6 flex flex-col gap-6">
              <div className="border-b border-slate-800 pb-3">
                <h3 className="font-bold text-base font-outfit text-slate-100">Portfolio Manager Decision Terminal</h3>
                <p className="text-xs text-slate-400 mt-0.5">Approve, customize, or override recommended multi-agent thesis constructs.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                {/* ACTION SIGNAL TAXONOMY SELECT */}
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                    Action Signal (FR-082)
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {["Strong Buy", "Buy", "Accumulate", "Hold", "Reduce", "Sell", "Strong Sell", "Not Buy", "Not Sell"].map((actionOption) => {
                      const isSelected = selectedAction === actionOption;
                      return (
                        <button
                          key={actionOption}
                          onClick={() => setSelectedAction(actionOption)}
                          className={`px-2 py-2 rounded text-[11px] font-extrabold uppercase tracking-wide border transition-all ${
                            isSelected
                              ? actionOption.includes("Buy")
                                ? "bg-emerald-950/40 text-emerald-400 border-emerald-500"
                                : actionOption.includes("Sell") || actionOption.includes("Reduce")
                                ? "bg-red-950/40 text-red-400 border-red-500"
                                : "bg-slate-800 text-slate-200 border-slate-700"
                              : "bg-slate-900 border-slate-800/80 hover:border-slate-800 text-slate-400"
                          }`}
                        >
                          {actionOption}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* SIZING & CONVICTION METERS */}
                <div className="flex flex-col gap-5">
                  
                  {/* CONVICTION SCORE RANGE */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between text-xs font-bold text-slate-400">
                      <span className="uppercase tracking-wide">Signal Conviction Score (FR-061)</span>
                      <span className="text-blue-400 font-mono font-black">{selectedConviction}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={100}
                      value={selectedConviction}
                      onChange={(e) => setSelectedConviction(parseInt(e.target.value))}
                      className="w-full accent-blue-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-[9px] text-slate-500 font-bold uppercase">
                      <span>Low Consensus (&lt;50)</span>
                      <span>Target Trigger (75+)</span>
                      <span>High Conviction (90+)</span>
                    </div>
                  </div>

                  {/* OVERRIDE POSITION SIZING */}
                  <div className="flex flex-col gap-1.5">
                    <div className="flex justify-between text-xs font-bold text-slate-400">
                      <span className="uppercase tracking-wide">Capital Allocation size</span>
                      <span className="text-indigo-400 font-mono font-black">{selectedSizing}%</span>
                    </div>
                    <input
                      type="range"
                      min={0}
                      max={10}
                      step={0.1}
                      value={selectedSizing}
                      onChange={(e) => setSelectedSizing(parseFloat(e.target.value))}
                      className="w-full accent-indigo-500 h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="px-2.5 py-1.5 rounded text-[10px] font-semibold flex items-center justify-between transition-colors duration-300 gap-3 mt-1 bg-slate-900/60 border border-slate-800/80">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${selectedSizing > 5.0 ? "bg-red-500 animate-ping" : "bg-indigo-400"}`} />
                        <span className="text-slate-400">Incremental VaR Impact:</span>
                        <span className="text-slate-200 font-bold">{computedRiskContribution}%</span>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded ${currentRiskStatus.color}`}>
                        {currentRiskStatus.label}
                      </span>
                    </div>
                  </div>

                </div>

              </div>

              {/* HORIZON SELECTOR */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-end">
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                    Primary Time Horizon (FR-065)
                  </label>
                  <div className="flex gap-2">
                    {["Tactical", "Medium-term", "Strategic"].map((hOption) => (
                      <button
                        key={hOption}
                        onClick={() => setSelectedHorizon(hOption)}
                        className={`flex-1 py-2 rounded text-xs font-bold border transition-all ${
                          selectedHorizon === hOption
                            ? "bg-indigo-950/40 text-indigo-400 border-indigo-500"
                            : "bg-slate-950 border-slate-800 text-slate-400"
                        }`}
                      >
                        {hOption}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 font-semibold leading-relaxed bg-[#0b0f19] p-3 rounded border border-slate-800">
                  <span className="text-indigo-400 font-bold block mb-0.5">Horizon Rule Mapping:</span>
                  Tactical focus: technical momentum. Medium-term focus: catalyst timeline. Strategic focus: core fundamental DCF valuation profiles.
                </div>
              </div>

              {/* HUMAN AUDIT NOTES */}
              <div className="flex flex-col gap-2">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                  Reviewer Override Comments & Audit Trail Logs
                </label>
                <textarea
                  value={auditComment}
                  onChange={(e) => setAuditComment(e.target.value)}
                  placeholder="Record justification details for overrides, custom stop adjustments, or escalation events..."
                  className="w-full h-20 bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-slate-700 font-medium"
                />
              </div>

              {/* ACTION EXECUTION BUTTONS */}
              <div className="flex flex-wrap gap-4 border-t border-slate-800/60 pt-4">
                <button
                  onClick={() => alert(`Idea approved in audit logs:\nSymbol: ${selectedSymbol}\nAction: ${selectedAction}\nConviction: ${selectedConviction}%\nWeight: ${selectedSizing}%`)}
                  className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition-all active:scale-95 shadow shadow-emerald-500/10"
                >
                  Commit Strategy To Portfolio
                </button>
                <button
                  onClick={() => alert("Idea flagged. Requesting secondary risk committee audit...")}
                  className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 rounded-lg text-xs font-bold uppercase tracking-wider transition-all active:scale-95"
                >
                  Request Risk Review
                </button>
              </div>

            </div>
          )}

        </div>

        {/* ==========================================
            RIGHT COLUMN: CONSOLE & DATA PROVENANCE
            ========================================== */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          
          {/* ORCHESTRATION CONSOLE LOG FEED */}
          <div className="gradient-border-panel p-5 flex flex-col h-[350px]">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-3">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-pulse-glow" />
                <h3 className="font-bold text-xs uppercase tracking-wider text-slate-100">Orchestrator log Console</h3>
              </div>
              <span className="text-[10px] text-slate-500 font-mono">LIVE FEED</span>
            </div>

            <div className="flex-1 bg-slate-950 border border-slate-900 rounded-lg p-3 overflow-y-auto font-mono text-[10px] leading-relaxed flex flex-col gap-2 shadow-inner">
              {consoleLogs.map((log, idx) => {
                const badgeColor = 
                  log.type === "success" ? "text-emerald-400 bg-emerald-950/40" :
                  log.type === "warning" ? "text-amber-400 bg-amber-950/40" :
                  log.type === "error" ? "text-red-400 bg-red-950/40" :
                  "text-blue-400 bg-blue-950/40";
                return (
                  <div key={idx} className="border-b border-slate-900/40 pb-1.5 last:border-0">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="text-slate-600 font-bold">[{log.timestamp}]</span>
                      <span className={`px-1.5 py-0.5 rounded font-black text-[8px] uppercase tracking-wide ${badgeColor}`}>
                        {log.source}
                      </span>
                    </div>
                    <span className="text-slate-300 font-medium">{log.message}</span>
                  </div>
                );
              })}
              {isSimulating && (
                <div className="flex items-center gap-1 text-blue-500 animate-pulse font-bold mt-1">
                  <span>&gt; Ingesting execution thread state...</span>
                  <span className="w-1.5 h-3 bg-blue-500 inline-block animate-pulse" />
                </div>
              )}
              {consoleLogs.length === 0 && !isSimulating && (
                <div className="text-slate-600 italic text-center py-12">
                  System logs empty. Run orchestration to view execution streams.
                </div>
              )}
              <div ref={consoleEndRef} />
            </div>
          </div>

          {/* AUDIT PATHS & LINEAGE METADATA */}
          <div className="gradient-border-panel p-5 flex flex-col justify-between min-h-[350px]">
            <div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-4">
                <h3 className="font-bold text-xs uppercase tracking-wider text-slate-100">Audit lineage Explorer</h3>
                <span className="text-[10px] text-slate-500 font-mono">NFR-011 - 014</span>
              </div>

              <div className="flex flex-col gap-4">
                {/* PROVENANCE */}
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1.5">
                    Data Source Provenance
                  </span>
                  <div className="flex flex-col gap-1.5">
                    {currentStock.lineage.dataSources.map((src, idx) => (
                      <div key={idx} className="flex gap-2 items-start bg-slate-900 border border-slate-800/40 p-2 rounded">
                        <span className="text-[9px] text-slate-400 font-extrabold font-mono pt-0.5">SRC0{idx+1}</span>
                        <p className="text-[10px] text-slate-300 leading-normal font-semibold">{src}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* MODELS USED */}
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1.5">
                    Model Engines Utilized
                  </span>
                  <div className="flex flex-col gap-1.5">
                    {currentStock.lineage.modelsUsed.map((model, idx) => (
                      <div key={idx} className="bg-slate-900 border border-slate-800/40 p-2 rounded text-[10px] text-slate-300 font-bold leading-normal">
                        {model}
                      </div>
                    ))}
                  </div>
                </div>

                {/* PROMPTS SNAPSHOTS */}
                <div>
                  <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-1.5">
                    Prompt Config Trace Snapshot
                  </span>
                  <div className="flex flex-col gap-1.5">
                    {currentStock.lineage.promptVersions.map((prompt, idx) => (
                      <div key={idx} className="flex items-center justify-between bg-slate-900 border border-slate-800/40 p-2 rounded text-[10px]">
                        <span className="text-slate-300 font-bold">{prompt.agent}</span>
                        <span className="text-blue-400 font-mono font-semibold">{prompt.version}</span>
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            </div>

            <div className="mt-6 pt-3 border-t border-slate-800/60 text-[10px] text-slate-500 font-semibold leading-relaxed">
              <span className="text-indigo-400 font-bold block mb-0.5">Governance Trace Guarantee:</span>
              Snapshots of input vectors, models, and prompts are retained to ensure compliance audit reproducibility checks can execute at any future date.
            </div>
          </div>

        </div>

      </main>
      
      {/* FOOTER */}
      <footer className="border-t border-slate-900 bg-[#070a12] px-6 py-4 flex items-center justify-between text-[11px] text-slate-500 font-semibold">
        <span>© 2026 Antigravity Multi-Agent Research Platforms. All rights reserved.</span>
        <span>Version 1.0.0 &bull; Build stable</span>
      </footer>

    </div>
  );
}
