import { Plus } from "lucide-react";
import { PERSONAS } from "@/mocks/chatResponses";
import type { PersonaId } from "@/mocks/chatResponses";

export interface SidebarProps {
  onNewChat: () => void;
  onSelectPersona: (personaId: PersonaId) => void;
  currentPersona: PersonaId | null;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
}

export default function Sidebar({
  onNewChat,
  onSelectPersona,
  currentPersona,
  isMobileOpen,
  onCloseMobile,
}: SidebarProps) {
  return (
    <>
      {isMobileOpen && <div className="overlay" onClick={onCloseMobile} aria-hidden="true" />}

      <aside className={`sidebar ${isMobileOpen ? "open" : ""}`}>
        <div className="brand">
          <img className="brand-logo" src="/logo.png" alt="NexusBridge" />
          <div>
            NexusBridge
            <span className="brand-subtitle">Opportunity discovery</span>
          </div>
        </div>

        <div className="sidebar-section">
          <button
            type="button"
            onClick={onNewChat}
            className="button primary-button"
          >
            <Plus size={17} />
            New chat
          </button>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">Specialist mode</p>
          {PERSONAS.map((p) => {
            const PersonaIcon = p.icon;

            return (
              <button
                key={p.id}
                type="button"
                onClick={() => {
                  onSelectPersona(p.id);
                  onCloseMobile();
                }}
                className={`persona-button ${currentPersona === p.id ? "active" : ""}`}
              >
                <PersonaIcon size={18} color={currentPersona === p.id ? "#0f766e" : p.accent} />
                {p.label}
              </button>
            );
          })}
        </div>

        <div className="sidebar-card">
          <strong>What it does</strong>
          <p>
            Search for business applications, potential buyers, investors, grants,
            research partners, and startup opportunities from one chat flow.
          </p>
        </div>
      </aside>
    </>
  );
}
