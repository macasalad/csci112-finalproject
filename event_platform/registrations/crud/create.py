from database.db_collections import registrations

def create_registration(registration_data):
    return registrations.insert_one(registration_data)