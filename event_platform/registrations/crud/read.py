from database.db_collections import registrations, participants
from bson import ObjectId

def get_registration(event_id, participant_id):
    # Any status: a "Cancelled" one is reused if the student enlists again
    return registrations.find_one({
        "eventId": ObjectId(event_id),
        "participantId": ObjectId(participant_id)
    })

def get_registered_event_ids(participant_id):
    registered = registrations.find(
        { "participantId": ObjectId(participant_id), "status": "Registered" },
        { "eventId": 1 }
    )

    return { registration['eventId'] for registration in registered }

def get_event_participants(event_id):
    registered = list(registrations.find({
        "eventId": ObjectId(event_id),
        "status": "Registered"
    }).sort("registeredAt", 1))

    participant_ids = [
        registration['participantId']
        for registration in registered
    ]

    found = {
        participant['_id']: participant
        for participant in participants.find({ "_id": { "$in": participant_ids } })
    }

    # Keep the order people enlisted in, and show when each one enlisted
    return [
        { **found[registration['participantId']], 'registeredAt': registration.get('registeredAt') }
        for registration in registered
        if registration['participantId'] in found
    ]