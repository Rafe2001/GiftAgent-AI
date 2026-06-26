'use client';
import { useState, useEffect } from "react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api";

// Avatar color based on name
function getAvatarColor(name) {
  const colors = [
    "linear-gradient(135deg, #3b82f6, #8b5cf6)",
    "linear-gradient(135deg, #ec4899, #f59e0b)",
    "linear-gradient(135deg, #10b981, #3b82f6)",
    "linear-gradient(135deg, #8b5cf6, #ec4899)",
    "linear-gradient(135deg, #f59e0b, #ef4444)",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return colors[Math.abs(hash) % colors.length];
}

function getInitials(name) {
  return name.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2);
}

export default function Dashboard() {
  const [contacts, setContacts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchData = async () => {
    try {
      const [contactsRes, recsRes] = await Promise.all([
        fetch(`${API_BASE}/contacts`).then(r => r.json()).catch(() => ({ contacts: [] })),
        fetch(`${API_BASE}/recommendations`).then(r => r.json()).catch(() => ({ recommendations: [] })),
      ]);
      setContacts(contactsRes.contacts || []);
      setRecommendations(recsRes.recommendations || []);
    } catch (err) {
      console.error("Failed to fetch data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll every 5 seconds while any contact is processing
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await fetch(`${API_BASE}/recommendations/generate`, { method: "POST" });
      const data = await res.json();
      showToast(`Processing ${data.jobs?.length || 0} contacts...`, "info");
      // Start polling
      setTimeout(fetchData, 2000);
    } catch (err) {
      showToast("Failed to start generation", "error");
    } finally {
      setGenerating(false);
    }
  };

  // Merge contacts with recommendations
  const mergedContacts = contacts.map(c => {
    const rec = recommendations.find(r => r.contact_id === c.contact_id);
    return { ...c, recommendation: rec };
  });

  const stats = {
    total: contacts.length,
    completed: recommendations.filter(r => ["completed", "completed_with_issues", "approved"].includes(r.workflow_status)).length,
    pending: recommendations.filter(r => r.workflow_status === "pending_review" || r.human_review?.status === "pending_review").length,
    processing: recommendations.filter(r => r.workflow_status === "processing").length,
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-overlay">
          <div className="loading-spinner" style={{ width: 40, height: 40 }}></div>
          <p>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Manage contacts and gift recommendations</p>
        </div>
        <div className="btn-group">
          <Link href="/upload" className="btn btn-ghost">📤 Upload Contacts</Link>
          {contacts.length > 0 && (
            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={generating}
            >
              {generating ? (
                <><div className="loading-spinner"></div> Generating...</>
              ) : (
                <>✨ Generate Recommendations</>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      {contacts.length > 0 && (
        <div className="stats-grid animate-in">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Contacts</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ background: "linear-gradient(135deg, #10b981, #3b82f6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{stats.completed}</div>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ background: "linear-gradient(135deg, #f59e0b, #ec4899)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{stats.pending}</div>
            <div className="stat-label">Pending Review</div>
          </div>
          <div className="stat-card">
            <div className="stat-value" style={{ background: "linear-gradient(135deg, #3b82f6, #8b5cf6)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>{stats.processing}</div>
            <div className="stat-label">Processing</div>
          </div>
        </div>
      )}

      {/* Contact Cards */}
      {mergedContacts.length === 0 ? (
        <div className="empty-state animate-in">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No contacts yet</div>
          <p className="page-subtitle">Upload contacts to get started with gift recommendations</p>
          <Link href="/upload" className="btn btn-primary" style={{ marginTop: "1rem" }}>
            📤 Upload Contacts
          </Link>
        </div>
      ) : (
        <div className="contacts-grid">
          {mergedContacts.map((contact, i) => {
            const status = contact.recommendation?.workflow_status || contact.recommendation?.human_review?.status || contact.status || "uploaded";
            return (
              <Link
                key={contact.contact_id}
                href={`/contact/${contact.contact_id}`}
                style={{ textDecoration: "none" }}
              >
                <div className={`card card-clickable animate-in animate-delay-${(i % 4) + 1}`}>
                  <div className="contact-card">
                    <div
                      className="contact-avatar"
                      style={{ background: getAvatarColor(contact.name) }}
                    >
                      {getInitials(contact.name)}
                    </div>
                    <div className="contact-info">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <div className="contact-name">{contact.name}</div>
                        <span className={`status-badge ${status}`}>
                          <span className="status-dot"></span>
                          {status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <div className="contact-role">{contact.role} at {contact.company}</div>
                      <div className="contact-meta">
                        <span className="meta-item">📍 {contact.location}</span>
                        {contact.recommendation?.recommended_gifts?.length > 0 && (
                          <span className="meta-item">🎁 {contact.recommendation.recommended_gifts.length} gifts</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}

      {/* Toast */}
      {toast && (
        <div className={`toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
