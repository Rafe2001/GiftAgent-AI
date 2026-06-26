'use client';
import { useState, useEffect, use } from "react";
import Link from "next/link";

const API_BASE = "http://localhost:8000/api";

const WORKFLOW_STEPS = [
  { key: "ingest", label: "Ingest", icon: "📥" },
  { key: "extract_signals", label: "Signals", icon: "🔍" },
  { key: "filter_signals", label: "Filter", icon: "🛡️" },
  { key: "generate_queries", label: "Queries", icon: "🔎" },
  { key: "search_products", label: "Search", icon: "🛒" },
  { key: "validate_products", label: "Validate", icon: "✅" },
  { key: "rank_gifts", label: "Rank", icon: "🏆" },
  { key: "generate_messages", label: "Messages", icon: "💬" },
  { key: "finalized", label: "Done", icon: "✨" },
];

function getStepIndex(stepKey) {
  return WORKFLOW_STEPS.findIndex(s => s.key === stepKey);
}

export default function ContactDetailPage({ params }) {
  const resolvedParams = use(params);
  const contactId = resolvedParams.id;
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("recommendations");
  const [toast, setToast] = useState(null);
  const [reviewing, setReviewing] = useState(false);

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchData = async () => {
    try {
      const res = await fetch(`${API_BASE}/recommendations/${contactId}`);
      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error("Failed to fetch:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 4000);
    return () => clearInterval(interval);
  }, [contactId]);

  const handleReview = async (action) => {
    setReviewing(true);
    try {
      const res = await fetch(`${API_BASE}/recommendations/${contactId}/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, notes: "" }),
      });
      const result = await res.json();
      setData(result);
      showToast(`Recommendation ${action}ed!`, action === "approve" ? "success" : "info");
    } catch (err) {
      showToast(`Failed to ${action}`, "error");
    } finally {
      setReviewing(false);
    }
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="loading-overlay">
          <div className="loading-spinner" style={{ width: 40, height: 40 }}></div>
          <p>Loading recommendation...</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <div className="empty-state-title">Contact not found</div>
          <Link href="/" className="btn btn-ghost" style={{ marginTop: "1rem" }}>← Back to Dashboard</Link>
        </div>
      </div>
    );
  }

  const currentStepIdx = getStepIndex(data.current_step);
  const isProcessing = data.workflow_status === "processing";
  const signals = data.profile_signals || {};
  const gifts = data.recommended_gifts || [];
  const trace = data.search_trace || {};
  const review = data.human_review || {};

  return (
    <div className="page-container" style={{ maxWidth: 1100, margin: "0 auto" }}>
      {/* Back + Header */}
      <Link href="/" style={{ color: "var(--text-muted)", fontSize: "0.85rem", display: "inline-flex", alignItems: "center", gap: 4, marginBottom: "1rem" }}>
        ← Back to Dashboard
      </Link>

      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 className="page-title">{data.contact_name || "Unknown Contact"}</h1>
          <p className="page-subtitle">Gift recommendation details and review</p>
        </div>
        <span className={`status-badge ${data.workflow_status || "pending"}`}>
          <span className="status-dot"></span>
          {(data.workflow_status || "pending").replace(/_/g, " ")}
        </span>
      </div>

      {/* Workflow Progress */}
      <div className="card" style={{ marginBottom: "1.5rem" }}>
        <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "0.75rem" }}>
          Workflow Progress
        </div>
        <div className="workflow-progress">
          {WORKFLOW_STEPS.map((step, i) => (
            <div key={step.key} className="workflow-step">
              <div className={`step-node ${
                i < currentStepIdx ? "completed" :
                i === currentStepIdx ? (isProcessing ? "active" : "completed") : ""
              }`}>
                {step.icon} {step.label}
              </div>
              {i < WORKFLOW_STEPS.length - 1 && (
                <div className={`step-connector ${i < currentStepIdx ? "completed" : ""}`}></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {["recommendations", "signals", "search_trace"].map(tab => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "recommendations" && "🎁 Recommendations"}
            {tab === "signals" && "🔍 Profile Signals"}
            {tab === "search_trace" && "🔎 Search Trace"}
          </button>
        ))}
      </div>

      {/* Tab Content: Recommendations */}
      {activeTab === "recommendations" && (
        <div className="animate-in">
          {/* Review Panel */}
          {gifts.length > 0 && (
            <div className="review-panel" style={{ marginBottom: "1.5rem" }}>
              <div className="review-status">
                <span style={{ fontWeight: 600 }}>Human Review</span>
                <span className={`status-badge ${review.status || "pending_review"}`}>
                  <span className="status-dot"></span>
                  {(review.status || "pending_review").replace(/_/g, " ")}
                </span>
              </div>
              <div className="review-actions">
                <button
                  className="btn btn-success"
                  onClick={() => handleReview("approve")}
                  disabled={reviewing || review.status === "approved"}
                >
                  ✅ Approve
                </button>
                <button
                  className="btn btn-danger"
                  onClick={() => handleReview("reject")}
                  disabled={reviewing || review.status === "rejected"}
                >
                  ❌ Reject
                </button>
                <button
                  className="btn btn-ghost"
                  onClick={() => handleReview("regenerate")}
                  disabled={reviewing}
                >
                  🔄 Regenerate
                </button>
              </div>
            </div>
          )}

          {/* Gift Cards */}
          {gifts.length > 0 ? (
            <div className="gifts-grid">
              {gifts.map((gift, i) => (
                <div key={i} className={`gift-card animate-in animate-delay-${i + 1}`}>
                  <div className={`gift-rank rank-${gift.rank}`}>
                    #{gift.rank} Pick
                  </div>
                  <div className="gift-header">
                    <div className="gift-name">{gift.gift_name}</div>
                    <div className="gift-price">{gift.estimated_price || "Price N/A"}</div>
                  </div>
                  <div className="gift-store">{gift.store || "Online Store"}</div>

                  <div className="gift-section">
                    <div className="gift-section-title">Why this gift</div>
                    <div className="gift-section-text">{gift.why_this_gift}</div>
                  </div>

                  <div className="gift-section">
                    <div className="gift-section-title">Personalisation reasoning</div>
                    <div className="gift-section-text">{gift.personalisation_reasoning}</div>
                  </div>

                  {gift.personalised_message && (
                    <div className="gift-section">
                      <div className="gift-section-title">Personalised message</div>
                      <div className="gift-message">"{gift.personalised_message}"</div>
                    </div>
                  )}

                  {gift.assumptions?.length > 0 && (
                    <div className="gift-section">
                      <div className="gift-section-title">Assumptions</div>
                      <div className="gift-section-text" style={{ fontSize: "0.8rem" }}>
                        {gift.assumptions.map((a, j) => (
                          <span key={j} className="signal-badge weak" style={{ marginRight: 4, marginBottom: 4 }}>
                            {a}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="gift-footer">
                    <div className="confidence-bar">
                      <span>Confidence</span>
                      <div className="confidence-track">
                        <div
                          className="confidence-fill"
                          style={{
                            width: `${(gift.confidence_score || 0.5) * 100}%`,
                            background: gift.confidence_score >= 0.7 ? "var(--accent-green)" :
                              gift.confidence_score >= 0.4 ? "var(--accent-amber)" : "var(--accent-red)",
                          }}
                        ></div>
                      </div>
                      <span>{((gift.confidence_score || 0.5) * 100).toFixed(0)}%</span>
                    </div>
                    <span className={`risk-badge ${gift.risk_level || "medium"}`}>
                      {gift.risk_level || "medium"} risk
                    </span>
                    {gift.product_url && (
                      <a href={gift.product_url} target="_blank" rel="noopener noreferrer" className="gift-link">
                        🔗 View Product
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">{isProcessing ? "⏳" : "🎁"}</div>
              <div className="empty-state-title">
                {isProcessing ? "Generating recommendations..." : "No recommendations yet"}
              </div>
              {isProcessing && <div className="loading-spinner" style={{ marginTop: "1rem" }}></div>}
            </div>
          )}
        </div>
      )}

      {/* Tab Content: Signals */}
      {activeTab === "signals" && (
        <div className="card animate-in">
          {signals.strong_signals?.length > 0 && (
            <div className="signal-section">
              <div className="signal-label">✅ Strong Signals</div>
              <div className="signals-group">
                {signals.strong_signals.map((s, i) => (
                  <span key={i} className="signal-badge strong">{s}</span>
                ))}
              </div>
            </div>
          )}
          {signals.weak_signals?.length > 0 && (
            <div className="signal-section">
              <div className="signal-label">⚠️ Weak Signals (Assumptions)</div>
              <div className="signals-group">
                {signals.weak_signals.map((s, i) => (
                  <span key={i} className="signal-badge weak">{s}</span>
                ))}
              </div>
            </div>
          )}
          {signals.signals_to_avoid?.length > 0 && (
            <div className="signal-section">
              <div className="signal-label">🚫 Signals to Avoid</div>
              <div className="signals-group">
                {signals.signals_to_avoid.map((s, i) => (
                  <span key={i} className="signal-badge avoid">{s}</span>
                ))}
              </div>
            </div>
          )}
          {!signals.strong_signals?.length && !signals.weak_signals?.length && (
            <div className="empty-state">
              <div className="empty-state-icon">🔍</div>
              <div className="empty-state-title">
                {isProcessing ? "Extracting signals..." : "No signals extracted yet"}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab Content: Search Trace */}
      {activeTab === "search_trace" && (
        <div className="animate-in">
          <div className="card" style={{ marginBottom: "1rem" }}>
            <div className="section-title" style={{ marginBottom: "1rem" }}>🔎 Search Queries Used</div>
            {trace.queries_used?.length > 0 ? (
              <div className="trace-queries">
                {trace.queries_used.map((q, i) => (
                  <div key={i} className="trace-query">
                    <span className="trace-query-num">Q{i + 1}</span>
                    {q}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                {isProcessing ? "Search queries being generated..." : "No search queries yet"}
              </div>
            )}
          </div>
          <div className="card">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div className="section-title">📦 Products Considered</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--accent-blue)" }}>
                {trace.products_considered_count || 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Errors */}
      {data.errors?.length > 0 && (
        <div className="card" style={{ marginTop: "1.5rem", borderColor: "rgba(239, 68, 68, 0.3)" }}>
          <div className="section-title" style={{ color: "var(--accent-red)" }}>⚠️ Workflow Errors</div>
          {data.errors.map((e, i) => (
            <div key={i} style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
              • {e}
            </div>
          ))}
        </div>
      )}

      {/* Toast */}
      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
}
