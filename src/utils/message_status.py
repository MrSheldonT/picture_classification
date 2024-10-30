from enum import Enum

class Status(Enum):
    NOT_ENTERED = "Parameters not entered"
    SUCCESSFULLY_UPDATED = 'Successfully updated'
    SUCCESSFULLY_DELETED = 'Successfully deleted'
    SUCCESSFULLY_CREATED = 'Successfully created'
    SUCCESSFULLY_READ = 'Successfully read'
    RECORD_NOT_FOUND = 'The requested record was not found, please check again'
    SUCCESSFULLY_CONSULTED =  'Consulted correctly'
