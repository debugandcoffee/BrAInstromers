import { FormEvent, KeyboardEvent, useEffect, useRef } from "react";
import { Send, UserRound } from "lucide-react";
import TypingIndicator from "./TypingIndicator";
import EmptyState from "./EmptyState";
import type { Persona, PersonaId } from "@/mocks/chatResponses";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface ChatAreaProps {
  messages: Message[];
  isTyping: boolean;
  onSendMessage: (text: string) => void;
  onSelectPersona: (personaId: PersonaId) => void;
  inputValue: string;
  setInputValue: (v: string) => void;
  persona: Persona | null;
}

export default function ChatArea({
  messages,
  isTyping,
  onSendMessage,
  onSelectPersona,
  inputValue,
  setInputValue,
  persona,
}: ChatAreaProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(
        inputRef.current.scrollHeight,
        160
      )}px`;
    }
  }, [inputValue]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed || isTyping) return;
    onSendMessage(trimmed);
    setInputValue("");
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as unknown as FormEvent);
    }
  };

  const renderContent = (text: string) => {
    return text.split("\n\n").map((paragraph, index) => {
      const parts = paragraph.split(/(\*\*.*?\*\*)/g).map((part, partIndex) => {
        if (part.startsWith("**") && part.endsWith("**")) {
          return <strong key={partIndex}>{part.slice(2, -2)}</strong>;
        }
        return <span key={partIndex}>{part}</span>;
      });

      return <p key={index}>{parts}</p>;
    });
  };

  const ActivePersonaIcon = persona?.icon;

  return (
    <div className="chat">
      <div ref={scrollRef} className="messages">
        {messages.length === 0 ? (
          <EmptyState onSelectPersona={onSelectPersona} />
        ) : (
          <div className="messages-inner">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.role}`}>
                {msg.role === "assistant" ? (
                  <img
                    className="avatar avatar-logo"
                    src="/logo.png"
                    alt="NexusBridge assistant"
                  />
                ) : (
                  <div
                    className="avatar"
                    aria-hidden="true"
                    style={{ background: "#111827" }}
                  >
                    <UserRound size={18} />
                  </div>
                )}

                <div className={`message ${msg.role}`}>
                  {renderContent(msg.content)}
                </div>
              </div>
            ))}

            {isTyping && <TypingIndicator />}
          </div>
        )}
      </div>

      <div className="composer-wrap">
        <form onSubmit={handleSubmit} className="composer">
          <div className="mode-line">
            <span className="mode-pill">
              {ActivePersonaIcon ? <ActivePersonaIcon size={15} /> : "No"}{" "}
              {persona?.label ?? "specialist mode"}
            </span>
            <span>
              {persona
                ? "Specialist system prompt is active."
                : "No specialist system prompt is active."}
            </span>
          </div>
          <div className="input-shell">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about business use cases, buyers, investors, grants, or partnerships..."
              rows={1}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isTyping}
              className="send-button"
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          </div>
          <p
            style={{
              margin: "8px 0 0",
              textAlign: "center",
              color: "#667085",
              fontSize: 11,
            }}
          >
            AI can make mistakes. Verify important information independently.
          </p>
        </form>
      </div>
    </div>
  );
}
