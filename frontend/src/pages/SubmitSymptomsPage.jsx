/**
 * SubmitSymptomsPage.jsx
 *
 * A premium clinical AI symptom checker interface.
 * Designed for academic presentation and healthcare demos.
 * Focuses on trust, clarity, and clinical realism.
 */
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  createConsultation,
  getDoctorsPreview,
  getRecommendedDoctor,
  getDoctorPublicStats,
} from "../services/consultation.js";
import { predictSymptoms } from "../services/symptoms.js";
import { getDoctorRatingSummary } from "../services/review.js";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BrainCircuit,
  ChevronDown,
  ChevronUp,
  Clock,
  FlaskConical,
  HeartPulse,
  Info,
  Microscope,
  ScanLine,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  TestTube,
  Thermometer,
  UserCheck,
  X,
} from "lucide-react";

/* ─── Common symptom chips (English + Swahili) ─── */
const COMMON_SYMPTOMS = [
  "Fever",
  "Headache",
  "Chills",
  "Vomiting",
  "Chest Pain",
  "Cough",
  "Fatigue",
  "Body Aches",
  "Nausea",
  "Diarrhea",
  "Shortness of Breath",
  "Rash",
];

const SWAHILI_SYMPTOMS = [
  { sw: "Homa", en: "Fever" },
  { sw: "Kichwa kuumwa", en: "Headache" },
  { sw: "Baridi kali", en: "Chills" },
  { sw: "Kutapika", en: "Vomiting" },
  { sw: "Kifua kuumwa", en: "Chest Pain" },
  { sw: "Kikohozi", en: "Cough" },
  { sw: "Uchovu", en: "Fatigue" },
  { sw: "Maumivu ya mwili", en: "Body Aches" },
  { sw: "Kichefuchefu", en: "Nausea" },
  { sw: "Tumbo kuhara", en: "Diarrhea" },
  { sw: "Pumzi kukata", en: "Shortness of Breath" },
  { sw: "Madoa ya ngozi", en: "Rash" },
  { sw: "Kukojoa uchungu", en: "Burning Urination" },
  { sw: "Kukojoa mara nyingi", en: "Frequent Urination" },
  { sw: "Shingo ngumu", en: "Stiff Neck" },
  { sw: "Kunywa maji sana", en: "Excessive Thirst" },
  { sw: "Kiharusi", en: "Seizure" },
  { sw: "Jicho kuharibika", en: "Blurred Vision" },
  { sw: "Moyo kupiga kasi", en: "Palpitations" },
  { sw: "Kupoteza uzito", en: "Weight Loss" },
];

/* ─── Severity config ─── */
const SEVERITY_CONFIG = {
  HIGH: {
    label: "High Severity",
    colorClass: "text-urgent-700",
    bgClass: "bg-urgent-50",
    borderClass: "border-urgent-200",
    badgeBg: "bg-urgent-100",
    badgeText: "text-urgent-700",
    badgeBorder: "border-urgent-200",
    barColor: "bg-urgent-500",
    icon: ShieldAlert,
    urgencyWord: "Urgent",
  },
  MEDIUM: {
    label: "Moderate Severity",
    colorClass: "text-caution-700",
    bgClass: "bg-caution-50",
    borderClass: "border-caution-200",
    badgeBg: "bg-caution-100",
    badgeText: "text-caution-700",
    badgeBorder: "border-caution-200",
    barColor: "bg-caution-500",
    icon: AlertTriangle,
    urgencyWord: "Caution",
  },
  LOW: {
    label: "Low Severity",
    colorClass: "text-success-700",
    bgClass: "bg-success-50",
    borderClass: "border-success-200",
    badgeBg: "bg-success-100",
    badgeText: "text-success-700",
    badgeBorder: "border-success-200",
    barColor: "bg-success-500",
    icon: UserCheck,
    urgencyWord: "Mild",
  },
};

/* ─── Match quality config ─── */
const MATCH_CONFIG = {
  "High Match": {
    badgeBg: "bg-success-100",
    badgeText: "text-success-700",
    badgeBorder: "border-success-200",
  },
  "Moderate Match": {
    badgeBg: "bg-caution-100",
    badgeText: "text-caution-700",
    badgeBorder: "border-caution-200",
  },
  "Low Match": {
    badgeBg: "bg-urgent-100",
    badgeText: "text-urgent-700",
    badgeBorder: "border-urgent-200",
  },
};

/* ─── Test icon map ─── */
const TEST_ICONS = {
  "blood smear": Microscope,
  "rdt": FlaskConical,
  "rapid diagnostic": FlaskConical,
  "cbc": TestTube,
  "complete blood count": TestTube,
  "widal": TestTube,
  "culture": FlaskConical,
  "x-ray": ScanLine,
  "pcr": Microscope,
  "antigen": FlaskConical,
  "ns1": FlaskConical,
  "urinalysis": TestTube,
  "spirometry": Activity,
  "glucose": TestTube,
  "hba1c": TestTube,
};

function getTestIcon(testName) {
  const lower = testName.toLowerCase();
  for (const key of Object.keys(TEST_ICONS)) {
    if (lower.includes(key)) return TEST_ICONS[key];
  }
  return Microscope;
}

/* ─── Confidence bar color helper ─── */
function confidenceBarColor(confidence) {
  if (confidence >= 0.7) return "bg-success-500";
  if (confidence >= 0.4) return "bg-caution-500";
  return "bg-urgent-500";
}

function confidenceBadgeClasses(confidence) {
  if (confidence >= 0.7)
    return "bg-success-100 text-success-700 border-success-200";
  if (confidence >= 0.4)
    return "bg-caution-100 text-caution-700 border-caution-200";
  return "bg-urgent-100 text-urgent-700 border-urgent-200";
}

/* ─── Tooltip component ─── */
function Tooltip({ children, text }) {
  const [show, setShow] = useState(false);
  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-56 bg-slate-800 text-white text-xs rounded-lg px-3 py-2 shadow-lg z-50">
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-800" />
        </div>
      )}
    </div>
  );
}

/* ─── Main Page ─── */
export default function SubmitSymptomsPage() {
  const navigate = useNavigate();
  const [symptoms, setSymptoms] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [consultLoading, setConsultLoading] = useState(false);
  const [consultSuccess, setConsultSuccess] = useState("");
  const [doctors, setDoctors] = useState([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState(null);
  const [recommendedDoctor, setRecommendedDoctor] = useState(null);
  const [doctorStats, setDoctorStats] = useState({});
  const [doctorRatings, setDoctorRatings] = useState({});
  const [showStatsFor, setShowStatsFor] = useState(null);
  const [typingActive, setTypingActive] = useState(false);
  const resultRef = useRef(null);

  useEffect(() => {
    getDoctorsPreview()
      .then((res) => setDoctors(res.data.doctors || []))
      .catch(() => setDoctors([]));
  }, []);

  /* Scroll to results when they appear */
  useEffect(() => {
    if (result && resultRef.current) {
      setTimeout(() => {
        resultRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 100);
    }
  }, [result]);

  const handleChipClick = (symptom) => {
    setSymptoms((prev) => {
      const trimmed = prev.trim();
      if (!trimmed) return symptom;
      const lastChar = trimmed.slice(-1);
      const separator = lastChar === "," ? " " : ", ";
      return trimmed + separator + symptom;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setConsultSuccess("");
    setRecommendedDoctor(null);
    setDoctorStats({});
    setShowStatsFor(null);
    setLoading(true);
    setTypingActive(true);

    try {
      const res = await predictSymptoms(symptoms);
      setResult(res.data);
      const topCondition = res.data.predictions?.[0]?.condition || "";

      try {
        const recRes = await getRecommendedDoctor(topCondition);
        setRecommendedDoctor(recRes.data.recommendation);
        if (recRes.data.recommendation?.doctor?.id) {
          setSelectedDoctorId(recRes.data.recommendation.doctor.id);
        }
      } catch {
        if (doctors.length > 0) {
          const sorted = [...doctors].sort(
            (a, b) => (a.current_load || 0) - (b.current_load || 0)
          );
          setSelectedDoctorId(sorted[0].id);
        }
      }
    } catch (err) {
      const msg = err.response?.data?.message || "Prediction failed";
      setError(msg);
    } finally {
      setLoading(false);
      setTypingActive(false);
    }
  };

  const handleShowStats = async (doctorId) => {
    if (showStatsFor === doctorId) {
      setShowStatsFor(null);
      return;
    }
    setShowStatsFor(doctorId);
    if (!doctorStats[doctorId]) {
      try {
        const res = await getDoctorPublicStats(doctorId);
        setDoctorStats((prev) => ({ ...prev, [doctorId]: res.data.stats }));
      } catch {
        /* silently fail */
      }
    }
    if (!doctorRatings[doctorId]) {
      try {
        const res = await getDoctorRatingSummary(doctorId);
        setDoctorRatings((prev) => ({ ...prev, [doctorId]: res.data.summary }));
      } catch {
        /* silently fail */
      }
    }
  };

  const topPrediction = result?.predictions?.[0];
  const predictions = result?.predictions || [];
  const matchedDoctor = doctors.find((d) => d.id === selectedDoctorId);

  const handleConsultDoctor = async () => {
    setConsultLoading(true);
    setConsultSuccess("");
    setError("");
    try {
      const res = await createConsultation({
        symptoms,
        predicted_condition: topPrediction?.condition || "",
        message: "",
        preferred_doctor_id: selectedDoctorId || undefined,
      });
      setConsultSuccess(res?.data?.info || "Consultation created successfully!");
      setTimeout(() => navigate("/patient/dashboard"), 1500);
    } catch (err) {
      setError(err?.response?.data?.error || "Failed to create consultation");
    } finally {
      setConsultLoading(false);
    }
  };

  const severityCfg = result?.severity
    ? SEVERITY_CONFIG[result.severity]
    : null;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
      {/* ─── Header ─── */}
      <div className="mb-8 text-center sm:text-left">
        <div className="inline-flex items-center gap-2 bg-clinical-50 border border-clinical-200 rounded-full px-3 py-1 mb-3">
          <BrainCircuit className="w-4 h-4 text-clinical-600" />
          <span className="text-xs font-semibold text-clinical-700 uppercase tracking-wide">
            AI-Assisted Clinical Support
          </span>
        </div>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
          Symptom Checker
        </h1>
        <p className="text-sm text-slate-500 mt-2 max-w-xl">
          Describe your symptoms in plain language. Our hybrid clinical engine
          analyzes your input against tropical disease patterns and provides
          evidence-based guidance.
        </p>
      </div>

      {/* ─── Input Card ─── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-7 mb-6 animate-fade-in-up">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-slate-800 mb-2">
              Describe your symptoms
            </label>
            <div className="relative">
              <textarea
                value={symptoms}
                onChange={(e) => setSymptoms(e.target.value)}
                required
                rows={5}
                placeholder="e.g. I have had a high fever for two days with headache, chills, and body aches..."
                className="w-full px-4 py-3.5 rounded-xl border border-slate-300 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-y text-sm leading-relaxed"
              />
              {symptoms.length > 0 && (
                <button
                  type="button"
                  onClick={() => setSymptoms("")}
                  className="absolute top-3 right-3 p-1 rounded-md hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Tip: Include duration, severity, and any recent travel or exposures
              for more accurate analysis.
            </p>
          </div>

          {/* Common symptom chips */}
          <div>
            <p className="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wide">
              Common Symptoms
            </p>
            <div className="flex flex-wrap gap-2">
              {COMMON_SYMPTOMS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => handleChipClick(s)}
                  className="text-xs font-medium bg-slate-50 text-slate-600 border border-slate-200 rounded-lg px-3 py-1.5 hover:bg-primary-50 hover:text-primary-700 hover:border-primary-200 transition-all"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Swahili symptom chips */}
          <div>
            <p className="text-xs font-medium text-slate-500 mb-2 uppercase tracking-wide flex items-center gap-1.5">
              <span>Maumivu ya Kawaida</span>
              <span className="text-[10px] bg-emerald-50 text-emerald-600 border border-emerald-200 rounded-full px-1.5 py-0.5">
                Swahili
              </span>
            </p>
            <div className="flex flex-wrap gap-2">
              {SWAHILI_SYMPTOMS.map((s) => (
                <button
                  key={s.sw}
                  type="button"
                  onClick={() => handleChipClick(s.sw)}
                  className="text-xs font-medium bg-emerald-50/60 text-emerald-700 border border-emerald-200 rounded-lg px-3 py-1.5 hover:bg-emerald-50 hover:text-emerald-800 hover:border-emerald-300 transition-all"
                  title={`${s.sw} = ${s.en}`}
                >
                  {s.sw}
                </button>
              ))}
            </div>
          </div>

          {/* Error / Success messages */}
          {error && (
            <div className="bg-urgent-50 border border-urgent-200 rounded-xl px-4 py-4 animate-fade-in-up">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-urgent-500 mt-0.5 shrink-0" />
                <div>
                  <p className="text-sm font-semibold text-urgent-800">
                    Unable to Analyze
                  </p>
                  <p className="text-sm text-urgent-700 mt-1">{error}</p>
                  <div className="mt-3 bg-white/60 rounded-lg px-3 py-2.5 border border-urgent-100">
                    <p className="text-xs font-medium text-urgent-700 mb-1">
                      Suggestions:
                    </p>
                    <ul className="text-xs text-urgent-600 space-y-1 list-disc list-inside">
                      <li>Describe at least 3 symptoms with some detail</li>
                      <li>Use common medical terms (e.g., fever, headache, nausea)</li>
                      <li>Mention how long you have been experiencing them</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {consultSuccess && (
            <div className="bg-success-50 border border-success-200 rounded-xl px-4 py-3 flex items-center gap-3 animate-fade-in-up">
              <UserCheck className="w-5 h-5 text-success-600 shrink-0" />
              <p className="text-sm font-medium text-success-800">
                {consultSuccess}
              </p>
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading || symptoms.trim().length < 3}
            className="w-full sm:w-auto inline-flex items-center justify-center bg-primary-600 text-white font-semibold px-8 py-3 rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md"
          >
            {loading ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2.5" />
                Analyzing Symptoms…
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Analyze Symptoms
              </>
            )}
          </button>
        </form>
      </div>

      {/* ─── Loading / Typing Indicator ─── */}
      {loading && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 mb-6 animate-fade-in-up">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-clinical-50 flex items-center justify-center">
              <BrainCircuit className="w-5 h-5 text-clinical-600 animate-pulse" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">
                AI Clinical Engine is analyzing…
              </p>
              <p className="text-xs text-slate-500">
                Cross-referencing symptom patterns against disease knowledge base
              </p>
            </div>
          </div>
          <div className="space-y-4">
            <div className="h-3 rounded-full animate-shimmer w-3/4" />
            <div className="h-3 rounded-full animate-shimmer w-1/2" />
            <div className="h-3 rounded-full animate-shimmer w-5/6" />
            <div className="h-3 rounded-full animate-shimmer w-2/3" />
          </div>
          <div className="mt-6 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-clinical-400 typing-dot" />
            <span className="w-2 h-2 rounded-full bg-clinical-400 typing-dot" />
            <span className="w-2 h-2 rounded-full bg-clinical-400 typing-dot" />
            <span className="text-xs text-slate-400 ml-1">
              Processing natural language…
            </span>
          </div>
        </div>
      )}

      {/* ─── Results ─── */}
      {result && (
        <div ref={resultRef} className="space-y-6">
          {/* ═══ Emergency Banner (HIGH severity) ═══ */}
          {result.severity === "HIGH" && (
            <div className="animate-fade-in-up animate-pulse-ring rounded-2xl border border-urgent-200 bg-urgent-50 p-5 flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-urgent-100 flex items-center justify-center shrink-0">
                <HeartPulse className="w-5 h-5 text-urgent-600" />
              </div>
              <div>
                <p className="text-sm font-bold text-urgent-800">
                  Emergency Alert — High Severity Detected
                </p>
                <p className="text-sm text-urgent-700 mt-1">
                  {result.urgency_message}
                </p>
                {result.detected_red_flags &&
                  result.detected_red_flags.length > 0 && (
                    <p className="text-xs text-urgent-600 mt-2 font-medium">
                      Detected red flags:{" "}
                      {result.detected_red_flags.join(", ")}
                    </p>
                  )}
              </div>
            </div>
          )}

          {/* ═══ Primary Prediction Card ═══ */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden animate-fade-in-up stagger-1">
            {/* Card header with severity & match */}
            <div className="px-6 py-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-clinical-50 flex items-center justify-center">
                  <Stethoscope className="w-5 h-5 text-clinical-600" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Clinical Assessment
                  </h2>
                  <p className="text-xs text-slate-500">
                    AI-generated triage report — not a final diagnosis
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                {result.severity && severityCfg && (
                  <span
                    className={`inline-flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-full border ${severityCfg.badgeBg} ${severityCfg.badgeText} ${severityCfg.badgeBorder}`}
                  >
                    <severityCfg.icon className="w-3.5 h-3.5" />
                    {severityCfg.label}
                  </span>
                )}
                {result.match_quality && (
                  <span
                    className={`text-xs font-bold px-3 py-1.5 rounded-full border ${
                      MATCH_CONFIG[result.match_quality]?.badgeBg || "bg-slate-100"
                    } ${
                      MATCH_CONFIG[result.match_quality]?.badgeText || "text-slate-700"
                    } ${
                      MATCH_CONFIG[result.match_quality]?.badgeBorder ||
                      "border-slate-200"
                    }`}
                  >
                    {result.match_quality}
                  </span>
                )}
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Primary condition */}
              {topPrediction && (
                <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                  <div className="flex-1">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">
                      Primary Prediction
                    </p>
                    <p className="text-2xl sm:text-3xl font-bold text-slate-900">
                      {topPrediction.condition}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-xs text-slate-500">Confidence</p>
                      <p className="text-xl font-bold text-slate-800">
                        {(topPrediction.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                    <div className="w-14 h-14 relative">
                      <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                        <path
                          className="text-slate-100"
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                        />
                        <path
                          className={
                            topPrediction.confidence >= 0.7
                              ? "text-success-500"
                              : topPrediction.confidence >= 0.4
                              ? "text-caution-500"
                              : "text-urgent-500"
                          }
                          d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="3"
                          strokeDasharray={`${
                            topPrediction.confidence * 100
                          }, 100`}
                          style={{ transition: "stroke-dasharray 1s ease-out" }}
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <Activity className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Cleaned symptoms */}
              {result.cleaned_symptoms && result.cleaned_symptoms.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                    Symptoms Understood
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {result.cleaned_symptoms.map((s, i) => (
                      <span
                        key={i}
                        className="text-xs font-medium bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Top-3 Predictions Visual Ranking */}
              {predictions.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
                    Differential Diagnosis (Top 3)
                  </p>
                  <div className="space-y-3">
                    {predictions.map((p, idx) => {
                      const pct = (p.confidence * 100).toFixed(0);
                      const isTop = idx === 0;
                      return (
                        <div
                          key={p.condition || `pred-${idx}`}
                          className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                            isTop
                              ? "bg-clinical-50/50 border-clinical-200"
                              : "bg-white border-slate-100"
                          }`}
                        >
                          <span
                            className={`text-xs font-bold w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                              isTop
                                ? "bg-clinical-100 text-clinical-700"
                                : "bg-slate-100 text-slate-500"
                            }`}
                          >
                            {idx + 1}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-semibold text-slate-800 truncate">
                                {p.condition}
                              </span>
                              <span
                                className={`text-xs font-bold px-2 py-0.5 rounded-full border ml-2 shrink-0 ${confidenceBadgeClasses(
                                  p.confidence
                                )}`}
                              >
                                {pct}%
                              </span>
                            </div>
                            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                              <div
                                className={`h-full rounded-full animate-bar-fill ${confidenceBarColor(
                                  p.confidence
                                )}`}
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Urgency Guidance (non-emergency) */}
              {result.urgency_message && result.severity !== "HIGH" && (
                <div
                  className={`rounded-xl px-5 py-4 border flex items-start gap-3 ${
                    result.severity === "MEDIUM"
                      ? "bg-caution-50 border-caution-200"
                      : "bg-success-50 border-success-200"
                  }`}
                >
                  <Clock
                    className={`w-5 h-5 mt-0.5 shrink-0 ${
                      result.severity === "MEDIUM"
                        ? "text-caution-600"
                        : "text-success-600"
                    }`}
                  />
                  <div>
                    <p
                      className={`text-sm font-semibold ${
                        result.severity === "MEDIUM"
                          ? "text-caution-800"
                          : "text-success-800"
                      }`}
                    >
                      {result.severity === "MEDIUM"
                        ? "Timely Medical Attention Recommended"
                        : "Self-Care May Be Sufficient"}
                    </p>
                    <p
                      className={`text-sm mt-1 ${
                        result.severity === "MEDIUM"
                          ? "text-caution-700"
                          : "text-success-700"
                      }`}
                    >
                      {result.urgency_message}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ═══ AI Clinical Insight Panel ═══ */}
          {result.clinical_insight && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 animate-fade-in-up stagger-2">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-lg bg-clinical-50 flex items-center justify-center">
                  <BrainCircuit className="w-4.5 h-4.5 text-clinical-600" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    AI Clinical Insight
                  </h3>
                  <p className="text-xs text-slate-500">
                    Why this prediction matches your presentation
                  </p>
                </div>
                <Tooltip text="This insight is generated by matching your symptoms against our clinical knowledge base. It explains the likely disease mechanism and what to watch for.">
                  <Info className="w-4 h-4 text-slate-300 hover:text-slate-500 cursor-help ml-auto" />
                </Tooltip>
              </div>
              <div className="bg-slate-50 rounded-xl border border-slate-100 p-4">
                <p className="text-sm text-slate-700 leading-relaxed">
                  {result.clinical_insight}
                </p>
              </div>
              {result.ai_advice && (
                <div className="mt-4 bg-primary-50 rounded-xl border border-primary-100 p-4">
                  <p className="text-xs font-bold text-primary-800 mb-1">
                    Recommended Next Steps
                  </p>
                  <p className="text-sm text-primary-800 leading-relaxed">
                    {result.ai_advice}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ═══ Recommended Tests Panel ═══ */}
          {result.recommended_tests && result.recommended_tests.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 animate-fade-in-up stagger-3">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-9 h-9 rounded-lg bg-violet-50 flex items-center justify-center">
                  <FlaskConical className="w-4.5 h-4.5 text-violet-600" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">
                    Recommended Diagnostic Tests
                  </h3>
                  <p className="text-xs text-slate-500">
                    Suggested investigations to confirm or rule out
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {result.recommended_tests.map((test, i) => {
                  const Icon = getTestIcon(test);
                  return (
                    <div
                      key={i}
                      className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-200 transition-all group"
                    >
                      <div className="w-9 h-9 rounded-lg bg-white border border-slate-100 flex items-center justify-center shrink-0 group-hover:shadow-sm transition-shadow">
                        <Icon className="w-4.5 h-4.5 text-slate-500 group-hover:text-clinical-600 transition-colors" />
                      </div>
                      <span className="text-sm font-medium text-slate-700">
                        {test}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ═══ Trust & Disclaimer Panel ═══ */}
          <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5 animate-fade-in-up stagger-4">
            <div className="flex items-start gap-3">
              <Info className="w-5 h-5 text-slate-400 mt-0.5 shrink-0" />
              <div className="space-y-2">
                <p className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                  Important Notice
                </p>
                <p className="text-xs text-slate-600 leading-relaxed">
                  This tool provides <strong>AI-assisted clinical support</strong>{" "}
                  and is <strong>not a final medical diagnosis</strong>. Predictions
                  are based on pattern matching and statistical modeling. Always
                  consult a licensed healthcare provider for definitive evaluation
                  and treatment.
                </p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="text-[10px] font-medium bg-white text-slate-500 border border-slate-200 rounded-full px-2.5 py-1">
                    Not a Diagnosis
                  </span>
                  <span className="text-[10px] font-medium bg-white text-slate-500 border border-slate-200 rounded-full px-2.5 py-1">
                    Consult a Provider
                  </span>
                  <span className="text-[10px] font-medium bg-white text-slate-500 border border-slate-200 rounded-full px-2.5 py-1">
                    Emergency? Call Local Emergency Services
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* ═══ Doctor Selection ═══ */}
          {predictions.length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 animate-fade-in-up stagger-5">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-9 h-9 rounded-lg bg-primary-50 flex items-center justify-center">
                  <UserCheck className="w-4.5 h-4.5 text-primary-600" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Connect with a Doctor
                  </h2>
                  <p className="text-xs text-slate-500">
                    Choose a healthcare provider for follow-up consultation
                  </p>
                </div>
              </div>

              {/* Smart recommendation */}
              {recommendedDoctor && (
                <div className="bg-primary-50 border border-primary-200 rounded-xl px-4 py-3 mb-5 flex items-start gap-3">
                  <Sparkles className="w-5 h-5 text-primary-600 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-primary-800">
                      Recommended: Dr. {recommendedDoctor.doctor.name} (
                      {recommendedDoctor.doctor.specialization})
                    </p>
                    <p className="text-xs text-primary-600 mt-0.5">
                      {recommendedDoctor.reason} · Active Patients:{" "}
                      {recommendedDoctor.doctor.current_load}
                    </p>
                  </div>
                </div>
              )}

              {doctors.length === 0 ? (
                <div className="bg-caution-50 border border-caution-200 rounded-xl px-4 py-3 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-caution-500 mt-0.5 shrink-0" />
                  <p className="text-sm text-caution-700">
                    No doctors available at the moment. Please try again later or
                    visit your nearest clinic.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
                  {[...doctors]
                    .sort((a, b) => (a.current_load || 0) - (b.current_load || 0))
                    .map((doc) => {
                      const isRec = recommendedDoctor?.doctor?.id === doc.id;
                      const stats = doctorStats[doc.id];
                      const rating = doctorRatings[doc.id];
                      const isOpen = showStatsFor === doc.id;
                      return (
                        <div key={doc.id} className="space-y-2">
                          <button
                            onClick={() => setSelectedDoctorId(doc.id)}
                            className={`w-full text-left p-4 rounded-xl border transition-all ${
                              selectedDoctorId === doc.id
                                ? "border-primary-500 bg-primary-50 ring-1 ring-primary-500 shadow-sm"
                                : isRec
                                ? "border-primary-200 bg-primary-50/30 hover:bg-primary-50/50"
                                : "border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300"
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <div
                                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                                  isRec
                                    ? "bg-primary-100 text-primary-700"
                                    : "bg-slate-100 text-slate-600"
                                }`}
                              >
                                {doc.name?.charAt(0) || "D"}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 flex-wrap">
                                  <p className="text-sm font-semibold text-slate-800">
                                    Dr. {doc.name}
                                  </p>
                                  {isRec && (
                                    <span className="text-[10px] bg-primary-100 text-primary-700 px-1.5 py-0.5 rounded border border-primary-200 font-medium">
                                      Recommended
                                    </span>
                                  )}
                                  {doc.is_verified ? (
                                    <span className="text-[10px] bg-clinical-50 text-clinical-600 px-1.5 py-0.5 rounded border border-clinical-100 font-medium">
                                      Verified
                                    </span>
                                  ) : (
                                    <span className="text-[10px] bg-caution-50 text-caution-600 px-1.5 py-0.5 rounded border border-caution-100 font-medium">
                                      Pending
                                    </span>
                                  )}
                                </div>
                                <p className="text-xs text-slate-500">
                                  {doc.specialization}
                                </p>
                                <div className="flex items-center gap-2 mt-1">
                                  <span
                                    className={`text-xs flex items-center gap-1 ${
                                      doc.is_available
                                        ? "text-success-600"
                                        : "text-urgent-500"
                                    }`}
                                  >
                                    <span
                                      className={`w-1.5 h-1.5 rounded-full ${
                                        doc.is_available
                                          ? "bg-success-500"
                                          : "bg-urgent-500"
                                      }`}
                                    />
                                    {doc.is_available
                                      ? "Available"
                                      : "Currently Busy"}
                                  </span>
                                  <span className="text-xs text-slate-400">
                                    · Load: {doc.current_load}
                                  </span>
                                </div>
                                {rating && rating.total_reviews > 0 && (
                                  <div className="flex items-center gap-1.5 mt-1.5">
                                    <div className="flex">
                                      {[1, 2, 3, 4, 5].map((s) => (
                                        <span
                                          key={s}
                                          className={`text-xs ${
                                            s <= Math.round(rating.average_rating)
                                              ? "text-amber-400"
                                              : "text-slate-200"
                                          }`}
                                        >
                                          ★
                                        </span>
                                      ))}
                                    </div>
                                    <span className="text-[10px] text-slate-500">
                                      {rating.average_rating.toFixed(1)} (
                                      {rating.total_reviews} review
                                      {rating.total_reviews !== 1 ? "s" : ""})
                                    </span>
                                  </div>
                                )}
                              </div>
                              {selectedDoctorId === doc.id && (
                                <div className="ml-auto w-6 h-6 rounded-full bg-primary-600 flex items-center justify-center">
                                  <svg
                                    className="w-3.5 h-3.5 text-white"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    strokeWidth={3}
                                  >
                                    <path
                                      strokeLinecap="round"
                                      strokeLinejoin="round"
                                      d="M5 13l4 4L19 7"
                                    />
                                  </svg>
                                </div>
                              )}
                            </div>
                          </button>

                          {/* Stats toggle */}
                          <button
                            onClick={() => handleShowStats(doc.id)}
                            className="w-full text-center text-xs text-slate-500 hover:text-primary-600 py-1 transition-colors flex items-center justify-center gap-1"
                          >
                            {isOpen ? (
                              <>
                                Hide Stats{" "}
                                <ChevronUp className="w-3 h-3" />
                              </>
                            ) : (
                              <>
                                View Stats & Experience{" "}
                                <ChevronDown className="w-3 h-3" />
                              </>
                            )}
                          </button>

                          {/* Expanded stats */}
                          {isOpen && stats && (
                            <div className="bg-slate-50 rounded-xl border border-slate-200 p-3 text-xs space-y-1.5">
                              <div className="flex justify-between">
                                <span className="text-slate-500">
                                  Total Consultations:
                                </span>
                                <span className="font-semibold text-slate-700">
                                  {stats.total_consultations}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-500">
                                  Cases Resolved:
                                </span>
                                <span className="font-semibold text-success-600">
                                  {stats.total_resolved}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-500">
                                  Avg Response Time:
                                </span>
                                <span className="font-semibold text-slate-700">
                                  {stats.average_response_minutes < 1
                                    ? "< 1 min"
                                    : `${stats.average_response_minutes} min`}
                                </span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-slate-500">
                                  Patients (Last 7 Days):
                                </span>
                                <span className="font-semibold text-slate-700">
                                  {stats.recent_patients_7d}
                                </span>
                              </div>
                              {rating && rating.total_reviews > 0 && (
                                <div className="pt-1 border-t border-slate-100">
                                  <div className="flex justify-between items-center">
                                    <span className="text-slate-500">
                                      Rating:
                                    </span>
                                    <span className="font-semibold text-amber-600">
                                      {rating.average_rating.toFixed(1)} / 5
                                    </span>
                                  </div>
                                  <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                                    <span>★ {rating.distribution[5]} five-star</span>
                                    <span>★ {rating.distribution[4]} four-star</span>
                                    <span>★ {rating.distribution[3]} three-star</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                          {isOpen && !stats && (
                            <div className="bg-slate-50 rounded-xl border border-slate-200 p-3 text-center">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 inline-block" />
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>
              )}

              {matchedDoctor && (
                <div className="bg-primary-50 border border-primary-100 rounded-xl px-4 py-3 mb-5 flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-primary-600" />
                  <p className="text-sm text-primary-800">
                    <span className="font-semibold">Selected:</span> Dr.{" "}
                    {matchedDoctor.name} ({matchedDoctor.specialization})
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleConsultDoctor}
                  disabled={consultLoading || doctors.length === 0}
                  className="inline-flex items-center bg-primary-600 text-white font-semibold px-6 py-2.5 rounded-xl hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm hover:shadow-md"
                >
                  {consultLoading ? (
                    <>
                      <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Creating Consultation…
                    </>
                  ) : (
                    <>
                      <Stethoscope className="w-4 h-4 mr-2" />
                      Consult Doctor
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </>
                  )}
                </button>
                <button
                  onClick={() => navigate("/patient/dashboard")}
                  className="inline-flex items-center bg-white border border-slate-300 text-slate-700 font-semibold px-6 py-2.5 rounded-xl hover:bg-slate-50 transition-all"
                >
                  Go to Dashboard
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
