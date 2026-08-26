export const DESIGN_TOKENS = {
  colors: {
    void: "#0a0b0d",
    panel: "#111318",
    panelRaised: "#181b21",
    inset: "#0c0e12",
    hairline: "#242830",
    hairlineBright: "#3a3f4a",
    textPrimary: "#e7e3d9",
    textDim: "#9ba0aa",
    textFaint: "#5c616b",
    amber: "#e0a730",
    amberDim: "#7a5e22",
    green: "#3fb968",
    greenDim: "#1b4a2c",
    red: "#f0554a",
    redDim: "#5a2420",
    blue: "#6fa8dc",
    parchment: "#c9a66b",
  },
  fonts: {
    serif: '"Source Serif 4 Variable", Georgia, serif',
    mono: '"IBM Plex Mono", "SFMono-Regular", Consolas, monospace',
    sans: '"Inter Variable", Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  layout: {
    headerHeight: 52,
    footerHeight: 26,
    leftSidebarWidth: 226,
    rightSidebarWidth: 250,
    minimumViewportWidth: 1080,
  },
} as const;

export const APP_NAME = "Conclave Terminal";
export const DEFAULT_API_BASE_URL = "http://localhost:8000/api/v1";
export const DEFAULT_WS_URL = "ws://localhost:8000/ws";
