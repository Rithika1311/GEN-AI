// API client for DocuMind backend

const API_BASE = "";

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/api/documents`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to fetch documents (${res.status})`);
  }
  const data = await res.json();
  return data.documents || [];
}

export async function uploadFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const res = await fetch(`${API_BASE}/api/documents`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  const data = await res.json();
  return data.documents || [];
}

export async function deleteDocument(documentId) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
    method: "DELETE",
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete document (${res.status})`);
  }

  return await res.json();
}

export async function streamChat({
  question,
  document_ids = null,
  history = [],
  onToken,
  onSources,
  onDone,
  onError,
  signal,
}) {
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        question,
        document_ids: document_ids && document_ids.length > 0 ? document_ids : null,
        history,
      }),
      signal,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Chat request failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop(); // Retain incomplete chunk

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          const jsonStr = trimmed.slice(6);
          try {
            const data = JSON.parse(jsonStr);
            if (data.type === "token") {
              onToken(data.content);
            } else if (data.type === "sources") {
              onSources(data.sources || []);
            } else if (data.type === "done") {
              onDone();
            }
          } catch (err) {
            console.error("Error parsing SSE event:", err, line);
          }
        }
      }
    }

    onDone();
  } catch (err) {
    if (err.name === "AbortError") {
      onDone();
      return;
    }
    onError(err);
  }
}
