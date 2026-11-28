from database.db_collections import registrations
from bson import ObjectId

def update_registration(registration_id, updated_data):
    return registrations.update_one(
        { "_id": ObjectId(registration_id) },
        { "$set": updated_data }
    )