import React, { useEffect, useState, useCallback } from "react";
import api from "../services/api.js";
import { getPatientConsultations, getConsultationHistory, sendFollowUp } from "../services/consultation.js";

/* ------------------------------------------------------------------ */
/* Helper Components                                                  */
/* ------------------------------------------------------------------ */

const SeverityBadge = ({ level }) => {
  const colors = {
    HIGH: "bg-red-100 text-red-700 border-red-200",
    MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
    LOW: "bg-emerald-100 text-emerald-700 border-emerald-200",
  };
  return (
    <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${colors[level] || colors.LOW}`}>
      {level}
    </span>
  );
};

const StatusBadge = ({ status }) => {
  const colors = {
    pending: "bg-amber-100 text-amber-700 border-amber-200",
    responded: "bg-blue-100 text-blue-700 border-blue-200",
    resolved: "bg-emerald-100 text-emerald-700 border-emerald-200",
  };
  return (
    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
};

const SymptomChip = ({ label }) => (
  <span className="inline-block bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-1 rounded-md border border-slate-200 mr-1.5 mb-1.5">
    {label}
  </span>
);

const SectionTitle = ({ children, className = "" }) => (
  <h4 className={`text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 ${className}`}>{children}</h4>
);

const InfoBox = ({ children, className = "" }) => (
  <div className={`bg-slate-50 rounded-lg p-3 text-sm text-slate-700 border border-slate-100 ${className}`}>
    {children}
  </div>
);

const DoctorBadge = ({ name, specialization }) => (
  <div className="flex items-center gap-2 mt-1">
    <div className="w-5 h-5 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-[10px] font-bold">
      {name?.charAt(0) || "D"}
    </div>
    <p className="text-xs text-slate-600">
      <span className="font-semibold">Dr. {name}</span>
      <span className="text-slate-400"> ({specialization || "General Practitioner"})</span>
    </p>
    <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 font-medium">
      Verified
    </span>
  </div>
);

/* ------------------------------------------------------------------ */
/* Chat Modal                                                         */
/* ------------------------------------------------------------------ */

const ChatModal = ({ consultation, onClose }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await getConsultationHistory(consultation.id);
      const history = res.data.history || [];
      // Convert history to chat messages
      const chatMessages = history
        .filter((h) => h.type === "followup")
        .map((h) => ({
          id: h.timestamp,
          sender: h.data.sender_role,
          senderName: h.data.sender_name,
          text: h.data.message,
          timestamp: h.timestamp_relative,
        }));
      setMessages(chatMessages);
    } catch (err) {
      console.error("Failed to load chat history", err);
    } finally {
      setLoading(false);
    }
  }, [consultation.id]);

  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, 5000);
    return () => clearInterval(interval);
  }, [fetchHistory]);

  const handleSend = async () => {
    if (!newMessage.trim()) return;
    setSending(true);
    try {
      await sendFollowUp(consultation.id, {
        message: newMessage.trim(),
        sender_role: "patient",
      });
      setNewMessage("");
      await fetchHistory();
    } catch (err) {
      alert(err.response?.data?.error || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg h-[600px] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-700">💬 Chat with Dr. {consultation.doctor_name}</h3>
            <p className="text-xs text-slate-400">{consultation.predicted_condition}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600" />
            </div>
          )}

          {!loading && messages.length === 0 && (
            <div className="text-center py-8">
              <p className="text-sm text-slate-400">No messages yet.</p>
              <p className="text-xs text-slate-400 mt-1">Start the conversation with your doctor.</p>
            </div>
          )}

          {messages.map((msg, idx) => {
            const isPatient = msg.sender === "patient";
            return (
              <div key={idx} className={`flex ${isPatient ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                    isPatient
                      ? "bg-primary-600 text-white rounded-br-none"
                      : "bg-slate-100 text-slate-700 border border-slate-200 rounded-bl-none"
                  }`}
                >
                  <p className="text-[10px] opacity-70 mb-0.5">{msg.senderName}</p>
                  <p>{msg.text}</p>
                  <p className={`text-[10px] mt-1 ${isPatient ? "text-primary-200" : "text-slate-400"}`}>
                    {msg.timestamp}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Input */}
        <div className="border-t border-slate-100 p-3">
          <div className="flex gap-2">
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type a message..."
              className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              onClick={handleSend}
              disabled={sending || !newMessage.trim()}
              className="px-4 bg-primary-600 text-white text-sm font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {sending ? "..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* History Modal                                                      */
/* ------------------------------------------------------------------ */

const HistoryModal = ({ history, onClose }) => {
  if (!history) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
          <h3 className="text-sm font-bold text-slate-700">Consultation History</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-lg">&times;</button>
        </div>
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {history.length === 0 ? (
            <p className="text-sm text-slate-400 text-center">No history available.</p>
          ) : (
            history.map((item, idx) => (
              <div key={idx} className="relative pl-4 border-l-2 border-slate-200">
                <div className="absolute -left-[5px] top-1 w-2 h-2 rounded-full bg-primary-500" />
                <p className="text-[10px] text-slate-400 font-medium uppercase">{item.type}</p>
                <p className="text-xs text-slate-500 mb-1">{item.timestamp_relative}</p>
                {item.type === "created" && (
                  <div className="text-sm text-slate-700 space-y-1">
                    <p><span className="font-semibold">Symptoms:</span> {item.data.symptoms}</p>
                    <p><span className="font-semibold">Condition:</span> {item.data.predicted_condition || "N/A"}</p>
                    <p><span className="font-semibold">Priority:</span> {item.data.priority}</p>
                  </div>
                )}
                {item.type === "responded" && (
                  <div className="text-sm text-slate-700 space-y-1">
                    {item.data.acknowledgement && <p>{item.data.acknowledgement}</p>}
                    {item.data.advice && <p className="text-emerald-700">{item.data.advice}</p>}
                    {item.data.tests && <pre className="whitespace-pre-wrap font-sans text-xs bg-slate-50 p-2 rounded border border-slate-100">{item.data.tests}</pre>}
                    {item.data.urgency && <p className="text-amber-700 font-medium">{item.data.urgency}</p>}
                  </div>
                )}
                {item.type === "followup" && (
                  <div className="text-sm text-slate-700">
                    <p className="font-semibold text-xs text-slate-500">{item.data.sender_name} ({item.data.sender_role})</p>
                    <p>{item.data.message}</p>
                  </div>
                )}
                {item.type === "resolved" && (
                  <p className="text-sm text-emerald-700 font-medium">Case marked as resolved.</p>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Main Dashboard                                                     */
/* ------------------------------------------------------------------ */

export default function PatientDashboard() {
  const [predictions, setPredictions] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState(null);
  const [history, setHistory] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [chatConsultation, setChatConsultation] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const [predRes, consultRes] = await Promise.all([
        api.get("/patient/predictions"),
        getPatientConsultations(),
      ]);
      setPredictions(predRes.data.predictions || []);
      setConsultations(consultRes.data.consultations || []);
    } catch (err) {
      setError("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const getCardTint = (priority) => {
    if (priority === "HIGH") return "border-l-4 border-l-red-500 bg-red-50/30";
    if (priority === "MEDIUM") return "border-l-4 border-l-amber-500 bg-amber-50/30";
    return "border-l-4 border-l-emerald-500 bg-emerald-50/30";
  };

  const formatTimestamp = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short",
    });
  };

  const handleViewHistory = async (consultationId) => {
    try {
      const res = await getConsultationHistory(consultationId);
      setHistory(res.data.history || []);
      setShowHistory(true);
    } catch (err) {
      alert(err.response?.data?.error || "Failed to load history");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600"></div>
        <span className="ml-3 text-slate-500">Loading dashboard...</span>
      </div>
    );
  }

  if (error) return <p className="text-red-500 p-6">{error}</p>;

  return (
    <div className="min-h-screen bg-slate-50">
      {showHistory && <HistoryModal history={history} onClose={() => setShowHistory(false)} />}
      {chatConsultation && <ChatModal consultation={chatConsultation} onClose={() => setChatConsultation(null)} />}

      <div className="max-w-5xl mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-slate-800">Patient Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">View your consultations, chat with doctors, and manage your health</p>
        </div>

        {/* Disclaimer */}
        <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-2 mb-6 flex items-center gap-2">
          <span className="text-blue-500 text-sm">ℹ️</span>
          <p className="text-xs text-blue-700">
            AI-assisted predictions are not a final medical diagnosis. Always consult your doctor.
          </p>
        </div>

        {/* Consultations Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-800">My Consultations</h2>
            <span className="text-sm text-slate-500">{consultations.length} total</span>
          </div>

          {consultations.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <p className="text-slate-500 text-sm">No consultations yet.</p>
              <p className="text-slate-400 text-xs mt-1">Go to Submit Symptoms to start one.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {consultations.map((c) => {
                const isExpanded = expandedId === c.id;
                const hasResponse = c.status === "responded" || c.status === "resolved";
                const canChat = c.status !== "resolved";

                return (
                  <div
                    key={c.id}
                    className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden transition-all ${getCardTint(c.priority)}`}
                  >
                    {/* Card Header - Always visible */}
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : c.id)}
                      className="w-full text-left p-4 flex items-start justify-between gap-3"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <SeverityBadge level={c.priority} />
                          <StatusBadge status={c.status} />
                          <span className="text-xs text-slate-400">{c.created_at_relative}</span>
                        </div>
                        <p className="text-sm font-semibold text-slate-800 mt-2">
                          {c.predicted_condition || "Unspecified Condition"}
                        </p>
                        <div className="flex flex-wrap mt-2">
                          {(c.symptoms_clean || c.symptoms)
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean)
                            .slice(0, 5)
                            .map((s, i) => (
                              <SymptomChip key={i} label={s} />
                            ))}
                        </div>
                        <DoctorBadge name={c.doctor_name} specialization={c.doctor_specialization} />
                      </div>
                      <span className="text-slate-400 text-lg">{isExpanded ? "▲" : "▼"}</span>
                    </button>

                    {/* Expanded Details */}
                    {isExpanded && (
                      <div className="px-4 pb-4 border-t border-slate-100 pt-3 space-y-4">
                        {/* Timestamp */}
                        <p className="text-xs text-slate-400">Submitted on {formatTimestamp(c.created_at)}</p>

                        {/* Full Symptoms */}
                        <div>
                          <SectionTitle>All Symptoms</SectionTitle>
                          <div className="flex flex-wrap">
                            {(c.symptoms_clean || c.symptoms)
                              .split(",")
                              .map((s) => s.trim())
                              .filter(Boolean)
                              .map((s, i) => (
                                <SymptomChip key={i} label={s} />
                              ))}
                          </div>
                        </div>

                        {/* Patient Message */}
                        {c.message && (
                          <div>
                            <SectionTitle>Your Message</SectionTitle>
                            <InfoBox className="italic">{c.message}</InfoBox>
                          </div>
                        )}

                        {/* AI Insight */}
                        <div className="bg-indigo-50 rounded-lg p-3 border border-indigo-100">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-indigo-500 text-xs">🤖</span>
                            <SectionTitle className="!mb-0">AI Insight</SectionTitle>
                          </div>
                          <p className="text-sm text-indigo-800">{c.ai_insight}</p>
                          <p className="text-xs text-indigo-600 mt-1">
                            Risk: <span className="font-bold">{c.ai_risk_level}</span>
                          </p>
                        </div>

                        {/* Doctor Response */}
                        {hasResponse ? (
                          <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-100">
                            <div className="flex items-center gap-2 mb-3">
                              <span className="text-emerald-600">✅</span>
                              <h4 className="text-sm font-bold text-emerald-800">Doctor Response</h4>
                            </div>

                            {c.response_acknowledgement && (
                              <div className="mb-3">
                                <SectionTitle>Acknowledgement</SectionTitle>
                                <InfoBox className="bg-white">{c.response_acknowledgement}</InfoBox>
                              </div>
                            )}

                            {c.response_advice && (
                              <div className="mb-3">
                                <SectionTitle>Advice</SectionTitle>
                                <InfoBox className="bg-white border-emerald-200 text-emerald-800">
                                  {c.response_advice}
                                </InfoBox>
                              </div>
                            )}

                            {c.response_tests && (
                              <div className="mb-3">
                                <SectionTitle>Recommended Tests</SectionTitle>
                                <InfoBox className="bg-white">
                                  <pre className="whitespace-pre-wrap font-sans text-sm">{c.response_tests}</pre>
                                </InfoBox>
                              </div>
                            )}

                            {c.response_urgency && (
                              <div>
                                <SectionTitle>Urgency</SectionTitle>
                                <InfoBox
                                  className={`${
                                    c.priority === "HIGH"
                                      ? "bg-red-50 border-red-200 text-red-800"
                                      : "bg-amber-50 border-amber-200 text-amber-800"
                                  }`}
                                >
                                  {c.response_urgency}
                                </InfoBox>
                              </div>
                            )}

                            {c.responded_at_relative && (
                              <p className="text-xs text-emerald-600 mt-3">
                                Responded {c.responded_at_relative}
                              </p>
                            )}
                          </div>
                        ) : (
                          <div className="bg-amber-50 rounded-lg p-3 border border-amber-100 flex items-center gap-2">
                            <span className="text-amber-500">⏳</span>
                            <p className="text-sm text-amber-700">
                              Waiting for doctor response. You will be notified when available.
                            </p>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="flex flex-wrap gap-2 pt-2">
                          {canChat && (
                            <button
                              onClick={() => setChatConsultation(c)}
                              className="px-3 py-1.5 bg-primary-600 text-white text-xs font-semibold rounded hover:bg-primary-700 transition-colors"
                            >
                              💬 Message Doctor
                            </button>
                          )}
                          <button
                            onClick={() => handleViewHistory(c.id)}
                            className="px-3 py-1.5 bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded hover:bg-slate-50 transition-colors"
                          >
                            View Full History
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Prediction History */}
        <div>
          <h2 className="text-lg font-bold text-slate-800 mb-4">Prediction History</h2>
          {predictions.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
              <p className="text-slate-500 text-sm">No predictions yet.</p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-left px-4 py-3 font-semibold text-slate-600">Date</th>
                      <th className="text-left px-4 py-3 font-semibold text-slate-600">Symptoms</th>
                      <th className="text-left px-4 py-3 font-semibold text-slate-600">Predicted</th>
                      <th className="text-left px-4 py-3 font-semibold text-slate-600">Confidence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {predictions.map((p) => (
                      <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="px-4 py-3 text-slate-600 whitespace-nowrap">
                          {new Date(p.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-4 py-3 text-slate-700 max-w-xs truncate">{p.symptoms_text}</td>
                        <td className="px-4 py-3 font-medium text-slate-800">{p.predicted_condition || "N/A"}</td>
                        <td className="px-4 py-3">
                          {p.confidence_score ? (
                            <span
                              className={`font-bold ${
                                p.confidence_score >= 0.7
                                  ? "text-emerald-600"
                                  : p.confidence_score >= 0.4
                                  ? "text-amber-600"
                                  : "text-red-600"
                              }`}
                            >
                              {(p.confidence_score * 100).toFixed(1)}%
                            </span>
                          ) : (
                            "N/A"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
