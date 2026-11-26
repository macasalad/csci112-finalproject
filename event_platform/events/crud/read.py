from database.db_collections import events, registrations, participants
from bson import ObjectId
import re

def get_all_events():
    return list(events.find({
        "status": { "$ne": "Cancelled" }
    }))

def get_event_by_id(event_id):
    return events.find_one({
        "_id": ObjectId(event_id)
    })

def get_events_by_organization(org_id, filters=None):
    if filters is None:
        filters = {}

    query = { "organizationID": ObjectId(org_id) }
    date_filter = {}

    if filters.get('search'):
        query['eventName'] = {
            '$regex': re.escape(filters['search']),
            '$options': 'i'
        }

    if filters.get('eventType'):
        query['eventType'] = filters['eventType']

    if filters.get('min_date'):
        date_filter['$gte'] = filters['min_date']

    if filters.get('max_date'):
        date_filter['$lt'] = filters['max_date']

    if date_filter:
        query['startTime'] = date_filter

    if filters.get('openToAll') == 'yes':
        query['openToAll'] = True
    elif filters.get('openToAll') == 'no':
        query['openToAll'] = False

    if filters.get('notDone'):
        query['status'] = {
            '$nin': ['Cancelled', 'Completed']
        }

    sort_options = {
        'date_asc': ('startTime', 1),
        'date_desc': ('startTime', -1),
        'name_asc': ('eventName', 1),
        'name_desc': ('eventName', -1)
    }

    sort_field, sort_order = sort_options.get(
        filters.get('sort'),
        ('startTime', 1)
    )
    
    return list(events.find(query).sort(sort_field, sort_order))

def get_event_participants(event_id):
    registered = list(registrations.find({
        "eventID": ObjectId(event_id)
    }))

    participant_ids = [
        registration['participantID']
        for registration in registered
    ]

    return list(participants.find({
        "_id": { "$in": participant_ids }
    }))

def get_upcoming_events():
    return list(events.find({"status": "Upcoming"}))
