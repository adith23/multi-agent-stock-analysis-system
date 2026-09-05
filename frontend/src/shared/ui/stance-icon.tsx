import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { AgentStance } from "@/entities/agent/types";
import { cn } from "@/shared/lib/cn";

export interface StanceIconProps {
  stance: AgentStance;
  className?: string;
}

const STANCE_CONFIG = {
  [AgentStance.BULLISH]: {
    Icon: ArrowUpRight,
    className: "text-green",
    label: "Bullish",
  },
  [AgentStance.BEARISH]: {
    Icon: ArrowDownRight,
    className: "text-red",
    label: "Bearish",
  },
  [AgentStance.NEUTRAL]: {
    Icon: Minus,
    className: "text-text-faint",
    label: "Neutral",
  },
} as const;

export function StanceIcon({ stance, className }: StanceIconProps) {
  const { Icon, label, className: stanceClassName } = STANCE_CONFIG[stance];
  return (
    <Icon
      aria-label={label}
      className={cn("size-4", stanceClassName, className)}
      role="img"
      strokeWidth={2}
    />
  );
}
