from database.db_collections import participants, organizers, users
from bson import ObjectId

def update_participant(participant_id, updated_data):
    return participants.update_one(
        {"_id": ObjectId(participant_id)},
        {"$set": updated_data}
    )

def update_organizer(organizer_id, updated_data):
    return organizers.update_one(
        {"_id": ObjectId(organizer_id)},
        {"$set": updated_data}
    )

def update_user(user_id, updated_data):
    return users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updated_data}
    )