from database.db_collections import events
from django.utils import timezone
from bson import ObjectId

def update_event(event_id, updated_data):
    return events.update_one(
        { "_id": ObjectId(event_id) },
        { "$set": updated_data }
    )

def update_event_statuses():
    now = timezone.now()

    events.update_many(
        {
            'startTime': { '$lte': now },
            'endTime': { '$gt': now },
            'status': { '$ne': 'Cancelled' }
        },
        { '$set': { 'status': 'Ongoing' } }
    )

    events.update_many(
        {
            'endTime': { '$lte': now },
            'status': { '$ne': 'Cancelled' }
        },
        { '$set': { 'status': 'Completed' } }
    )

def add_participant_count(event_id):
    return events.update_one(
        {
            "_id": ObjectId(event_id),
            "status": "Upcoming",
            "$expr": { "$lt": [ { "$ifNull": ["$currentParticipants", 0] }, "$maxParticipants" ] }
        },
        { "$inc": { "currentParticipants": 1 } }
    )

def remove_participant_count(event_id):
    return events.update_one(
        { "_id": ObjectId(event_id), "currentParticipants": { "$gt": 0 } },
        { "$inc": { "currentParticipants": -1 } }
    )