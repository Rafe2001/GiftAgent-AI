'use client';
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";

const API_BASE = "http://localhost:8000/api";

const SAMPLE_DATA = `[
  {
    "name": "Aarav Mehta",
    "role": "VP Sales",
    "company": "Acme Corp",
    "location": "Bengaluru, India",
    "linkedin_profile": {
      "headline": "VP Sales at Acme Corp | Enterprise SaaS | GTM Leadership",
      "about": "I enjoy building high-performing revenue teams and scaling SaaS businesses across India and Southeast Asia.",
      "experience": [
        {
          "title": "VP Sales",
          "company": "Acme Corp",
          "description": "Leading enterprise sales, strategic accounts, and GTM expansion."
        }
      ],
      "recent_posts": [
        "Great sales teams are built on trust, coaching, and consistency.",
        "Still recovering from yesterday's India vs Australia match. What a game!"
      ],
      "recent_comments": [
        "Cricket teaches leadership better than most management books."
      ],
      "engaged_topics": ["Cricket", "Revenue leadership", "SaaS GTM", "Team building"]
    },
    "relationship_context": {
      "relationship_type": "Prospective customer",
      "last_interaction": "Positive discovery call last week",
      "business_goal": "Nurture relationship before follow-up meeting"
    },
    "gift_context": {
      "occasion": "Post-meeting thank you",
      "budget_min": 3000,
      "budget_max": 5000,
      "currency": "INR",
      "country": "India"
    }
  }
]`;

export default function UploadPage() {
  const [jsonText, setJsonText] = useState("");
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);
  const [dragover, setDragover] = useState(false);
  const fileRef = useRef(null);
  const router = useRouter();

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const validateJSON = (text) => {
    try {
      let parsed = JSON.parse(text);
      // If wrapped in a {"contacts": [...]} object, extract the contacts array
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed) && Array.isArray(parsed.contacts)) {
        parsed = parsed.contacts;
      }
      const contacts = Array.isArray(parsed) ? parsed : [parsed];

      for (const c of contacts) {
        if (!c.name) return "Each contact must have a 'name' field";
      }

      return null; // valid
    } catch (e) {
      return `Invalid JSON: ${e.message}`;
    }
  };

  const handleUpload = async () => {
    const validationError = validateJSON(jsonText);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");
    setUploading(true);

    try {
      let parsed = JSON.parse(jsonText);
      // If wrapped in a {"contacts": [...]} object, extract the contacts array
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed) && Array.isArray(parsed.contacts)) {
        parsed = parsed.contacts;
      }
      const contacts = Array.isArray(parsed) ? parsed : [parsed];

      const res = await fetch(`${API_BASE}/contacts/upload`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ contacts }),
      });

      if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);

      const data = await res.json();
      showToast(`Uploaded ${data.contacts?.length || 0} contacts!`, "success");

      // Auto-generate recommendations
      await fetch(`${API_BASE}/recommendations/generate`, { method: "POST" });

      // Redirect to dashboard after short delay
      setTimeout(() => router.push("/"), 1500);
    } catch (err) {
      setError(err.message);
      showToast("Upload failed", "error");
    } finally {
      setUploading(false);
    }
  };

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragover(false);
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (file && file.name.endsWith(".json")) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setJsonText(ev.target.result);
        setError("");
      };
      reader.readAsText(file);
    } else {
      setError("Please upload a .json file");
    }
  };

  const loadSample = () => {
    setJsonText(SAMPLE_DATA);
    setError("");
  };

  return (
    <div className="page-container" style={{ maxWidth: 900, margin: "0 auto" }}>
      <div className="page-header">
        <h1 className="page-title">Upload Contacts</h1>
        <p className="page-subtitle">
          Paste JSON contact data or upload a .json file to generate personalised gift recommendations
        </p>
      </div>

      {/* File Upload Area */}
      <div
        className={`upload-area ${dragover ? "dragover" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
        onDragLeave={() => setDragover(false)}
        onDrop={handleFileDrop}
        onClick={() => fileRef.current?.click()}
        style={{ marginBottom: "1.5rem" }}
      >
        <div className="upload-icon">📁</div>
        <div className="upload-text">Drop a JSON file here or click to browse</div>
        <div className="upload-hint">Supports .json files with contact data</div>
        <input
          ref={fileRef}
          type="file"
          accept=".json"
          onChange={handleFileDrop}
          style={{ display: "none" }}
        />
      </div>

      {/* Divider */}
      <div style={{ textAlign: "center", margin: "1rem 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
        — or paste JSON below —
      </div>

      {/* JSON Editor */}
      <textarea
        className="json-editor"
        value={jsonText}
        onChange={(e) => { setJsonText(e.target.value); setError(""); }}
        placeholder='Paste your contact JSON here...

Example:
[
  {
    "name": "John Doe",
    "role": "VP Sales",
    "company": "Acme Corp",
    "location": "Bengaluru, India",
    "linkedin_profile": { ... },
    "relationship_context": { ... },
    "gift_context": { ... }
  }
]'
      />

      {error && (
        <div className="json-error">⚠️ {error}</div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "1rem" }}>
        <button className="btn btn-ghost" onClick={loadSample}>
          📋 Load Sample Data
        </button>
        <div className="btn-group">
          <button
            className="btn btn-ghost"
            onClick={() => { setJsonText(""); setError(""); }}
            disabled={!jsonText}
          >
            Clear
          </button>
          <button
            className="btn btn-primary"
            onClick={handleUpload}
            disabled={!jsonText || uploading}
          >
            {uploading ? (
              <><div className="loading-spinner"></div> Uploading...</>
            ) : (
              <>🚀 Upload & Generate</>
            )}
          </button>
        </div>
      </div>

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
