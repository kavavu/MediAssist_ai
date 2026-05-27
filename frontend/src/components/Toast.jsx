import React, { useEffect, useState } from "react";
import { CheckCircle, XCircle, AlertTriangle, Info, X } from "lucide-react";

const ICONS = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};

const STYLES = {
  success: "bg-emerald-50 border-emerald-200 text-emerald-800",
  error: "bg-red-50 border-red-200 text-red-800",
  warning: "bg-amber-50 border-amber-200 text-amber-800",
  info: "bg-sky-50 border-sky-200 text-sky-800",
};

const ICON_COLORS = {
  success: "text-emerald-500",
  error: "text-red-500",
  warning: "text-amber-500",
  info: "text-sky-500",
};

const PROGRESS_COLORS = {
  success: "bg-emerald-400",
  error: "bg-red-400",
  warning: "bg-amber-400",
  info: "bg-sky-400",
};

export default function Toast({ id, type, message, duration = 4000, onRemove }) {
  const [progress, setProgress] = useState(100);
  const [exiting, setExiting] = useState(false);
  const Icon = ICONS[type] || Info;

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - start;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        handleClose();
      }
    }, 50);
    return () => clearInterval(interval);
  }, [duration]);

  const handleClose = () => {
    setExiting(true);
    setTimeout(() => onRemove(id), 300);
  };

  return (
    <div
      className={`
        relative flex items-start gap-3 px-4 py-3 rounded-xl border shadow-lg
        min-w-[320px] max-w-[420px] overflow-hidden
        transition-all duration-300 ease-out
        ${exiting ? "translate-x-full opacity-0" : "translate-x-0 opacity-100"}
        ${STYLES[type] || STYLES.info}
      `}
      role="alert"
    >
      <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${ICON_COLORS[type] || ICON_COLORS.info}`} />
      <div className="flex-1 text-sm font-medium leading-relaxed pr-2">
        {message}
      </div>
      <button
        onClick={handleClose}
        className="flex-shrink-0 p-0.5 rounded-lg hover:bg-black/5 transition-colors"
        aria-label="Dismiss"
      >
        <X className="w-4 h-4 opacity-60" />
      </button>
      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 h-0.5 bg-black/5 w-full">
        <div
          className={`h-full ${PROGRESS_COLORS[type] || PROGRESS_COLORS.info} transition-none`}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
