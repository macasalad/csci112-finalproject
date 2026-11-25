from database.db_collections import events
from bson import ObjectId


def delete_event(event_id):
    return events.delete_one({ "_id": ObjectId(event_id) })
