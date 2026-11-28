from database.db_collections import registrations
from bson import ObjectId

def get_registration(event_id, participant_id):
    return registrations.find_one({
        "eventId": ObjectId(event_id),
        "participantId": ObjectId(participant_id)
    })

def get_registered_event_ids(participant_id):
    registered = registrations.aggregate([
        {
            "$match": {
                "participantId": ObjectId(participant_id),
                "status": "Registered" 
            }
        },
        {
            "$group": {
                "_id": "$eventId" 
            }
        }
    ])

    return { registration['_id'] for registration in registered }

def get_event_participants(event_id):
    return list(registrations.aggregate([
        {
            "$match": {
                "eventId": ObjectId(event_id),
                "status": "Registered" 
            } 
        },
        { 
            "$sort": {
                "registeredAt": 1 
            } 
        },
        { 
            "$lookup": {
                "from": "participants",
                "localField": "participantId",
                "foreignField": "_id",
                "as": "participant"
            }
        },
        { 
            "$unwind": "$participant"
        },
        {
            "$project": {
                "_id": "$participant._id",
                "firstName": "$participant.firstName",
                "lastName": "$participant.lastName",
                "idNumber": "$participant.idNumber",
                "course": "$participant.course",
                "year": "$participant.year",
                "email": "$participant.email",
                "registeredAt": 1
            }
        }
    ]))