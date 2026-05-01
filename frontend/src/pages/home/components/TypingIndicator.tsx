export default function TypingIndicator() {
  return (
    <div className="message-row">
      <img className="avatar avatar-logo" src="/logo.png" alt="NexusBridge assistant" />
      <div className="message">
        <div className="typing" aria-label="Assistant is typing">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}
