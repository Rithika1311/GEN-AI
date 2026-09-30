import React from "react";
import SourceChip from "./SourceChip";

export default function MessageBubble({ message }) {
  const isUser = message.role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className="message-avatar">
        {isUser ? "👤" : "🤖"}
      </div>
      <div className="message-content-wrapper">
        <div className="message-bubble">
          <div className="message-text">
            {message.content}
            {message.isStreaming && <span className="typing-cursor">▋</span>}
          </div>
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="sources-section">
            <span className="sources-label">Sources ({message.sources.length}):</span>
            <div className="sources-chips-grid">
              {message.sources.map((src, idx) => (
                <SourceChip key={`${src.document_id}-${src.chunk_index}-${idx}`} source={src} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
