from database.db_collections import events, registrations
from bson import ObjectId
import re

SORT_OPTIONS = {
    'date_asc': ('startTime', 1),
    'date_desc': ('startTime', -1),
    'name_asc': ('eventName', 1),
    'name_desc': ('eventName', -1)
}

def get_all_events():
    return list(events.aggregate([
        { "$match": { "status": { "$ne": "Cancelled" } } }
    ]))

def get_event_by_id(event_id):
    return events.find_one({
        "_id": ObjectId(event_id)
    })

def get_upcoming_events():
    return list(events.aggregate([
        {
            "$match": {
                "status": "Upcoming"
            } 
        },
        {
            "$sort": {
                "startTime": 1
            }
        }
    ]))

def _filter_stages(filters=None):
    filters = filters or {}
    match = {}
    date_filter = {}

    if filters.get('search'):
        match['eventName'] = {
            '$regex': re.escape(filters['search']),
            '$options': 'i'
        }

    if filters.get('eventType'):
        match['eventType'] = filters['eventType']

    if filters.get('min_date'):
        date_filter['$gte'] = filters['min_date']

    if filters.get('max_date'):
        date_filter['$lt'] = filters['max_date']

    if date_filter:
        match['startTime'] = date_filter

    if filters.get('openToAll') == 'yes':
        match['openToAll'] = True
    elif filters.get('openToAll') == 'no':
        match['openToAll'] = False

    if filters.get('notDone'):
        match['status'] = {
            '$nin': ['Cancelled', 'Completed']
        }

    sort_field, sort_order = SORT_OPTIONS.get(filters.get('sort'), ('startTime', 1))

    return [
        {
            "$match": match
        },
        {
            "$sort": { 
                sort_field: sort_order
            }
        }
    ]

def get_events_by_organization(org_id, filters=None):
    return list(events.aggregate([
        {
            "$match": {
                "organizationID": ObjectId(org_id)
            }
        }] + _filter_stages(filters)))

def get_registered_events(participant_id, filters=None):
    return list(registrations.aggregate([
        {
            "$match": {
                "participantId": ObjectId(participant_id),
                "status": "Registered" 
            }
        },
        { 
            "$lookup": {
                "from": "events",
                "localField": "eventId",
                "foreignField": "_id",
                "as": "event"
            }
        },
        {
            "$unwind": "$event"
        },
        {
            "$project": {
                "_id": "$event._id",
                "eventName": "$event.eventName",
                "description": "$event.description",
                "eventType": "$event.eventType",
                "startTime": "$event.startTime",
                "endTime": "$event.endTime",
                "location": "$event.location",
                "maxParticipants": "$event.maxParticipants",
                "currentParticipants": "$event.currentParticipants",
                "openToAll": "$event.openToAll",
                "organizationID": "$event.organizationID",
                "status": "$event.status"
            }
        }] + _filter_stages(filters)))