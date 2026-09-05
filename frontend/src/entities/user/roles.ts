import { UserRole } from "./types";

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.PORTFOLIO_MANAGER]: "Portfolio Manager",
  [UserRole.INVESTMENT_ANALYST]: "Investment Analyst",
  [UserRole.RESEARCH_ANALYST]: "Research Analyst",
  [UserRole.RISK_OFFICER]: "Risk Officer",
  [UserRole.COMPLIANCE_REVIEWER]: "Compliance Reviewer",
  [UserRole.SYSTEM_ADMINISTRATOR]: "System Administrator",
};

const SENSITIVE_DATA_ROLES = new Set<UserRole>([
  UserRole.PORTFOLIO_MANAGER,
  UserRole.RISK_OFFICER,
  UserRole.COMPLIANCE_REVIEWER,
  UserRole.SYSTEM_ADMINISTRATOR,
]);

export function canAccessSensitiveData(role: UserRole): boolean {
  return SENSITIVE_DATA_ROLES.has(role);
}
