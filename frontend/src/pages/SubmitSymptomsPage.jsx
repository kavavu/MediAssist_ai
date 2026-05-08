/**
 * Submit symptoms page.
 *
 * - Textarea for symptom input
 * - POSTs to /api/predict
 * - Shows doctor assignment preview before confirming consultation
 * - Renders top-3 predicted conditions as cards
 * - Shows "Consult Doctor" button to create a consultation
 */
import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import api from "../services/api.js";
import { createConsultation, getDoctorsPreview, getRecommendedDoctor, getDoctorPublicStats } from "../services/consultation.js";

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
  const [showDoctorSelect, setShowDoctorSelect] = useState(false);
  const [recommendedDoctor, setRecommendedDoctor] = useState(null);
  const [doctorStats, setDoctorStats] = useState({});
  const [showStatsFor, setShowStatsFor] = useState(null);

  useEffect(() => {
    getDoctorsPreview()
      .then((res) => setDoctors(res.data.doctors || []))
      .catch(() => setDoctors([]));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setConsultSuccess("");
    setShowDoctorSelect(false);
    setRecommendedDoctor(null);
    setDoctorStats({});
    setShowStatsFor(null);
    setLoading(true);
    try {
      const res = await api.post("/predict", { symptoms_text: symptoms });
      setResult(res.data);
      const topCondition = res.data.predictions?.[0]?.condition || "";
      
      // Fetch smart recommendation based on top condition
      try {
        const recRes = await getRecommendedDoctor(topCondition);
        setRecommendedDoctor(recRes.data.recommendation);
        if (recRes.data.recommendation?.doctor?.id) {
          setSelectedDoctorId(recRes.data.recommendation.doctor.id);
        }
      } catch {
        // Fallback: auto-select the least-loaded available doctor
        if (doctors.length > 0) {
          const sorted = [...doctors].sort((a, b) => (a.current_load || 0) - (b.current_load || 0));
          setSelectedDoctorId(sorted[0].id);
        }
      }
    } catch (err) {
      setError(err.response?.data?.message || "Prediction failed");
    } finally {
      setLoading(false);
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
        // silently fail
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
      setConsultSuccess(res.data.info || "Consultation created successfully!");
      setTimeout(() => navigate("/patient/dashboard"), 1500);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to create consultation");
    } finally {
      setConsultLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-800">Submit Symptoms</h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe your symptoms and our AI will analyze possible conditions. You can then choose a doctor for consultation.
        </p>
      </div>

      {/* Input Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">
              Describe your symptoms
            </label>
            <textarea
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              required
              rows={5}
              placeholder="e.g. headache, fever, body aches for two days..."
              className="w-full px-4 py-3 rounded-lg border border-slate-300 bg-white text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all resize-y"
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
          {consultSuccess && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
              <p className="text-sm text-emerald-700">{consultSuccess}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center bg-primary-600 text-white font-semibold px-6 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Analyzing...
              </>
            ) : (
              "🔍 Analyze Symptoms"
            )}
          </button>
        </form>
      </div>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Prediction Cards */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Possible Conditions</h2>

            {predictions.length === 0 && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
                <p className="text-sm text-amber-700">
                  No confident prediction could be generated. Please consult a doctor.
                </p>
              </div>
            )}

            {predictions.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {predictions.map((p, idx) => {
                  const isTop = idx === 0;
                  const confidencePct = (p.confidence * 100).toFixed(1);
                  const badgeColor =
                    p.confidence >= 0.7
                      ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                      : p.confidence >= 0.4
                      ? "bg-amber-100 text-amber-700 border-amber-200"
                      : "bg-red-100 text-red-700 border-red-200";

                  return (
                    <div
                      key={p.condition}
                      className={`rounded-xl border p-4 transition-all ${
                        isTop
                          ? "border-primary-500 bg-primary-50/40 ring-1 ring-primary-500"
                          : "border-slate-200 bg-slate-50/40"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="font-bold text-slate-800 text-sm">{p.condition}</h3>
                        {isTop && (
                          <span className="text-[10px] font-bold bg-primary-600 text-white px-2 py-0.5 rounded-full uppercase tracking-wide">
                            Top Match
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-500">Confidence:</span>
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full border ${badgeColor}`}>
                          {confidencePct}%
                        </span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-1.5 mt-3">
                        <div
                          className={`h-1.5 rounded-full ${
                            p.confidence >= 0.7
                              ? "bg-emerald-500"
                              : p.confidence >= 0.4
                              ? "bg-amber-500"
                              : "bg-red-500"
                          }`}
                          style={{ width: `${confidencePct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {result.recommendation && (
              <div className="mt-4 bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
                <p className="text-sm text-blue-800 font-medium">{result.recommendation}</p>
              </div>
            )}

            {/* Disclaimer */}
            <div className="mt-4 bg-amber-50 border border-amber-100 rounded-lg px-4 py-3 flex items-start gap-2">
              <span className="text-amber-500 text-sm mt-0.5">⚠️</span>
              <p className="text-xs text-amber-700">
                <strong>Disclaimer:</strong> This AI prediction is not a medical diagnosis. Always consult a qualified healthcare professional.
              </p>
            </div>
          </div>

          {/* Doctor Selection */}
          {predictions.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <h2 className="text-lg font-bold text-slate-800 mb-4">Choose a Doctor</h2>

              {/* Smart Recommendation Banner */}
              {recommendedDoctor && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 mb-4">
                  <div className="flex items-start gap-2">
                    <span className="text-emerald-600 text-sm mt-0.5">🎯</span>
                    <div>
                      <p className="text-sm font-semibold text-emerald-800">
                        Recommended: Dr. {recommendedDoctor.doctor.name} ({recommendedDoctor.doctor.specialization})
                      </p>
                      <p className="text-xs text-emerald-600 mt-0.5">
                        {recommendedDoctor.reason} | Active Patients: {recommendedDoctor.doctor.current_load}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <p className="text-sm text-slate-500 mb-4">
                Based on your symptoms, we recommend selecting a doctor below. The system will auto-assign the best match if you don't choose.
              </p>

              {doctors.length === 0 ? (
                <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
                  <p className="text-sm text-amber-700">No doctors available at the moment. Please try again later.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
                  {/* Sort doctors by least load for fair display */}
                  {[...doctors].sort((a, b) => (a.current_load || 0) - (b.current_load || 0)).map((doc) => {
                    const isRecommended = recommendedDoctor?.doctor?.id === doc.id;
                    const stats = doctorStats[doc.id];
                    const isStatsOpen = showStatsFor === doc.id;
                    return (
                      <div key={doc.id} className="space-y-2">
                        <button
                          onClick={() => setSelectedDoctorId(doc.id)}
                          className={`w-full text-left p-4 rounded-xl border transition-all ${
                            selectedDoctorId === doc.id
                              ? "border-primary-500 bg-primary-50 ring-1 ring-primary-500"
                              : isRecommended
                              ? "border-emerald-300 bg-emerald-50/30 hover:bg-emerald-50/50"
                              : "border-slate-200 bg-white hover:bg-slate-50"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${
                              isRecommended ? "bg-emerald-100 text-emerald-700" : "bg-primary-100 text-primary-700"
                            }`}>
                              {doc.name?.charAt(0) || "D"}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <p className="text-sm font-semibold text-slate-800">Dr. {doc.name}</p>
                                {isRecommended && (
                                  <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded border border-emerald-200 font-medium">
                                    🎯 Recommended
                                  </span>
                                )}
                                {doc.is_verified ? (
                                  <span className="text-[10px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded border border-blue-100 font-medium">
                                    ✅ Verified
                                  </span>
                                ) : (
                                  <span className="text-[10px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded border border-amber-100 font-medium">
                                    ⏳ Pending
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-500">{doc.specialization}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className={doc.is_available ? "text-green-500 text-xs" : "text-red-500 text-xs"}>
                                  {doc.is_available ? "🟢 Available" : "🔴 Busy"}
                                </span>
                                <span className="text-xs text-slate-400">| Active Patients: {doc.current_load}</span>
                              </div>
                            </div>
                            {selectedDoctorId === doc.id && (
                              <span className="ml-auto text-primary-600 text-lg">✓</span>
                            )}
                          </div>
                        </button>
                        {/* Stats toggle button */}
                        <button
                          onClick={() => handleShowStats(doc.id)}
                          className="w-full text-center text-xs text-slate-500 hover:text-primary-600 py-1 transition-colors"
                        >
                          {isStatsOpen ? "▲ Hide Stats" : "▼ View Stats & Experience"}
                        </button>
                        {/* Expanded stats */}
                        {isStatsOpen && stats && (
                          <div className="bg-slate-50 rounded-lg border border-slate-200 p-3 text-xs space-y-1.5">
                            <div className="flex justify-between">
                              <span className="text-slate-500">Total Consultations:</span>
                              <span className="font-semibold text-slate-700">{stats.total_consultations}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Cases Resolved:</span>
                              <span className="font-semibold text-emerald-600">{stats.total_resolved}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Avg Response Time:</span>
                              <span className="font-semibold text-slate-700">
                                {stats.average_response_minutes < 1 ? "< 1 min" : `${stats.average_response_minutes} min`}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Patients (Last 7 Days):</span>
                              <span className="font-semibold text-slate-700">{stats.recent_patients_7d}</span>
                            </div>
                          </div>
                        )}
                        {isStatsOpen && !stats && (
                          <div className="bg-slate-50 rounded-lg border border-slate-200 p-3 text-center">
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600 inline-block" />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {matchedDoctor && (
                <div className="bg-primary-50 border border-primary-100 rounded-lg px-4 py-3 mb-4">
                  <p className="text-sm text-primary-800">
                    <span className="font-semibold">Selected:</span> Dr. {matchedDoctor.name} ({matchedDoctor.specialization})
                  </p>
                </div>
              )}

              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleConsultDoctor}
                  disabled={consultLoading || doctors.length === 0}
                  className="inline-flex items-center bg-primary-600 text-white font-semibold px-5 py-2.5 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {consultLoading ? (
                    <>
                      <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                      Creating...
                    </>
                  ) : (
                    "🩺 Consult Doctor"
                  )}
                </button>
                <button
                  onClick={() => navigate("/patient/dashboard")}
                  className="inline-flex items-center bg-white border border-slate-300 text-slate-700 font-semibold px-5 py-2.5 rounded-lg hover:bg-slate-50 transition-colors"
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
