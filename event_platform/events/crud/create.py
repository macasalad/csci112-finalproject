from database.db_collections import events

def create_event(event_data):
    return events.insert_one(event_data)