import React, { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";

export default function ChatWindow({
  messages,
  onSendMessage,
  onStopGeneration,
  onClearChat,
  isStreaming,
  selectedDocCount,
  totalDocCount,
}) {
  const [inputText, setInputText] = useState("");
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputText.trim() || isStreaming) return;
    onSendMessage(inputText.trim());
    setInputText("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const starterPrompts = [
    "What are the main findings in the document?",
    "Summarize the key methodologies mentioned.",
    "What are the limitations or trade-offs discussed?",
  ];

  const getScopeBadge = () => {
    if (totalDocCount === 0) {
      return "No documents indexed";
    }
    if (selectedDocCount === 0 || selectedDocCount === totalDocCount) {
      return `Searching across all ${totalDocCount} documents`;
    }
    return `Searching across ${selectedDocCount} of ${totalDocCount} documents`;
  };

  return (
    <div className="chat-window">
      <div className="chat-header">
        <div className="chat-header-info">
          <h2>DocuMind Chat</h2>
          <span className="search-scope-badge">{getScopeBadge()}</span>
        </div>
        {messages.length > 0 && (
          <button
            type="button"
            className="clear-chat-btn"
            onClick={onClearChat}
            disabled={isStreaming}
          >
            Clear Conversation
          </button>
        )}
      </div>

      <div className="chat-messages-container">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            <div className="empty-icon">💬</div>
            <h3>Ask questions grounded in your PDFs</h3>
            <p>
              DocuMind verifies every answer using retrieved passages and cites the exact file and page number.
            </p>
            {totalDocCount > 0 && (
              <div className="starter-prompts">
                <span className="starter-label">Try asking:</span>
                <div className="starter-list">
                  {starterPrompts.map((prompt, idx) => (
                    <button
                      key={idx}
                      className="starter-btn"
                      onClick={() => onSendMessage(prompt)}
                      disabled={isStreaming}
                    >
                      "{prompt}"
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((msg, index) => (
              <MessageBubble key={index} message={msg} />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <textarea
            ref={inputRef}
            className="chat-textarea"
            placeholder={
              totalDocCount === 0
                ? "Upload a PDF first to begin asking questions..."
                : "Ask a question about your documents... (Shift+Enter for new line)"
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={1}
            disabled={isStreaming || totalDocCount === 0}
          />

          {isStreaming ? (
            <button
              type="button"
              className="stop-btn"
              onClick={onStopGeneration}
              title="Stop streaming response"
            >
              ⏹ Stop
            </button>
          ) : (
            <button
              type="submit"
              className="send-btn"
              disabled={!inputText.trim() || totalDocCount === 0}
              title="Send question"
            >
              ➤
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
