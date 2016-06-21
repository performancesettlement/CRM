ERROR_GET_AREAS = "An error occurred trying to get the areas for the state: %s"
ERROR_GET_FILES = "An error occurred trying to get the files"
ERROR_GET_FILES_STATUS = "An error occurred trying to get the status list"
ERROR_GET_COMMUNITIES = "An error occurred trying to get the communities for the area: %s"
ERROR_GET_COMPLETED_BY_STATUS = "An error occurred trying to get the completed percentage for the status id: %s"
ERROR_SAVE_FILE_HISTORY = "An error occurred trying to save the file status history for the file id: %s"
ERROR_SAVE_FILE_ACCESS_HISTORY = "An error occurred trying to save the file access history for the file id: %s and the user: %s"
ERROR_GET_FILE_ACCESS_HISTORY = "An error occurred trying to get the file access history for the user: %s"
ERROR_GET_FILE = "An error occurred trying to get the file by id: %s for the user: %s"
ERROR_GET_DOCUMENTS = "An error occurred trying to get the documents for the file id: %s"
ERROR_CREATE_STATUS_PERMISSION = "An error occurred trying to create the permission for the status: %s"
ERROR_CREATE_FILE_PERMISSION = "An error occurred trying to create the permission for the file: %s"
ERROR_MODIFY_STATUS_PERMISSION = "An error occurred trying to modify the permission for the status: %s"
ERROR_GET_STATUS_PERMISSIONS = "An error occurred trying to get the status permissions for the user: %s"
ERROR_GET_PARTICIPANT_OPTIONS = "An error occurred trying to get the new participant options for the file id: %s"
ERROR_GET_USERS_BY_IDS = "An error occurred trying to get a list of user from the ids: %s"
ERROR_USER_NONE = "An error occurred. The user is None"
MESSAGE_REQUEST_FAILED = "Your request couldn't be processed, please try again."
ERROR_VALIDATE_IMPORT_HEADER = "An error occurred trying to get the header: %s"
ERROR_VALIDATE_NUMBER_HEADERS = "The number of headers found is not correct. There should be %d columns, " \
                                "and %d were found."
ERROR_IMPORT_FILE = "An error occurred trying to import files for the user: %s"
ERROR_IMPORT_CLIENTS = "An error occurred trying to import clients for the user: %s"
ERROR_SAVE_FILE_IMPORT_HISTORY = "An error occurred trying to save the import file history for the user: %s"
CHECK_MODEL_EXISTS_IN_DB = "An error occurred trying to get the id for the model %s passing the name: %s"
ERROR_VALIDATE_IMPORT_CELL_EXISTS_DB = "Row: %d. The field %s must exist already in the system."
ERROR_VALIDATE_IMPORT_CELL_NOT_EMPTY = "Row: %d. The field %s cannot be empty."
ERROR_VALIDATE_IMPORT_CELL_VALID_TYPE = "Row: %d. The field %s is not a valid %s."
ERROR_VALIDATE_IMPORT_CELL_UNIQUE = "Row: %d. The field %s must be unique."
ERROR_GET_IMPORT_DEFAULT_STATUS = "The default file status couldn't be retrieve."
ERROR_FILE_IMPORT_NO_ROWS = "No files to import."
ERROR_CLIENT_IMPORT_NO_ROWS = "No clients to import."
ERROR_GET_SEED_FILE = "An error occurred trying to get the seed file id from the config model"
ERROR_GET_PROFILE = "An error occurred trying to get the user %s profile"
ERROR_GET_RECOVER_KEY = "An error occurred trying to create the recover key for the user: %s"
ERROR_PARTICIPANTS_CHANGED = "The file participants have been modified by another user, The screen has been reloaded."

MESSAGE_REQUEST_FAILED_CODE = 1
ERROR_PARTICIPANTS_CHANGED_CODE = 2

CODES_TO_MESSAGE = {
    0: None,
    MESSAGE_REQUEST_FAILED_CODE: MESSAGE_REQUEST_FAILED,
    ERROR_PARTICIPANTS_CHANGED_CODE: ERROR_PARTICIPANTS_CHANGED
}
