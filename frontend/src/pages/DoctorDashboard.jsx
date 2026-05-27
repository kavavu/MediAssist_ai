import React, { useEffect, useState, useCallback, useRef } from "react";
import {
  getDoctorConsultations,
  respondToConsultation,
  editResponse,
  resolveConsultation,
  sendFollowUp,
  getDoctorStats,
  getAiResponse,
  getAiFullResponse,
  getConsultationHistory,
} from "../services/consultation.js";
import { getSocket, joinConsultationRoom, leaveConsultationRoom, joinDoctorRoom, leaveDoctorRoom } from "../services/socket.js";
import { getConsultationFiles } from "../services/upload.js";
import SocketStatusBadge from "../components/SocketStatusBadge.jsx";
import FileUploadZone from "../components/FileUploadZone.jsx";
import { useToast } from "../components/ToastProvider.jsx";
import { SkeletonStats, SkeletonCard } from "../components/Skeleton.jsx";
import EmptyState from "../components/EmptyState.jsx";

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
    <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${colors[level] || colors.LOW}`}>
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
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
};

const SymptomChip = ({ label }) => (
  <span className="inline-block bg-slate-100 text-slate-700 text-xs font-medium px-2.5 py-1 rounded-md border border-slate-200 mr-1.5 mb-1.5">
    {label}
  </span>
);

const StatCard = ({ title, value, color }) => (
  <div className={`bg-white rounded-xl p-4 border-l-4 ${color} shadow-sm`}>
    <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">{title}</p>
    <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
  </div>
);

const SectionTitle = ({ children, className = "" }) => (
  <h3 className={`text-sm font-bold text-slate-400 uppercase tracking-wider mb-2 ${className}`}>{children}</h3>
);

const InfoBox = ({ children, className = "" }) => (
  <div className={`bg-slate-50 rounded-lg p-3 text-sm text-slate-700 border border-slate-100 ${className}`}>
    {children}
  </div>
);

const DoctorBadge = ({ name, specialization, isAvailable, currentLoad, isVerified }) => (
  <div className="flex items-center gap-2">
    <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center text-xs font-bold">
      {name?.charAt(0) || "D"}
    </div>
    <div className="leading-tight">
      <p className="text-xs font-semibold text-slate-700">Dr. {name}</p>
      <p className="text-[10px] text-slate-500">{specialization || "General Practitioner"}</p>
    </div>
    {typeof isAvailable !== "undefined" && (
      <span className={isAvailable ? "text-[10px] text-green-600" : "text-[10px] text-red-600"}>
        {isAvailable ? "🟢" : "🔴"}
      </span>
    )}
    {typeof currentLoad !== "undefined" && (
      <span className="text-[10px] text-slate-400">Load: {currentLoad}</span>
    )}
    {isVerified ? (
      <span className="ml-1 text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 font-medium">
        ✅ Verified
      </span>
    ) : (
      <span className="ml-1 text-[10px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded border border-amber-100 font-medium">
        ⏳ Pending Verification
      </span>
    )}
  </div>
);

/* ------------------------------------------------------------------ */
/* Toast Notification                                                 */
/* ------------------------------------------------------------------ */

const Toast = ({ message, onClose }) => {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);
  return (
    <div className="fixed top-4 right-4 z-50 bg-primary-700 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 animate-bounce">
      <span className="text-lg">🔔</span>
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
};

/* ------------------------------------------------------------------ */
/* Chat Panel (inline in right panel)                                 */
/* ------------------------------------------------------------------ */

const QUICK_REPLIES = [
  "Thank you for the update.",
  "Please take your medication as prescribed.",
  "Let me know if symptoms worsen.",
  "Schedule a follow-up in 3 days.",
  "Rest and stay hydrated.",
];

const ChatPanel = ({ consultation }) => {
  const toast = useToast();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showQuickReplies, setShowQuickReplies] = useState(false);
  const messagesEndRef = useRef(null);
  const fetchHistory = useCallback(async () => {
    try {
      const res = await getConsultationHistory(consultation.id);
      const history = res.data.history || [];
      const chatMessages = history
        .filter((h) => h.type === "followup")
        .map((h) => ({
          id: h.data?.message_id || h.timestamp || `${h.data?.sender_role}-${h.timestamp}`,
          sender: h.data?.sender_role,
          senderName: h.data?.sender_name,
          text: h.data?.message,
          timestamp: h.timestamp_relative,
          fullTimestamp: h.timestamp,
        }));
      setMessages(chatMessages);
    } catch {
      // silently fail; user can retry by reopening chat
    } finally {
      setLoading(false);
    }
  }, [consultation.id]);

  useEffect(() => {
    fetchHistory();

    // Join consultation room for real-time messages
    joinConsultationRoom(consultation.id);

    // Set up socket listener for new messages
    const socket = getSocket();
    if (!socket) return;

    const handleNewMessage = (data) => {
      try {
        if (!data || !data.message) return;
        if (data.consultation_id !== consultation.id) return;

        const msg = data.message;
        // Validate required fields
        if (!msg.id || !msg.sender_role || !msg.message) return;

        setMessages((prev) => {
          // Prevent duplicates: check by unique message id
          if (prev.some((m) => m.id === msg.id)) return prev;
          return [
            ...prev,
            {
              id: msg.id,
              sender: msg.sender_role,
              senderName: msg.sender_name || "Unknown",
              text: msg.message,
              timestamp: "just now",
              fullTimestamp: msg.created_at || new Date().toISOString(),
            },
          ];
        });
      } catch {
        // ignore socket handling errors
      }
    };

    socket.on("new_message", handleNewMessage);

    return () => {
      try {
        socket.off("new_message", handleNewMessage);
        leaveConsultationRoom(consultation.id);
      } catch {
        // ignore cleanup errors
      }
    };
  }, [fetchHistory, consultation.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text) => {
    const messageToSend = text || newMessage;
    if (!messageToSend.trim()) return;
    setSending(true);
    try {
      await sendFollowUp(consultation.id, {
        message: messageToSend.trim(),
        sender_role: "doctor",
      });
      setNewMessage("");
      setShowQuickReplies(false);
      // Don't fetch history — the socket will push the new message
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const formatFullTime = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  };

  return (
    <div className="border border-slate-200 rounded-xl bg-white overflow-hidden mt-4">
      <div className="bg-slate-50 px-4 py-2 border-b border-slate-100 flex items-center gap-2">
        <span className="text-sm">💬</span>
        <h4 className="text-sm font-bold text-slate-700">Chat with Patient</h4>
        <span className="text-xs text-slate-400 ml-auto">Auto-refreshing</span>
      </div>
      <div className="h-56 overflow-y-auto p-3 space-y-2">
        {loading && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600" />
          </div>
        )}
        {!loading && messages.length === 0 && (
          <p className="text-xs text-slate-400 text-center py-4">No messages yet. Start the conversation.</p>
        )}
        {messages.map((msg, idx) => {
          const isDoctor = msg.sender === "doctor";
          const showDate = idx === 0 || (
            messages[idx - 1] &&
            new Date(msg.fullTimestamp).toDateString() !== new Date(messages[idx - 1].fullTimestamp).toDateString()
          );
          return (
            <div key={msg.id || `${msg.sender}-${msg.fullTimestamp}`}>
              {showDate && (
                <div className="flex justify-center my-2">
                  <span className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full">
                    {formatFullTime(msg.fullTimestamp).split(",")[0]}
                  </span>
                </div>
              )}
              <div className={`flex ${isDoctor ? "justify-end" : "justify-start"}`}>
                <div
                  className={`max-w-[85%] rounded-lg px-3 py-1.5 text-xs ${
                    isDoctor
                      ? "bg-primary-600 text-white rounded-br-none"
                      : "bg-slate-100 text-slate-700 border border-slate-200 rounded-bl-none"
                  }`}
                >
                  <p className="text-[10px] opacity-70 mb-0.5">{msg.senderName}</p>
                  <p>{msg.text}</p>
                  <p className={`text-[9px] mt-0.5 ${isDoctor ? "text-primary-200" : "text-slate-400"}`}>
                    {formatFullTime(msg.fullTimestamp)}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Replies */}
      {showQuickReplies && (
        <div className="border-t border-slate-100 px-3 py-2 bg-slate-50">
          <p className="text-[10px] text-slate-500 mb-1.5 font-medium uppercase tracking-wide">Quick Replies</p>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_REPLIES.map((reply) => (
              <button
                key={reply}
                onClick={() => handleSend(reply)}
                disabled={sending}
                className="text-[11px] bg-white border border-slate-200 text-slate-600 px-2.5 py-1 rounded-full hover:bg-primary-50 hover:border-primary-200 hover:text-primary-700 transition-colors"
              >
                {reply}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="border-t border-slate-100 p-2 flex gap-2">
        <button
          onClick={() => setShowQuickReplies(!showQuickReplies)}
          className="px-2 text-slate-400 hover:text-primary-600 transition-colors"
          title="Quick replies"
        >
          ⚡
        </button>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a message..."
          className="flex-1 px-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          onClick={() => handleSend()}
          disabled={sending || !newMessage.trim()}
          className="px-3 bg-primary-600 text-white text-xs font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          {sending ? "..." : "Send"}
        </button>
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

export default function DoctorDashboard() {
  const [consultations, setConsultations] = useState([]);
  const [filtered, setFiltered] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [stats, setStats] = useState({});
  const [toast, setToast] = useState(null);
  const [newCount, setNewCount] = useState(0);

  /* Response form state */
  const [acknowledgement, setAcknowledgement] = useState("");
  const [advice, setAdvice] = useState("");
  const [tests, setTests] = useState("");
  const [urgency, setUrgency] = useState("");
  const [submitting, setSubmitting] = useState(false);

  /* AI Full Response state */
  const [aiFullResponse, setAiFullResponse] = useState("");
  const [aiFullResponseLoading, setAiFullResponseLoading] = useState(false);
  const [aiFullResponseSource, setAiFullResponseSource] = useState("");
  const [showAiDraft, setShowAiDraft] = useState(false);

  /* Editing mode */
  const [isEditing, setIsEditing] = useState(false);

  /* History */
  const [history, setHistory] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  /* Chat visibility */
  const [showChat, setShowChat] = useState(false);

  const prevCountRef = useRef(0);
  const selected = consultations.find((c) => c.id === selectedId);

  // Load files when selected patient changes
  useEffect(() => {
    if (!selected) return;
    if (selected.files) return; // already loaded
    getConsultationFiles(selected.id)
      .then((files) => {
        setConsultations((prev) =>
          prev.map((c) => (c.id === selected.id ? { ...c, files } : c))
        );
      })
      .catch(() => {});
  }, [selectedId]);

  const fetchData = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [cRes, sRes] = await Promise.all([
        getDoctorConsultations(),
        getDoctorStats(),
      ]);
      const newConsultations = cRes.data.consultations || [];

      if (silent && newConsultations.length > prevCountRef.current && prevCountRef.current > 0) {
        const diff = newConsultations.length - prevCountRef.current;
        setToast(`${diff} new patient case${diff > 1 ? "s" : ""} received`);
        setNewCount(diff);
        setTimeout(() => setNewCount(0), 5000);
      }
      prevCountRef.current = newConsultations.length;

      setConsultations(newConsultations);
      setStats(sRes.data.stats || {});
      setError("");
    } catch (err) {
      if (!silent) setError("Failed to load consultations.");
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  /* Real-time socket listeners (replaces polling) */
  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    // Get current user from localStorage to join doctor room
    const userStr = window.localStorage.getItem("current_user");
    let doctorId = null;
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user.role === "doctor") {
          doctorId = user.id;
          joinDoctorRoom(user.id);
        }
      } catch {
        // ignore parse error
      }
    }

    const handleNewConsultation = (data) => {
      try {
        if (!data || !data.consultation) return;
        const newConsultation = data.consultation;
        // Validate required fields
        if (!newConsultation.id) return;

        setConsultations((prev) => {
          // Prevent duplicates: check by unique consultation id
          if (prev.some((c) => c.id === newConsultation.id)) return prev;
          const updated = [newConsultation, ...prev];
          // Show toast notification
          const diff = updated.length - prev.length;
          if (diff > 0) {
            setToast(`${diff} new patient case${diff > 1 ? "s" : ""} received`);
            setNewCount(diff);
            setTimeout(() => setNewCount(0), 5000);
          }
          return updated;
        });
      } catch {
        // ignore socket handling errors
      }
    };

    const handleConsultationUpdated = (data) => {
      try {
        if (!data || !data.consultation_id || !data.data) return;

        setConsultations((prev) =>
          prev.map((c) =>
            c.id === data.consultation_id ? { ...c, ...data.data } : c
          )
        );
      } catch {
        // ignore socket handling errors
      }
    };

    socket.on("new_consultation", handleNewConsultation);
    socket.on("consultation_updated", handleConsultationUpdated);

    return () => {
      try {
        socket.off("new_consultation", handleNewConsultation);
        socket.off("consultation_updated", handleConsultationUpdated);
        if (doctorId) {
          try {
            leaveDoctorRoom(doctorId);
          } catch {
            // ignore
          }
        }
      } catch {
        // ignore cleanup errors
      }
    };
  }, []);

  /* Filter + Search */
  useEffect(() => {
    let data = [...consultations];
    if (filterStatus !== "all") {
      if (filterStatus === "high") {
        data = data.filter((c) => c.priority === "HIGH");
      } else {
        data = data.filter((c) => c.status === filterStatus);
      }
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      data = data.filter(
        (c) =>
          (c.patient_name || "").toLowerCase().includes(q) ||
          (c.predicted_condition || "").toLowerCase().includes(q)
      );
    }
    setFiltered(data);
    // Only auto-select first item if nothing is selected AND we have data
    if (data.length > 0 && !selectedId) {
      setSelectedId(data[0].id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [consultations, filterStatus, search]);

  /* Reset form when selection changes */
  useEffect(() => {
    if (selected) {
      setAcknowledgement(selected.response_acknowledgement || "");
      setAdvice(selected.response_advice || "");
      setTests(selected.response_tests || "");
      setUrgency(selected.response_urgency || "");
      setIsEditing(false);
      setShowChat(false);
    }
  }, [selectedId]);

  const handleRespond = async () => {
    if (!selected) return;
    setSubmitting(true);
    try {
      await respondToConsultation(selected.id, {
        acknowledgement: acknowledgement.trim() || undefined,
        advice: advice.trim() || undefined,
        tests: tests.trim() || undefined,
        urgency: urgency.trim() || undefined,
      });
      await fetchData();
      setToast("Response submitted successfully");
      setIsEditing(false);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to submit");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEditSave = async () => {
    if (!selected) return;
    setSubmitting(true);
    try {
      await editResponse(selected.id, {
        acknowledgement: acknowledgement.trim() || undefined,
        advice: advice.trim() || undefined,
        tests: tests.trim() || undefined,
        urgency: urgency.trim() || undefined,
      });
      await fetchData();
      setToast("Response updated successfully");
      setIsEditing(false);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to update");
    } finally {
      setSubmitting(false);
    }
  };

  const handleResolve = async () => {
    if (!selected) return;
    try {
      await resolveConsultation(selected.id);
      await fetchData();
      setToast("Case marked as resolved");
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to resolve");
    }
  };

  const handleAiAssist = async (type) => {
    if (!selected) return;
    try {
      const res = await getAiResponse(selected.id);
      const s = res.data.suggestions;
      if (type === "full") {
        setAcknowledgement(s.acknowledgement);
        setAdvice(s.advice);
        setTests(s.tests);
        setUrgency(s.urgency);
      } else if (type === "tests") {
        setTests(s.tests);
      } else if (type === "urgency") {
        setUrgency(s.urgency);
      }
    } catch (err) {
      const msg = err?.response?.data?.error || err?.message || "AI assist failed";
      toast.error(msg);
    }
  };

  const handleAiFullResponse = async () => {
    if (!selected) return;
    setAiFullResponseLoading(true);
    setShowAiDraft(true);
    try {
      const res = await getAiFullResponse(selected.id);
      const data = res.data;
      setAiFullResponse(data.response || "");
      setAiFullResponseSource(data.source || "fallback");
      // Also populate structured fields for editing
      if (data.structured) {
        setAcknowledgement(data.structured.acknowledgement || "");
        setAdvice(data.structured.advice || "");
        setTests(data.structured.tests || "");
        setUrgency(data.structured.urgency || "");
      }
    } catch (err) {
      const msg = err?.response?.data?.error || err?.message || "AI response generation failed";
      toast.error(msg);
      setShowAiDraft(false);
    } finally {
      setAiFullResponseLoading(false);
    }
  };

  const handleApplyAiDraft = () => {
    // Extract sections from the full response and populate fields
    const draft = aiFullResponse;
    // Simple heuristic: split by common section headers
    const lines = draft.split("\n");
    let currentSection = "";
    let ack = [], adv = [], tst = [], urg = [], flw = [];
    
    for (const line of lines) {
      const lower = line.toLowerCase();
      if (lower.includes("acknowledg")) { currentSection = "ack"; continue; }
      if (lower.includes("clinical interpretation")) { currentSection = "adv"; continue; }
      if (lower.includes("care recommendation")) { currentSection = "adv"; continue; }
      if (lower.includes("recommended test")) { currentSection = "tst"; continue; }
      if (lower.includes("urgency")) { currentSection = "urg"; continue; }
      if (lower.includes("follow-up")) { currentSection = "flw"; continue; }
      if (lower.includes("this assessment is ai-assisted")) continue;
      if (line.trim().startsWith("---")) continue;
      if (line.trim().startsWith("*")) continue;
      
      if (currentSection === "ack" && line.trim()) ack.push(line.trim());
      if (currentSection === "adv" && line.trim()) adv.push(line.trim());
      if (currentSection === "tst" && line.trim()) tst.push(line.trim());
      if (currentSection === "urg" && line.trim()) urg.push(line.trim());
      if (currentSection === "flw" && line.trim()) flw.push(line.trim());
    }
    
    if (ack.length) setAcknowledgement(ack.join(" "));
    if (adv.length) setAdvice(adv.join(" "));
    if (tst.length) setTests(tst.join("\n"));
    if (urg.length) setUrgency(urg.join(" "));
    
    setShowAiDraft(false);
    setIsEditing(true);
    toast.success("AI draft applied. Review and edit before sending.");
  };

  const handleViewHistory = async () => {
    if (!selected) return;
    try {
      const res = await getConsultationHistory(selected.id);
      setHistory(res.data.history || []);
      setShowHistory(true);
    } catch (err) {
      toast.error(err.response?.data?.error || "Failed to load history");
    }
  };

  const getSeverityTint = (priority) => {
    if (priority === "HIGH") return "bg-red-50/60 border-red-100";
    if (priority === "MEDIUM") return "bg-amber-50/60 border-amber-100";
    return "bg-emerald-50/60 border-emerald-100";
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

  const canEdit = selected && (selected.status === "responded" || selected.status === "resolved");

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          <SkeletonStats count={4} />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1"><SkeletonCard count={3} /></div>
            <div className="lg:col-span-2"><SkeletonCard count={2} /></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) return <p className="text-red-500 p-6">{error}</p>;

  return (
    <div className="min-h-screen bg-slate-50">
      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
      {showHistory && <HistoryModal history={history} onClose={() => setShowHistory(false)} />}

      {/* Analytics Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-xl font-bold text-slate-800">Doctor Dashboard</h1>
              <p className="text-sm text-slate-500 mt-0.5">Manage patient consultations and responses</p>
            </div>
            <SocketStatusBadge />
            {newCount > 0 && (
              <span className="bg-red-500 text-white text-xs font-bold px-3 py-1 rounded-full animate-pulse">
                {newCount} NEW
              </span>
            )}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatCard title="Patients Today" value={stats.total_patients_today || 0} color="border-primary-500" />
            <StatCard title="Pending" value={stats.pending_cases || 0} color="border-amber-500" />
            <StatCard title="High Severity" value={stats.high_severity_cases || 0} color="border-red-500" />
            <StatCard title="Avg Response" value={`${stats.average_response_minutes || 0}m`} color="border-emerald-500" />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-4">
        {/* Disclaimer */}
        <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-2 mb-4 flex items-center gap-2">
          <span className="text-blue-500 text-sm">ℹ️</span>
          <p className="text-xs text-blue-700">
            AI-assisted predictions. Not a final medical diagnosis. Always verify clinically.
          </p>
        </div>

        <div className="flex gap-4 h-[calc(100vh-280px)] min-h-[500px]">
          {/* LEFT PANEL - Patient List */}
          <div className="w-[32%] bg-white rounded-xl border border-slate-200 flex flex-col overflow-hidden shadow-sm">
            {/* Search & Filters */}
            <div className="p-3 border-b border-slate-100 space-y-2">
              <input
                type="text"
                placeholder="Search by name or condition..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
              <div className="flex gap-1 flex-wrap">
                {["all", "pending", "responded", "high"].map((f) => (
                  <button
                    key={f}
                    onClick={() => setFilterStatus(f)}
                    className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                      filterStatus === f
                        ? "bg-primary-600 text-white"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                    }`}
                  >
                    {f === "high" ? "High Priority" : f.charAt(0).toUpperCase() + f.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto">
              {filtered.length === 0 ? (
                <EmptyState
                  icon="inbox"
                  title="No patients in queue"
                  description="New patient consultations will appear here when assigned to you."
                />
              ) : (
                filtered.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => setSelectedId(c.id)}
                    className={`w-full text-left p-3 border-b border-slate-50 transition-all hover:bg-slate-50 ${
                      selectedId === c.id ? "ring-2 ring-primary-500 ring-inset bg-primary-50/30" : ""
                    } ${getSeverityTint(c.priority)}`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-slate-800 truncate">{c.patient_name}</p>
                        <p className="text-xs text-slate-500 truncate mt-0.5">{c.predicted_condition || "N/A"}</p>
                      </div>
                      <SeverityBadge level={c.priority} />
                    </div>
                    <div className="flex items-center justify-between mt-2">
                      <StatusBadge status={c.status} />
                      <span className="text-xs text-slate-400">{c.created_at_relative}</span>
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* RIGHT PANEL - Patient Details */}
          <div className="flex-1 bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm flex flex-col max-h-[calc(100vh-180px)]">
            {!selected ? (
              <div className="flex items-center justify-center h-full text-slate-400 text-sm">
                Select a patient to view details
              </div>
            ) : (
              <div className="p-5 space-y-5 overflow-y-auto flex-1">
                {/* HEADER */}
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800">{selected.patient_name}</h2>
                    <p className="text-xs text-slate-500 mt-0.5">{selected.patient_email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <SeverityBadge level={selected.priority} />
                    <StatusBadge status={selected.status} />
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span>📅 {formatTimestamp(selected.created_at)}</span>
                  <DoctorBadge name={selected.doctor_name} specialization={selected.doctor_specialization} isAvailable={selected.doctor_is_available} currentLoad={selected.doctor_current_load} isVerified={selected.doctor_is_verified} />
                </div>

                {/* CONDITION BLOCK */}
                <div className="bg-primary-50 rounded-xl p-4 border border-primary-100">
                  <SectionTitle>Predicted Condition</SectionTitle>
                  <p className="text-lg font-bold text-primary-800">{selected.predicted_condition || "N/A"}</p>
                  {selected.confidence_score && (
                    <p className="text-sm text-primary-600 mt-1">
                      Confidence: <span className="font-bold">{(selected.confidence_score * 100).toFixed(1)}%</span>
                    </p>
                  )}
                </div>

                {/* SYMPTOMS */}
                <div>
                  <SectionTitle>Symptoms</SectionTitle>
                  <div className="flex flex-wrap">
                    {(selected.symptoms_clean || selected.symptoms)
                      .split(",")
                      .map((s) => s.trim())
                      .filter(Boolean)
                      .map((s) => (
                        <SymptomChip key={s} label={s} />
                      ))}
                  </div>
                </div>

                {/* PATIENT MESSAGE */}
                {selected.message && (
                  <div>
                    <SectionTitle>Patient Message</SectionTitle>
                    <InfoBox className="italic">{selected.message}</InfoBox>
                  </div>
                )}

                {/* AI INSIGHT */}
                <div className="bg-indigo-50 rounded-xl p-4 border border-indigo-100">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-indigo-500">🤖</span>
                    <SectionTitle className="!mb-0">AI Clinical Insight</SectionTitle>
                  </div>
                  <p className="text-sm text-indigo-800 mb-2">{selected.ai_insight}</p>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-indigo-600">
                      Risk: <span className="font-bold">{selected.ai_risk_level}</span>
                    </span>
                  </div>
                  <p className="text-xs text-indigo-600 mt-2">{selected.ai_suggested_steps}</p>
                </div>

                {/* DOCTOR RESPONSE */}
                <div className="border-t border-slate-200 pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <SectionTitle className="!mb-0">Doctor Response</SectionTitle>
                    <div className="flex gap-1.5">
                      <button
                        onClick={handleAiFullResponse}
                        disabled={aiFullResponseLoading}
                        className="text-xs bg-gradient-to-r from-indigo-100 to-violet-100 text-indigo-700 px-2.5 py-1 rounded-md font-medium hover:from-indigo-200 hover:to-violet-200 transition-colors disabled:opacity-50"
                      >
                        {aiFullResponseLoading ? (
                          <span className="flex items-center gap-1">
                            <span className="animate-spin rounded-full h-3 w-3 border-b-2 border-indigo-600" />
                            Drafting…
                          </span>
                        ) : (
                          <span>🤖 AI Draft Response</span>
                        )}
                      </button>
                      <button
                        onClick={() => handleAiAssist("full")}
                        className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium hover:bg-slate-200 transition-colors"
                      >
                        📝 Structured
                      </button>
                      <button
                        onClick={() => handleAiAssist("tests")}
                        className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium hover:bg-slate-200 transition-colors"
                      >
                        🧪 Tests
                      </button>
                      <button
                        onClick={() => handleAiAssist("urgency")}
                        className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md font-medium hover:bg-slate-200 transition-colors"
                      >
                        ⚡ Urgency
                      </button>
                    </div>
                  </div>

                  {/* AI Full Response Draft Panel */}
                  {showAiDraft && (
                    <div className="mb-4 bg-gradient-to-br from-indigo-50 to-violet-50 rounded-xl border border-indigo-200 p-4 animate-fade-in-up">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-indigo-600">
                            <svg className="w-4 h-4 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                            </svg>
                          </span>
                          <span className="text-xs font-bold text-indigo-700">AI-Assisted Draft</span>
                          {aiFullResponseSource && (
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full border font-medium ${
                              aiFullResponseSource === "openai"
                                ? "bg-emerald-50 text-emerald-600 border-emerald-200"
                                : "bg-amber-50 text-amber-600 border-amber-200"
                            }`}>
                              {aiFullResponseSource === "openai" ? "OpenAI" : "Fallback"}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-1.5">
                          <button
                            onClick={() => setShowAiDraft(false)}
                            className="text-[10px] text-slate-500 hover:text-slate-700 px-2 py-1 rounded hover:bg-slate-100 transition-colors"
                          >
                            Hide
                          </button>
                        </div>
                      </div>
                      {aiFullResponseLoading ? (
                        <div className="space-y-2">
                          <div className="h-3 bg-indigo-100 rounded animate-shimmer w-full" />
                          <div className="h-3 bg-indigo-100 rounded animate-shimmer w-5/6" />
                          <div className="h-3 bg-indigo-100 rounded animate-shimmer w-4/5" />
                          <div className="h-3 bg-indigo-100 rounded animate-shimmer w-3/4" />
                          <div className="flex items-center gap-1.5 mt-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 typing-dot" />
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 typing-dot" />
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 typing-dot" />
                            <span className="text-[10px] text-indigo-500 ml-1">Generating professional response…</span>
                          </div>
                        </div>
                      ) : (
                        <>
                          <div className="bg-white/70 rounded-lg border border-indigo-100 p-3 max-h-64 overflow-y-auto">
                            <pre className="text-xs text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
                              {aiFullResponse}
                            </pre>
                          </div>
                          <div className="flex gap-2 mt-3">
                            <button
                              onClick={handleApplyAiDraft}
                              className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-md font-medium hover:bg-indigo-700 transition-colors"
                            >
                              ✓ Apply to Response Fields
                            </button>
                            <button
                              onClick={handleAiFullResponse}
                              className="text-xs bg-white border border-indigo-200 text-indigo-700 px-3 py-1.5 rounded-md font-medium hover:bg-indigo-50 transition-colors"
                            >
                              🔄 Regenerate
                            </button>
                            <button
                              onClick={() => { setShowAiDraft(false); setAiFullResponse(""); }}
                              className="text-xs bg-white border border-slate-200 text-slate-600 px-3 py-1.5 rounded-md font-medium hover:bg-slate-50 transition-colors"
                            >
                              Dismiss
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  )}

                  {canEdit && !isEditing ? (
                    <div className="space-y-3">
                      {selected.response_acknowledgement && (
                          <div>
                            <p className="text-xs font-semibold text-slate-500 mb-1">Acknowledgement</p>
                            <InfoBox>{selected.response_acknowledgement}</InfoBox>
                          </div>
                        )}
                        {selected.response_advice && (
                          <div>
                            <p className="text-xs font-semibold text-slate-500 mb-1">Advice</p>
                            <InfoBox className="bg-emerald-50 border-emerald-100 text-emerald-800">
                              {selected.response_advice}
                            </InfoBox>
                          </div>
                        )}
                        {selected.response_tests && (
                          <div>
                            <p className="text-xs font-semibold text-slate-500 mb-1">Recommended Tests</p>
                            <InfoBox className="bg-blue-50 border-blue-100">
                              <pre className="whitespace-pre-wrap font-sans text-sm">{selected.response_tests}</pre>
                            </InfoBox>
                          </div>
                        )}
                        {selected.response_urgency && (
                          <div>
                            <p className="text-xs font-semibold text-slate-500 mb-1">Urgency</p>
                            <InfoBox className={`${selected.priority === "HIGH" ? "bg-red-50 border-red-100 text-red-800" : "bg-amber-50 border-amber-100 text-amber-800"}`}>
                              {selected.response_urgency}
                            </InfoBox>
                          </div>
                        )}
                        {selected.responded_at_relative && (
                          <p className="text-xs text-slate-400">Responded {selected.responded_at_relative}</p>
                        )}

                      {/* Action Buttons */}
                      <div className="flex flex-wrap gap-2 pt-2">
                        <button
                          onClick={() => setIsEditing(true)}
                          className="px-4 bg-slate-700 text-white text-sm font-semibold py-2 rounded-lg hover:bg-slate-800 transition-colors"
                        >
                          Edit Response
                        </button>
                        <button
                          onClick={() => setShowChat(!showChat)}
                          className={`px-4 text-sm font-semibold py-2 rounded-lg transition-colors ${
                            showChat ? "bg-primary-700 text-white" : "bg-primary-600 text-white hover:bg-primary-700"
                          }`}
                        >
                          {showChat ? "Hide Chat" : "💬 Open Chat"}
                        </button>
                        <button
                          onClick={handleViewHistory}
                          className="px-4 bg-white border border-slate-200 text-slate-700 text-sm font-semibold py-2 rounded-lg hover:bg-slate-50 transition-colors"
                        >
                          View History
                        </button>
                        {selected.status !== "resolved" && (
                          <button
                            onClick={handleResolve}
                            className="px-4 bg-emerald-600 text-white text-sm font-semibold py-2 rounded-lg hover:bg-emerald-700 transition-colors"
                          >
                            Mark Resolved
                          </button>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs font-semibold text-slate-500 block mb-1">Acknowledgement</label>
                        <textarea
                          rows={2}
                          value={acknowledgement}
                          onChange={(e) => setAcknowledgement(e.target.value)}
                          placeholder="Acknowledge the patient's symptoms..."
                          className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-500 block mb-1">Advice</label>
                        <textarea
                          rows={2}
                          value={advice}
                          onChange={(e) => setAdvice(e.target.value)}
                          placeholder="Provide medical advice..."
                          className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-500 block mb-1">Recommended Tests</label>
                        <textarea
                          rows={3}
                          value={tests}
                          onChange={(e) => setTests(e.target.value)}
                          placeholder="List recommended tests..."
                          className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y font-mono"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-slate-500 block mb-1">Urgency</label>
                        <textarea
                          rows={2}
                          value={urgency}
                          onChange={(e) => setUrgency(e.target.value)}
                          placeholder="Specify urgency level..."
                          className="w-full text-sm px-3 py-2 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-y"
                        />
                      </div>

                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={isEditing ? handleEditSave : handleRespond}
                          disabled={submitting}
                          className="flex-1 bg-primary-600 text-white text-sm font-semibold py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                          {submitting ? "Saving..." : isEditing ? "Save Changes" : "Submit Response"}
                        </button>
                        {isEditing && (
                          <button
                            onClick={() => {
                              setIsEditing(false);
                              setAcknowledgement(selected.response_acknowledgement || "");
                              setAdvice(selected.response_advice || "");
                              setTests(selected.response_tests || "");
                              setUrgency(selected.response_urgency || "");
                            }}
                            className="px-4 bg-white border border-slate-200 text-slate-700 text-sm font-semibold py-2.5 rounded-lg hover:bg-slate-50 transition-colors"
                          >
                            Cancel
                          </button>
                        )}
                        {!isEditing && (
                          <button
                            onClick={handleResolve}
                            className="px-4 bg-emerald-600 text-white text-sm font-semibold py-2.5 rounded-lg hover:bg-emerald-700 transition-colors"
                          >
                            Mark Resolved
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* File Attachments */}
                  <div className="pt-4 border-t border-slate-100">
                    <SectionTitle>Patient Attachments</SectionTitle>
                    <FileUploadZone
                      consultationId={selected.id}
                      files={selected.files || []}
                      onChange={(files) => {
                        setSelected((s) => (s ? { ...s, files } : s));
                      }}
                      readOnly
                    />
                  </div>

                  {/* Inline Chat Panel */}
                  {showChat && <ChatPanel consultation={selected} />}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
