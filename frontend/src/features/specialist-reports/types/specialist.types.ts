export interface EvidenceItem { source: string; sourceType: string; timestamp: string; confidence: "High" | "Med" | "Low"; }
export interface MacroReportView { regime: string; summary: string; points: readonly string[]; evidence: readonly EvidenceItem[]; }
export interface FundamentalReportView { thesis: string; grade: string; bullDrivers: readonly string[]; bearDrivers: readonly string[]; fairValue: { low: number; mid: number; high: number }; evidence: readonly EvidenceItem[]; }
export interface TechnicalReportView { trend: { short: string; medium: string; long: string }; momentum: number; levels: { support: number; resistance: number }; flags: readonly string[]; evidence: readonly EvidenceItem[]; }
export interface SentimentReportView { score: number; direction: string; attention: string; tags: readonly string[]; evidence: readonly EvidenceItem[]; }
export interface SpecialistReportViews { macro: MacroReportView; fundamental: FundamentalReportView; technical: TechnicalReportView; sentiment: SentimentReportView; }
