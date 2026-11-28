from database.db_collections import participants, organizers, users

def create_participant(participant_data):
    return participants.insert_one(participant_data)

def create_organizer(organizer_data):
    return organizers.insert_one(organizer_data)

def create_user(user_data):
    return users.insert_one(user_data)