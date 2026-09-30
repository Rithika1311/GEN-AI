import React, { useState, useRef } from "react";

export default function UploadPanel({ onUploadSuccess }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

  const validateFiles = (files) => {
    const valid = [];
    for (const file of files) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setErrorMessage(`"${file.name}" is not a PDF file. Only PDF files are allowed.`);
        return null;
      }
      if (file.size > MAX_FILE_SIZE) {
        setErrorMessage(`"${file.name}" exceeds the 10 MB size limit.`);
        return null;
      }
      valid.push(file);
    }
    return valid;
  };

  const handleFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    setErrorMessage("");
    const validFiles = validateFiles(Array.from(fileList));
    if (!validFiles || validFiles.length === 0) return;

    setIsUploading(true);
    setStatusMessage(`Uploading and processing ${validFiles.length} file(s)...`);

    try {
      await onUploadSuccess(validFiles);
      setStatusMessage("Upload & indexing complete!");
      setTimeout(() => setStatusMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Failed to upload document.");
      setStatusMessage("");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <div className="upload-panel">
      <div
        className={`drop-zone ${isDragging ? "dragging" : ""} ${isUploading ? "uploading" : ""}`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={(e) => handleFiles(e.target.files)}
          multiple
          accept=".pdf,application/pdf"
          style={{ display: "none" }}
        />
        <div className="drop-zone-content">
          <span className="drop-icon">{isUploading ? "⏳" : "📤"}</span>
          <p className="drop-primary">
            {isUploading ? "Processing documents..." : "Drag & drop PDF files here"}
          </p>
          <span className="drop-secondary">
            or <button type="button" className="browse-btn">browse files</button>
          </span>
          <span className="drop-hint">Max 10 MB per file • PDF only</span>
        </div>
      </div>

      {isUploading && (
        <div className="upload-progress">
          <div className="progress-bar-indeterminate" />
          <span className="progress-status">{statusMessage}</span>
        </div>
      )}

      {errorMessage && (
        <div className="upload-error">
          <span>⚠️ {errorMessage}</span>
          <button onClick={() => setErrorMessage("")}>✕</button>
        </div>
      )}
    </div>
  );
}
