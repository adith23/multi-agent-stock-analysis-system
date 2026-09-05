export interface ExposureMetricView { label: string; value: number; limit: number; }
export interface StressScenarioView { scenario: string; impact: string; }
export interface ComplianceCheckView { label: string; pass: boolean; }
export interface RiskComplianceView { status: string; exposures: readonly ExposureMetricView[]; stressTests: readonly StressScenarioView[]; note: string; restrictedListStatus: string; checks: readonly ComplianceCheckView[]; escalation: string; }
