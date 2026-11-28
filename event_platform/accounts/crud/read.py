from database.db_collections import participants, organizers, users
from bson import ObjectId

# Participants
def get_participant_by_id(participant_id):
    return participants.find_one({
        "_id": ObjectId(participant_id)
    })

def get_participant_by_student_id(id_number):
    return participants.find_one({
        "idNumber": id_number
    })

# Organizers
def get_organizer_by_id(organizer_id):
    return organizers.find_one({
        "_id": ObjectId(organizer_id)
    })

def get_organizer_by_name(organization_name):
    return organizers.find_one({
        "organizationName": organization_name
    })

# Users
def get_user_by_email(email):
    return users.find_one({
        "email": email
    })