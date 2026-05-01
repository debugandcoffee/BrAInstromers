import { ArrowRight } from "lucide-react";
import { PERSONAS } from "@/mocks/chatResponses";
import type { PersonaId } from "@/mocks/chatResponses";

export interface EmptyStateProps {
  onSelectPersona: (personaId: PersonaId) => void;
}

export default function EmptyState({ onSelectPersona }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-heading">
        <h1>Find the next business opportunity.</h1>
        <p>
          Use the chat to discover commercial use cases, companies that could buy a solution,
          investors who may fund it, grant paths, startup targets, and research partners.
        </p>
      </div>

      <div className="persona-grid">
        {PERSONAS.map((p) => {
          const PersonaIcon = p.icon;

          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectPersona(p.id)}
              className="persona-card"
            >
              <PersonaIcon size={28} color={p.accent} />
              <h2>{p.label}</h2>
              <p>{p.description}</p>

              <div className="suggestions">
                {p.suggestions.slice(0, 2).map((suggestion) => (
                  <span key={suggestion} className="suggestion-button">
                    <ArrowRight size={14} />
                    {suggestion}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
