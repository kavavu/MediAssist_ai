import React from "react";
import { FileSearch, Inbox, Calendar, FlaskConical, Pill, Users, MessageSquare } from "lucide-react";

const ICONS = {
  search: FileSearch,
  inbox: Inbox,
  calendar: Calendar,
  lab: FlaskConical,
  medicine: Pill,
  users: Users,
  chat: MessageSquare,
};

export default function EmptyState({
  icon = "inbox",
  title = "No data available",
  description = "There is nothing to display at the moment.",
  action = null,
}) {
  const Icon = ICONS[icon] || Inbox;

  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-slate-400" />
      </div>
      <h3 className="text-lg font-semibold text-slate-700 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-xs mb-5">{description}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
