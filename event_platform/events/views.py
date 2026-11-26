from datetime import datetime, timedelta, timezone as dt_timezone

from bson import ObjectId
from bson.errors import InvalidId
from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from django.utils import timezone

from accounts.crud.read import get_organizer_by_id
from .crud.create import create_event
from .crud.read import (
    get_event_by_id,
    get_upcoming_events,
    get_events_by_organization,
    get_registered_events,
    get_registered_event_ids,
    get_event_participants
)
from .crud.update import update_event, update_event_statuses
from .form_choices import STATUSES, TYPES


# ---------- Helpers ----------

def to_local(value):
    # PyMongo returns naive UTC datetimes. Convert them to local time.
    if timezone.is_naive(value):
        value = value.replace(tzinfo=dt_timezone.utc)
    return timezone.localtime(value)


def _fmt_time(value):
    return value.strftime('%I:%M %p').lstrip('0')   # "1:00 PM"


def _initials(name):
    letters = "".join(word[0] for word in name.split() if word[:1].isupper())
    return letters[:6] or "ORG"


def _card(doc, enlisted_ids=frozenset(), org_cache=None):
    """
    Turns an event document into the fields an event card needs.
    Discover (JavaScript) and My events (Django template) use the same fields,
    so the cards on both pages look the same.
    """
    org_cache = {} if org_cache is None else org_cache
    org_id = doc.get('organizationID')
    if org_id not in org_cache:
        org_cache[org_id] = (get_organizer_by_id(org_id) if org_id else None) or {}
    org_name = org_cache[org_id].get('organizationName', '')

    start = to_local(doc['startTime'])
    end = to_local(doc['endTime'])
    capacity = doc.get('maxParticipants') or 0
    taken = doc.get('currentParticipants') or 0
    pct = round(taken / capacity * 100) if capacity else 0
    event_type = doc.get('eventType', '')

    return {
        'id': str(doc['_id']),
        'org': _initials(org_name),
        'orgName': org_name,
        'type': event_type,
        'typeClass': event_type.lower().replace(' ', '-'),
        'status': doc.get('status', ''),
        'date': start.strftime('%Y-%m-%d'),
        'month': start.strftime('%b').upper(),
        'day': start.strftime('%d'),
        'year': start.year,
        'start': _fmt_time(start),
        'end': _fmt_time(end),
        'start_full': f"{start:%a, %b} {start.day}, {start.year} · {_fmt_time(start)}",   # Thu, Dec 3, 2026 · 1:00 PM
        'end_full': f"{end:%a, %b} {end.day}, {end.year} · {_fmt_time(end)}",
        'title': doc.get('eventName', ''),
        'desc': doc.get('description', ''),
        'venue': doc.get('location', ''),
        'audience': 'Open to all Ateneans' if doc.get('openToAll') else 'Members only',
        'capacity': capacity,
        'taken': taken,
        'left': max(capacity - taken, 0),
        'pct': pct,
        'bar': min(pct, 100),
        'full': capacity > 0 and taken >= capacity,
        'enlisted': doc['_id'] in enlisted_ids,
    }


def _filters_from_request(request):
    filters = {
        'search': request.GET.get('search', '').strip(),
        'eventType': request.GET.get('eventType', ''),
        'openToAll': request.GET.get('openToAll', ''),
        'notDone': request.GET.get('notDone') == 'on',
        'sort': request.GET.get('sort', 'date_asc')
    }

    min_date = request.GET.get('min_date', '')
    max_date = request.GET.get('max_date', '')
    try:
        if min_date:
            filters['min_date'] = timezone.make_aware(datetime.strptime(min_date, '%Y-%m-%d'))
    except ValueError:
        min_date = ''
    try:
        if max_date:
            filters['max_date'] = timezone.make_aware(
                datetime.strptime(max_date, '%Y-%m-%d') + timedelta(days=1)
            )
    except ValueError:
        max_date = ''

    return filters, min_date, max_date


# ---------- Discover ----------

def event_list(request):
    if not request.session.get('user_id'):
        return redirect('login')

    update_event_statuses()

    role = request.session.get('role')
    profile_id = request.session.get('profile_id')
    enlisted = get_registered_event_ids(profile_id) if role == 'participant' else set()

    org_cache = {}
    cards = [_card(doc, enlisted, org_cache) for doc in get_upcoming_events()]

    return render(request, 'events/event_list.html', {
        'events_data': cards,
        'can_enlist': role == 'participant',
    })


# ---------- My events (organizers AND participants) ----------
# URL name stays 'org_event_list' so existing redirects keep working.

def org_event_list_view(request):
    if not request.session.get('user_id'):
        return redirect('login')

    update_event_statuses()

    role = request.session.get('role')
    profile_id = request.session.get('profile_id')
    is_organizer = role == 'organizer'
    filters, min_date, max_date = _filters_from_request(request)

    if is_organizer:
        docs = get_events_by_organization(profile_id, filters)
    else:
        docs = get_registered_events(profile_id, filters)

    enlisted = {doc['_id'] for doc in docs} if not is_organizer else set()
    org_cache = {}
    cards = [_card(doc, enlisted, org_cache) for doc in docs]

    has_filters = bool(
        filters['search'] or filters['eventType'] or filters['openToAll']
        or filters['notDone'] or min_date or max_date
    )

    return render(request, 'events/my_events.html', {
        'events': cards,
        'is_organizer': is_organizer,
        'types': TYPES,
        'filters': filters,
        'min_date': min_date,
        'max_date': max_date,
        'has_filters': has_filters,
    })


# ---------- Organizer: create / edit / cancel ----------

def _parse_event_form(request):
    """
    Reads the create/edit form. Returns (data, error).
    A blank or invalid field gives an error message instead of a crash.
    """
    try:
        start_time = timezone.make_aware(datetime.strptime(request.POST.get('startTime', ''), '%Y-%m-%dT%H:%M'))
        end_time = timezone.make_aware(datetime.strptime(request.POST.get('endTime', ''), '%Y-%m-%dT%H:%M'))
    except ValueError:
        return None, 'Please enter a valid start and end date and time.'

    try:
        max_participants = int(request.POST.get('maxParticipants', ''))
    except ValueError:
        return None, 'Maximum participants must be a whole number.'

    data = {
        'eventName': request.POST.get('title', '').strip(),
        'description': request.POST.get('description', '').strip(),
        'startTime': start_time,
        'endTime': end_time,
        'location': request.POST.get('venue', '').strip(),
        'eventType': request.POST.get('type', '').strip(),
        'maxParticipants': max_participants,
        'openToAll': request.POST.get('openToAll') == 'on',
    }

    if not all([data['eventName'], data['description'], data['location'], data['eventType']]):
        return None, 'Please fill in all fields.'
    if max_participants < 1:
        return None, 'Maximum participants must be at least 1.'
    if start_time < timezone.localtime():
        return None, 'Start time cannot be in the past.'
    if end_time <= start_time:
        return None, 'End time must be later than start time.'

    return data, None


def create_event_view(request):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('role') != 'organizer':
        messages.error(request, 'Only organizers can host events.')
        return redirect('event_list')

    if request.method == 'POST':
        data, error = _parse_event_form(request)
        if error:
            messages.error(request, error)
        else:
            create_event({
                **data,
                'currentParticipants': 0,
                'organizationID': ObjectId(request.session.get('profile_id')),
                'status': 'Upcoming'
            })
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
        data, error = _parse_event_form(request)
        if error:
            messages.error(request, error)
        else:
            update_event(event_id, {**data, 'status': request.POST.get('status') or event.get('status')})
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

def event_detail_view(request, event_id):
    if not request.session.get('user_id'):
        return redirect('login')

    update_event_statuses()

    try:
        event = get_event_by_id(event_id)
    except InvalidId as exc:
        raise Http404("Event not found") from exc
    if event is None:
        raise Http404("Event not found")

    is_owner = (
        request.session.get('role') == 'organizer'
        and str(event.get('organizationID')) == request.session.get('profile_id')
    )
    participants = get_event_participants(event_id) if is_owner else []

    return render(request, 'events/event_detail.html', {
        'event': event,
        'card': _card(event),
        'event_id': event_id,
        'is_owner': is_owner,
        'participants': participants,
    })