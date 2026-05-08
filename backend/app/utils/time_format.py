"""
Human-readable timestamp formatting.

Examples:
    - "Just now"
    - "5 minutes ago"
    - "2 hours ago"
    - "Yesterday"
    - "3 days ago"
    - "Jan 15, 2026"
"""
from datetime import datetime, timezone
from typing import Optional


def format_time_ago(dt: Optional[datetime]) -> str:
    """
    Format a datetime as a human-readable relative string.
    Returns empty string if dt is None.
    """
    if dt is None:
        return ""

    # Ensure both are timezone-aware or both naive
    now = datetime.utcnow()
    if dt.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    elif dt.tzinfo is None and now.tzinfo is not None:
        dt = dt.replace(tzinfo=timezone.utc)

    diff = now - dt
    total_seconds = int(diff.total_seconds())

    if total_seconds < 0:
        return "Just now"

    if total_seconds < 60:
        return "Just now"
    if total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    if total_seconds < 7200:
        return "1 hour ago"
    if total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours} hours ago"
    if total_seconds < 172800:
        return "Yesterday"
    if total_seconds < 604800:
        days = total_seconds // 86400
        return f"{days} days ago"

    # Older than a week — show date
    return dt.strftime("%b %d, %Y")
