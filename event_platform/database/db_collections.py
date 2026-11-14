from database.db_utils import open_connection, close_connection

conn = open_connection()
db = conn['events-db']

participants = db['participants']
organizers = db['organizers']
events = db['events']
registrations = db['organizers']