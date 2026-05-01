import { useCallback, useMemo, useState } from "react";
import { Menu } from "lucide-react";
import Sidebar from "./components/Sidebar";
import ChatArea from "./components/ChatArea";
import { DEFAULT_SYSTEM_NOTE, MOCK_RESPONSES, PERSONAS } from "@/mocks/chatResponses";
import type { PersonaId } from "@/mocks/chatResponses";
import type { Message } from "./components/ChatArea";

let messageCounter = 0;

function generateId(): string {
  messageCounter += 1;
  return `msg_${messageCounter}_${Date.now()}`;
}

function getMockResponse(personaId: PersonaId | null): string {
  const responses = personaId ? MOCK_RESPONSES[personaId] : null;
  if (responses && responses.length > 0) {
    const idx = Math.floor(Math.random() * responses.length);
    return responses[idx];
  }
  const defaults = MOCK_RESPONSES.default;
  const idx = Math.floor(Math.random() * defaults.length);
  return defaults[idx];
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

  const handleSendMessage = useCallback(
    (text: string) => {
      const userMessage: Message = {
        id: generateId(),
        role: 'user',
        content: text,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsTyping(true);

      const delay = 650 + Math.random() * 650;

      setTimeout(() => {
        const systemContext = persona?.systemPrompt ?? DEFAULT_SYSTEM_NOTE;
        const response = `${getMockResponse(currentPersona)}\n\n**Active system context**\n${systemContext}`;
        const assistantMessage: Message = {
          id: generateId(),
          role: 'assistant',
          content: response,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setIsTyping(false);
      }, delay);
    },
    [currentPersona, persona]
  );

  const handleSelectPersona = useCallback(
    (personaId: PersonaId) => {
      setCurrentPersona(personaId);
      const selectedPersona = PERSONAS.find((p) => p.id === personaId);
      if (!selectedPersona) return;

      const greeting = `**${selectedPersona.label} mode is active.**\n\n${selectedPersona.description}\n\nSystem prompt applied:\n${selectedPersona.systemPrompt}`;

      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: greeting,
        timestamp: new Date(),
      };

      setMessages([assistantMessage]);
    },
    []
  );

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
