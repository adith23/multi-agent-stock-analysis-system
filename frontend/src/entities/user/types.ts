export enum UserRole {
  PORTFOLIO_MANAGER = "portfolio_manager",
  INVESTMENT_ANALYST = "investment_analyst",
  RESEARCH_ANALYST = "research_analyst",
  RISK_OFFICER = "risk_officer",
  COMPLIANCE_REVIEWER = "compliance_reviewer",
  SYSTEM_ADMINISTRATOR = "system_administrator",
}

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  job_title: string;
  role: UserRole;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LogoutRequest {
  refresh: string;
}
