from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
from bson import ObjectId
from accounts.crud.read import get_participant_by_id, get_organizer_by_id
from events.crud.read import get_event_by_id
from events.crud.update import add_participant_count, remove_participant_count
from .crud.create import create_registration
from .crud.read import get_registration
from .crud.update import update_registration


def go_back(request):
    # Return to the page the button was on (Discover or My events)
    if request.POST.get('next') == 'org_event_list':
        return redirect('org_event_list')
    return redirect('event_list')

def enlist_view(request, event_id):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.session.get('role') != 'participant':
        messages.error(request, 'Only students can enlist in events.')
        return redirect('event_list')

    if request.method != 'POST':
        return redirect('event_list')

    participant_id = request.session.get('profile_id')
    event = get_event_by_id(event_id)
    registration = get_registration(event_id, participant_id)

    if not event or event['status'] != 'Upcoming':
        messages.error(request, 'This event is no longer open for enlistment.')
        return go_back(request)

    if registration and registration['status'] == 'Registered':
        messages.error(request, 'You are already enlisted in this event.')
        return go_back(request)

    if not event.get('openToAll'):
        organizer = get_organizer_by_id(event['organizationID'])
        participant = get_participant_by_id(participant_id)

        if organizer['organizationName'] not in participant.get('organizations', []):
            messages.error(request, f"Only members of {organizer['organizationName']} can enlist in this event.")
            return go_back(request)

    # Only adds a seat if the event is still Upcoming and not full
    if add_participant_count(event_id).modified_count == 0:
        messages.error(request, 'This event is already full.')
        return go_back(request)

    if registration:
        # Enlisting again after delisting: reuse the same registration
        update_registration(registration['_id'], {
            'status': 'Registered',
            'registeredAt': timezone.now(),
            'cancelledAt': None
        })
    else:
        create_registration({
            'eventId': ObjectId(event_id),
            'participantId': ObjectId(participant_id),
            'status': 'Registered',
            'registeredAt': timezone.now(),
            'cancelledAt': None
        })

    messages.success(request, f"You are now enlisted in {event['eventName']}.")
    return go_back(request)

def delist_view(request, event_id):
    if not request.session.get('user_id'):
        return redirect('login')

    if request.method != 'POST':
        return redirect('event_list')

    participant_id = request.session.get('profile_id')
    event = get_event_by_id(event_id)
    registration = get_registration(event_id, participant_id)

    if not registration or registration['status'] != 'Registered':
        messages.error(request, 'You are not enlisted in this event.')
        return go_back(request)

    if not event or event['status'] != 'Upcoming':
        messages.error(request, 'You can no longer delist from this event.')
        return go_back(request)

    update_registration(registration['_id'], {
        'status': 'Cancelled',
        'cancelledAt': timezone.now()
    })
    remove_participant_count(event_id)

    messages.success(request, f"You have delisted from {event['eventName']}.")
    return go_back(request)