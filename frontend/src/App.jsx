import React, { useState, useEffect, useRef } from "react";
import UploadPanel from "./components/UploadPanel";
import DocumentList from "./components/DocumentList";
import ChatWindow from "./components/ChatWindow";
import { fetchDocuments, uploadFiles, deleteDocument, streamChat } from "./api";

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [appError, setAppError] = useState("");

  const abortControllerRef = useRef(null);

  const loadDocuments = async () => {
    setIsLoadingDocs(true);
    setAppError("");
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
      // Auto-select newly loaded documents
      setSelectedDocIds(docs.map((d) => d.id));
    } catch (err) {
      setAppError(err.message || "Failed to load documents.");
    } finally {
      setIsLoadingDocs(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleUploadSuccess = async (files) => {
    const uploadedDocs = await uploadFiles(files);
    // Reload full list to ensure fresh state and chunk counts
    const refreshed = await fetchDocuments();
    setDocuments(refreshed);
    // Add new docs to selection
    setSelectedDocIds((prev) => [
      ...new Set([...prev, ...uploadedDocs.map((d) => d.id)]),
    ]);
  };

  const handleDeleteDocument = async (id, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"? All associated vectors will be removed.`)) {
      return;
    }
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
      setSelectedDocIds((prev) => prev.filter((docId) => docId !== id));
    } catch (err) {
      alert(err.message || "Failed to delete document.");
    }
  };

  const handleToggleSelectDoc = (id) => {
    setSelectedDocIds((prev) =>
      prev.includes(id) ? prev.filter((docId) => docId !== id) : [...prev, id]
    );
  };

  const handleSelectAllDocs = (select) => {
    if (select) {
      setSelectedDocIds(documents.map((d) => d.id));
    } else {
      setSelectedDocIds([]);
    }
  };

  const handleSendMessage = async (question) => {
    if (isStreaming) return;

    // Build chat history from prior completed messages
    const historyPayload = messages
      .filter((m) => !m.isStreaming && m.content)
      .map((m) => ({ role: m.role, content: m.content }));

    const userMessage = { role: "user", content: question };
    const assistantPlaceholder = {
      role: "assistant",
      content: "",
      sources: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setIsStreaming(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Filter by selected document IDs if not all are selected
    const filterIds =
      selectedDocIds.length > 0 && selectedDocIds.length < documents.length
        ? selectedDocIds
        : null;

    await streamChat({
      question,
      document_ids: filterIds,
      history: historyPayload,
      signal: controller.signal,
      onToken: (token) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
            updated[lastIndex] = {
              ...updated[lastIndex],
              content: updated[lastIndex].content + token,
            };
          }
          return updated;
        });
      },
      onSources: (sources) => {
        setMessages((prev) => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
            updated[lastIndex] = {
              ...updated[lastIndex],
              sources: sources || [],
            };
          }
          return updated;
        });
      },
      onDone: () => {
        setIsStreaming(false);
        abortControllerRef.current = null;
        setMessages((prev) => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
            updated[lastIndex] = {
              ...updated[lastIndex],
              isStreaming: false,
            };
          }
          return updated;
        });
      },
      onError: (err) => {
        setIsStreaming(false);
        abortControllerRef.current = null;
        setMessages((prev) => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;
          if (lastIndex >= 0 && updated[lastIndex].role === "assistant") {
            updated[lastIndex] = {
              ...updated[lastIndex],
              content:
                updated[lastIndex].content ||
                `Error: ${err.message || "Failed to generate answer. Check backend connection."}`,
              isStreaming: false,
            };
          }
          return updated;
        });
      },
    });
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleClearChat = () => {
    if (isStreaming) return;
    setMessages([]);
  };

  return (
    <div className="app-layout">
      {/* Sidebar: Document Ingestion and Management */}
      <aside className="app-sidebar">
        <div className="app-brand">
          <div className="brand-logo">📚</div>
          <div className="brand-text">
            <h1>DocuMind</h1>
            <p>Verifiable RAG Assistant</p>
          </div>
        </div>

        {appError && (
          <div className="app-global-error">
            <span>{appError}</span>
            <button onClick={loadDocuments}>Retry</button>
          </div>
        )}

        <UploadPanel onUploadSuccess={handleUploadSuccess} />

        <DocumentList
          documents={documents}
          selectedDocIds={selectedDocIds}
          onToggleSelect={handleToggleSelectDoc}
          onSelectAll={handleSelectAllDocs}
          onDeleteDocument={handleDeleteDocument}
          isLoading={isLoadingDocs}
        />
      </aside>

      {/* Main Panel: Interactive Grounded Chat */}
      <main className="app-main">
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          onStopGeneration={handleStopGeneration}
          onClearChat={handleClearChat}
          isStreaming={isStreaming}
          selectedDocCount={selectedDocIds.length}
          totalDocCount={documents.length}
        />
      </main>
    </div>
  );
}
