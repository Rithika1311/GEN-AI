import React from "react";

export default function DocumentList({
  documents,
  selectedDocIds,
  onToggleSelect,
  onSelectAll,
  onDeleteDocument,
  isLoading,
}) {
  const allSelected = documents.length > 0 && selectedDocIds.length === documents.length;

  return (
    <div className="document-list-container">
      <div className="document-list-header">
        <div className="header-left">
          <h3>Uploaded Documents ({documents.length})</h3>
        </div>
        {documents.length > 0 && (
          <button
            type="button"
            className="select-all-btn"
            onClick={() => onSelectAll(!allSelected)}
          >
            {allSelected ? "Deselect All" : "Select All"}
          </button>
        )}
      </div>

      {documents.length === 0 ? (
        <div className="empty-docs-state">
          <p>No documents uploaded yet.</p>
          <span>Upload PDF files above to start asking questions with citations.</span>
        </div>
      ) : (
        <div className="document-cards-list">
          {documents.map((doc) => {
            const isSelected = selectedDocIds.includes(doc.id);
            return (
              <div
                key={doc.id}
                className={`document-card ${isSelected ? "selected" : ""}`}
              >
                <div className="document-card-main">
                  <label className="checkbox-container">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelect(doc.id)}
                    />
                    <span className="checkmark" />
                  </label>
                  <div className="document-info">
                    <div className="document-name" title={doc.filename}>
                      {doc.filename}
                    </div>
                    <div className="document-meta">
                      <span>{doc.page_count} {doc.page_count === 1 ? "page" : "pages"}</span>
                      <span>•</span>
                      <span>{doc.chunk_count} chunks</span>
                    </div>
                  </div>
                </div>

                <button
                  type="button"
                  className="delete-doc-btn"
                  title="Delete document and vectors"
                  onClick={() => onDeleteDocument(doc.id, doc.filename)}
                >
                  🗑️
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
