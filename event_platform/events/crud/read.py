from database.db_collections import events
from bson import ObjectId

def get_all_events():
    return list(events.find())

def get_event_by_id(event_id):
    return events.find_one({
        "_id": ObjectId(event_id)
    })

def get_events_by_organization(org_id):
    return list(events.find({
        "organizationID": ObjectId(org_id)
    }))