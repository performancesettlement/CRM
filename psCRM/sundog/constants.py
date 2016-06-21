SHORT_DATE_FORMAT = "%m/%d/%Y"
CACHE_IMPORT_EXPIRATION = 30
STATUS_CODENAME_PREFIX = 'can_use_status_'

COLOR_CHOICES = (
    ('', 'Plain Gray'),
    ('label-primary', 'Green'),
    ('label-information', 'Light Blue'),
    ('label-success', 'Electric Blue'),
    ('label-warning', 'Orange'),
    ('label-danger', 'Red'),
)

PRIORITY_CHOICES = (
    (4, 'Top priority'),
    (3, 'High priority'),
    (2, 'Moderate priority'),
    (1, 'Low priority'),
)

RADIO_FILTER_CHOICES = (
    ('0', 'All Files'),
    ('1', 'Participant Only'),
)

PRIORITY_COLOR_CHOICES = (
    (4, 'text-danger'),
    (3, 'text-warning'),
    (2, 'text-success'),
    (1, 'text-info'),
)

IMPORT_FILE_EXCEL_HEADERS = [
    'DESCRIPTION',
    'STATUS',
    'CLIENT',
    'PRIORITY',
    'QUOTED PRICE',
    'QUOTED DATE',
    'INVOICE PRICE',
    'INVOICE DATE',
    'PARTICIPANT1',
    'PARTICIPANT2',
    'TAG1',
    'TAG2',
    'TAG3',
    'TAG4',
    'TAG5'
]

IMPORT_CLIENT_EXCEL_HEADERS = [
    'CLIENT TYPE',
    'CLIENT NAME',
    'IDENTIFICATION',
    'EMAIL',
    'PHONE NUMBER',
    'MOBILE NUMBER',
    'COUNTRY',
    'STATE',
    'CITY',
    'ZIP CODE',
    'ADDRESS',
    'RELATED USER'
]

IMPORT_FILE_EXCEL_FILENAME = 'FileImport.xlsx'
IMPORT_CLIENT_EXCEL_FILENAME = 'ClientImport.xlsx'
