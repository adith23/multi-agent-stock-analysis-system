import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Conclave Decision Terminal",
    short_name: "Conclave",
    description: "Governed multi-agent stock analysis and decision support.",
    start_url: "/",
    display: "standalone",
    background_color: "#0a0b0d",
    theme_color: "#0a0b0d",
  };
}
