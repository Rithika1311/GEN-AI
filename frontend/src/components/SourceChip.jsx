import React, { useState } from "react";

export default function SourceChip({ source }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="source-chip-container">
      <button
        type="button"
        className={`source-chip ${expanded ? "active" : ""}`}
        onClick={() => setExpanded(!expanded)}
        title="Click to view retrieved passage"
      >
        <span className="source-icon">📄</span>
        <span className="source-name">{source.filename}</span>
        <span className="source-page">p.{source.page}</span>
        <span className="source-score" title={`Relevance score: ${(source.similarity_score * 100).toFixed(0)}%`}>
          {(source.similarity_score * 100).toFixed(0)}%
        </span>
      </button>

      {expanded && (
        <div className="source-passage-card">
          <div className="passage-header">
            <strong>{source.filename}</strong> (Page {source.page}, Chunk #{source.chunk_index})
            <button className="close-btn" onClick={() => setExpanded(false)}>✕</button>
          </div>
          <div className="passage-body">
            "{source.text}"
          </div>
        </div>
      )}
    </div>
  );
}
