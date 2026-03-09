"""
Calendar MCP Server
───────────────────
Model Context Protocol tool for calendar operations.

Production: Integrates with Google Calendar API via google-api-python-client.
Demo mode: Logs actions without modifying any calendar.

Setup:
  1. Enable Google Calendar API in Google Cloud Console
  2. Download credentials.json (OAuth 2.0)
  3. Set GOOGLE_CALENDAR_CREDENTIALS_PATH in .env
"""

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from utils.logger import get_logger

log = get_logger("mcp.calendar")

CREDENTIALS_PATH = os.getenv("GOOGLE_CALENDAR_CREDENTIALS_PATH", "")
CALENDAR_ID      = os.getenv("GOOGLE_CALENDAR_ID", "primary")
DEMO_MODE        = not CREDENTIALS_PATH


# ── Public MCP Tool Functions ─────────────────────────────────────────────────

def create_event(
    title: str,
    description: str = "",
    start_time: str = "",
    end_time: str = "",
    attendees: Optional[list[str]] = None,
    location: str = "",
) -> dict:
    """
    Create a calendar event.

    Args:
        title: Event title
        description: Event description
        start_time: ISO 8601 string (defaults to now + 1 hour)
        end_time: ISO 8601 string (defaults to start + 1 hour)
        attendees: List of email addresses to invite
        location: Event location

    Returns:
        {"success": bool, "event_id": str, "link": str}
    """
    now = datetime.now(timezone.utc)
    start_dt = start_time or (now + timedelta(hours=1)).isoformat()
    end_dt   = end_time   or (now + timedelta(hours=2)).isoformat()

    if DEMO_MODE:
        log.info(f"[DEMO] Would create event: '{title}' at {start_dt}")
        return {
            "success": True,
            "event_id": "demo_event_001",
            "link": "https://calendar.google.com/[DEMO]",
        }

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        service = build("calendar", "v3", credentials=creds)

        event_body = {
            "summary":     title,
            "description": description,
            "location":    location,
            "start": {"dateTime": start_dt, "timeZone": "UTC"},
            "end":   {"dateTime": end_dt,   "timeZone": "UTC"},
        }
        if attendees:
            event_body["attendees"] = [{"email": a} for a in attendees]

        result = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event_body,
            sendUpdates="all" if attendees else "none",
        ).execute()

        log.info(f"Event created: {result['id']} — {title}")
        return {
            "success":  True,
            "event_id": result["id"],
            "link":     result.get("htmlLink", ""),
        }
    except Exception as e:
        log.error(f"Calendar event creation failed: {e}")
        return {"success": False, "event_id": "", "link": str(e)}


def list_events(days_ahead: int = 7, max_results: int = 10) -> list[dict]:
    """
    List upcoming calendar events.

    Returns:
        List of event dicts with keys: id, title, start, end, attendees
    """
    if DEMO_MODE:
        now = datetime.now(timezone.utc)
        log.info(f"[DEMO] Would list events for next {days_ahead} days")
        return [
            {
                "id":        "demo_event_001",
                "title":     "Team Standup",
                "start":     (now + timedelta(hours=2)).isoformat(),
                "end":       (now + timedelta(hours=2, minutes=30)).isoformat(),
                "attendees": ["team@example.com"],
            }
        ]

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
        )
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(timezone.utc)
        time_max = (now + timedelta(days=days_ahead)).isoformat()

        result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=now.isoformat(),
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = []
        for item in result.get("items", []):
            events.append({
                "id":        item["id"],
                "title":     item.get("summary", ""),
                "start":     item["start"].get("dateTime", item["start"].get("date", "")),
                "end":       item["end"].get("dateTime",   item["end"].get("date", "")),
                "attendees": [a["email"] for a in item.get("attendees", [])],
            })
        return events
    except Exception as e:
        log.error(f"Failed to list events: {e}")
        return []


def delete_event(event_id: str) -> dict:
    """
    Delete a calendar event by ID.

    Returns:
        {"success": bool, "message": str}
    """
    if DEMO_MODE:
        log.info(f"[DEMO] Would delete event: {event_id}")
        return {"success": True, "message": f"[DEMO] Event {event_id} deleted"}

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            CREDENTIALS_PATH,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
        log.info(f"Event deleted: {event_id}")
        return {"success": True, "message": f"Event {event_id} deleted"}
    except Exception as e:
        log.error(f"Failed to delete event {event_id}: {e}")
        return {"success": False, "message": str(e)}
