import { useCallback, useMemo, useState } from "react";
import { Menu } from "lucide-react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import type { PersonaId } from "@/mocks/chatResponses";
import { PERSONAS } from "@/mocks/chatResponses";
import type { Message } from "./components/ChatArea";

let messageCounter = 0;

function generateId(): string {
  messageCounter += 1;
  return `msg_${messageCounter}_${Date.now()}`;
}

async function getResponse(message: string, persona: string = "general") {
  const res = await fetch(
    "http://localhost:8000/search?q=" +
      encodeURIComponent(message) +
      `&persona=${encodeURIComponent(persona)}`
  );

  if (!res.ok) {
    throw new Error("Backend request failed");
  }

  return res.json();
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [currentPersona, setCurrentPersona] = useState<PersonaId | null>(null);

  const persona = useMemo(
    () => PERSONAS.find((item) => item.id === currentPersona) ?? null,
    [currentPersona]
  );

  const handleNewChat = useCallback(() => {
    setMessages([]);
    setIsTyping(false);
    setInputValue("");
    setCurrentPersona(null);
  }, []);

  const handleSendMessage = useCallback(async (text: string) => {
    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsTyping(true);

    try {
      const data = await getResponse(text, currentPersona ?? "general");

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: data.result?.answer ?? "No response",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: "Backend error (RAG failed).",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  }, []);

  const handleSelectPersona = useCallback((personaId: PersonaId) => {
    setCurrentPersona(personaId);
    const selectedPersona = PERSONAS.find((p) => p.id === personaId);
    if (!selectedPersona) return;

    const greeting = `**${selectedPersona.label} mode is active.**\n\n${selectedPersona.description}\n\nSystem prompt applied:\n${selectedPersona.systemPrompt}`;

    const assistantMessage: Message = {
      id: generateId(),
      role: "assistant",
      content: greeting,
      timestamp: new Date(),
    };

    setMessages([assistantMessage]);
  }, []);

  return (
    <div className="app-shell">
      <Sidebar
        onNewChat={handleNewChat}
        onSelectPersona={handleSelectPersona}
        currentPersona={currentPersona}
        isMobileOpen={mobileSidebarOpen}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <div className="main">
        <div className="mobile-header">
          <button
            type="button"
            onClick={() => setMobileSidebarOpen(true)}
            className="icon-button"
            aria-label="Open navigation"
          >
            <Menu size={20} />
          </button>
          <img className="brand-logo" src="/logo.png" alt="NexusBridge" />
          <strong>NexusBridge</strong>
        </div>

        <ChatArea
          messages={messages}
          isTyping={isTyping}
          onSendMessage={handleSendMessage}
          onSelectPersona={handleSelectPersona}
          inputValue={inputValue}
          setInputValue={setInputValue}
          persona={persona}
        />
      </div>
    </div>
  );
}
