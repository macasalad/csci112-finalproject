from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .crud.create import create_event
from .crud.read import (
    get_all_events,
    get_event_by_id,
    get_events_by_organization,
    get_event_participants
)
from .crud.update import update_event, update_event_statuses
from .form_choices import STATUSES, TYPES
from datetime import datetime, timedelta
from bson import ObjectId


def to_local(value):
    # PyMongo returns datetimes that are in UTC. convert them to local time.
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.utc)
    return timezone.localtime(value)


def event_list(request):
    update_event_statuses()
    event_list = get_all_events()

    return render(
        request,
        "events/event_list.html",
        {"events": event_list}
    )

def create_event_view(request):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('role') != 'organizer':
        messages.error(request, 'Only organizers can create events.')
        return redirect('home')

    if request.method == 'POST':
        start_time = timezone.make_aware(datetime.strptime(
            request.POST.get('startTime'),
            '%Y-%m-%dT%H:%M'
        ))
        end_time = timezone.make_aware(datetime.strptime(
            request.POST.get('endTime'),
            '%Y-%m-%dT%H:%M'
        ))

        if start_time < timezone.localtime():
            messages.error(request, 'Start time cannot be in the past.')
        elif end_time < start_time:
            messages.error(request, 'End time cannot be earlier than start time.')
        else:
            event = {
                'eventName': request.POST.get('title', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'startTime': start_time,
                'endTime': end_time,
                'location': request.POST.get('venue', '').strip(),
                'eventType': request.POST.get('type', '').strip(),
                'maxParticipants': int(request.POST.get('maxParticipants')),
                'currentParticipants': 0,
                'openToAll': request.POST.get('openToAll') == 'on',
                'organizationID': ObjectId(request.session.get('profile_id')),
                'status': 'Upcoming'
            }

            create_event(event)
            messages.success(request, 'Event created successfully.')
            return redirect('org_event_list')

    return render(request, 'events/create_event.html', {
        'statuses': STATUSES,
        'types': TYPES
    })

def edit_event_view(request, event_id):
    if not request.session.get('user_id'):
            return redirect('login')
    
    event = get_event_by_id(event_id)
    if event['organizationID'] != ObjectId(request.session.get('profile_id')):
        messages.error(request, 'You cannot edit this event.')
        return redirect('event_list')

    if request.method == 'POST':
        start_time = timezone.make_aware(datetime.strptime(
            request.POST.get('startTime'),
            '%Y-%m-%dT%H:%M'
        ))
        end_time = timezone.make_aware(datetime.strptime(
            request.POST.get('endTime'),
            '%Y-%m-%dT%H:%M'
        ))

        if start_time < timezone.localtime():
            messages.error(request, 'Start time cannot be in the past.')
        elif end_time < start_time:
            messages.error(request, 'End time cannot be earlier than start time.')
        else:
            updated_data = {
                'eventName': request.POST.get('title', '').strip(),
                'description': request.POST.get('description', '').strip(),
                'startTime': start_time,
                'endTime': end_time,
                'location': request.POST.get('venue', '').strip(),
                'eventType': request.POST.get('type', '').strip(),
                'maxParticipants': int(request.POST.get('maxParticipants')),
                'openToAll': request.POST.get('openToAll') == 'on',
                'status': request.POST.get('status')
            }

            update_event(event_id, updated_data)
            messages.success(request, 'Event updated successfully.')
            return redirect('event_detail', event_id=event_id)

    return render(request, 'events/edit_event.html', {
        'event': event,
        'types': TYPES,
        'statuses': STATUSES,
        'start_time': to_local(event['startTime']).strftime('%Y-%m-%dT%H:%M'),
        'end_time': to_local(event['endTime']).strftime('%Y-%m-%dT%H:%M'),
        'event_id': event_id
    })

def cancel_event_view(request, event_id):
    if not request.session.get('user_id'):
        return redirect('login')

    event = get_event_by_id(event_id)

    if event['organizationID'] != ObjectId(request.session.get('profile_id')):
        messages.error(request, 'You cannot cancel this event.')
        return redirect('org_event_list')

    if request.method == 'POST':
        update_event(event_id, { "status": "Cancelled" })
        messages.success(request, 'Event cancelled successfully.')

    return redirect('org_event_list')

def org_event_list_view(request):
    update_event_statuses()

    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('role') != 'organizer':
        messages.error(request, 'Only organizers can view this page.')
        return redirect('home')

    filters = {
        'search': request.GET.get('search', '').strip(),
        'eventType': request.GET.get('eventType', ''),
        'openToAll': request.GET.get('openToAll', ''),
        'notDone': request.GET.get('notDone') == 'on',
        'sort': request.GET.get('sort', 'date_asc')
    }

    min_date = request.GET.get('min_date')
    if min_date:
        filters['min_date'] = timezone.make_aware(
            datetime.strptime(min_date, '%Y-%m-%d')
        )
    max_date = request.GET.get('max_date')
    if max_date:
        filters['max_date'] = timezone.make_aware(
            datetime.strptime(max_date, '%Y-%m-%d') + timedelta(days=1)
        )

    org_events = get_events_by_organization(request.session.get('profile_id'), filters)
    
    for event in org_events:
        event['event_id'] = str(event['_id'])
   
    return render(request, 'events/org_event_list.html', {
        'events': org_events,
        'types': TYPES,
        'filters': filters,
        'min_date': min_date or '',
        'max_date': max_date or ''
    })

def event_detail_view(request, event_id):
    update_event_statuses()

    event = get_event_by_id(event_id)
    participants = get_event_participants(event_id)

    return render(request, 'events/event_detail.html', {
        'event': event,
        'event_id': event_id,
        'participants': participants
    })
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
