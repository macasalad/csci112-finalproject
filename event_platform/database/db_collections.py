from database.db_utils import open_connection, close_connection

conn = open_connection()
db = conn['dev-events-db']

users = db['users']
participants = db['participants']
organizers = db['organizers']
events = db['events']
registrations = db['registrations']