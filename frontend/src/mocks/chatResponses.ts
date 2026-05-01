import { Building2, ChartNoAxesCombined, Microscope } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type PersonaId = "researcher" | "investor" | "business";

export interface Persona {
  id: PersonaId;
  label: string;
  shortLabel: string;
  description: string;
  icon: LucideIcon;
  accent: string;
  systemPrompt: string;
  suggestions: string[];
}

export const PERSONAS: Persona[] = [
  {
    id: "researcher",
    label: "Researcher",
    shortLabel: "Research",
    description:
      "Find commercial paths for research, map industry partners, and turn technical capability into market-ready opportunities.",
    icon: Microscope,
    accent: "#0f766e",
    systemPrompt:
      "You are a research commercialization analyst. Help identify industry use cases, business buyers, grant programs, pilot partners, and go-to-market hypotheses. Be specific, evidence-oriented, and ask for missing technical constraints when needed.",
    suggestions: [
      "Find business use cases for our lab's sensor technology",
      "Map companies that could pilot a medical imaging algorithm",
      "Suggest EU grant paths for an applied AI research project",
    ],
  },
  {
    id: "investor",
    label: "Investor",
    shortLabel: "Invest",
    description:
      "Evaluate startup ideas, surface grant and funding angles, and build a sharper view of markets, risks, and investability.",
    icon: ChartNoAxesCombined,
    accent: "#b45309",
    systemPrompt:
      "You are an investor analyst. Assess market size, competition, defensibility, traction signals, funding fit, risk, grant leverage, and next diligence questions. Prefer structured recommendations and clear assumptions.",
    suggestions: [
      "Evaluate whether this AI logistics idea is venture-backable",
      "List diligence questions for a climate hardware startup",
      "Find grant and co-investment angles for a deep-tech company",
    ],
  },
  {
    id: "business",
    label: "Business",
    shortLabel: "Business",
    description:
      "Discover technologies worth buying or partnering on, identify vendors, and translate operational pain points into solution searches.",
    icon: Building2,
    accent: "#be123c",
    systemPrompt:
      "You are a business development strategist. Help companies find technologies, startups, researchers, vendors, grants, and partnerships that solve operational or growth problems. Focus on practical adoption paths and buyer language.",
    suggestions: [
      "Find startups that can reduce energy costs in manufacturing",
      "Turn this operational problem into a technology search brief",
      "Identify research teams that could build a custom computer vision solution",
    ],
  },
];

export const DEFAULT_SYSTEM_NOTE =
  "No specialist system prompt is active. The assistant should behave as a general opportunity discovery chat.";

export const MOCK_RESPONSES: Record<PersonaId | "default", string[]> = {
  researcher: [
    "**Research commercialization path**\n\nStart by describing the technology in plain business language: what it measures, predicts, automates, or reduces. Then I would map 3 buyer groups: companies with a costly workflow, regulated organizations that need better evidence, and integrators that can bundle your method into an existing product.\n\nUseful next step: share the field, maturity level, and any validation data.",
    "**Partner search approach**\n\nI would build a shortlist across four buckets: strategic corporates, applied R&D centers, pilot-friendly SMEs, and grant consortium partners. For each candidate, score pain intensity, technical fit, sales cycle, and access to data or test environments.",
  ],
  investor: [
    "**Investment screen**\n\nI would evaluate this through five lenses: urgent buyer pain, market timing, defensibility, route to distribution, and non-dilutive funding leverage. A strong next output would be a diligence memo with key assumptions, risks, and proof points needed before a first check.",
    "**Funding angle**\n\nFor deep-tech and applied AI ideas, combine private capital with grants or procurement pilots. The strongest stories usually show a near-term paid pilot, a credible technical moat, and a grant pathway that reduces early capital intensity.",
  ],
  business: [
    "**Solution discovery plan**\n\nTranslate the business problem into a search brief: current workflow, cost of the problem, constraints, buying criteria, and target implementation window. Then compare startups, research labs, vendors, and grant-backed pilot options side by side.",
    "**Buyer-ready framing**\n\nA useful search starts with the business metric: revenue gained, time saved, risk reduced, or cost removed. From there, I can help identify solution categories, likely vendors, research partners, and a pilot design.",
  ],
  default: [
    "**Opportunity discovery**\n\nTell me what you have or what you need: a technology, a business problem, a startup idea, a target sector, or an investor profile. I can help map use cases, buyers, partners, grants, and next validation steps.",
    "**Good starting point**\n\nShare one paragraph about the idea or problem, plus geography, sector, and maturity stage. I will turn it into a structured opportunity map with recommended targets and follow-up questions.",
  ],
};
