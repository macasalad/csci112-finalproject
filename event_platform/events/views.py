from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from django.http import Http404
from django.shortcuts import render

from accounts.crud.read import get_organizer_by_id
from .crud.read import get_event_by_id, get_upcoming_events


def _display_event(doc):
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title") or doc.get("eventName") or "",
        "description": doc.get("description") or "",
        "venue": doc.get("venue") or doc.get("location") or "",
        "status": doc["status"],
    }


def _event_time(value):
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        # PyMongo decodes BSON dates as naive UTC datetimes by default.
        return value.replace(tzinfo=timezone.utc)
    return value


def event_list(request):
    display_events = [_display_event(doc) for doc in get_upcoming_events()]
    return render(request, "events/event_list.html", {"events": display_events})


def event_detail(request, event_id):
    try:
        doc = get_event_by_id(event_id)
    except InvalidId as exc:
        raise Http404("Event not found") from exc

    if doc is None or doc.get("status") != "Upcoming":
        raise Http404("Event not found")

    organizer_id = doc.get("organizer")
    organizer = get_organizer_by_id(organizer_id) if ObjectId.is_valid(organizer_id) else None
    event = {
        **_display_event(doc),
        "start_time": _event_time(doc.get("startTime")),
        "end_time": _event_time(doc.get("endTime")),
        "host": organizer.get("organizationName") if organizer else None,
        "max_participants": doc.get("maxParticipants"),
        "current_participants": doc.get("currentParticipants"),
    }
    return render(request, "events/event_detail.html", {"event": event})
