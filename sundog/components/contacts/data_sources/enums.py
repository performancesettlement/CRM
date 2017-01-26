from sundog.models import (
    DEBT_SETTLEMENT,
    STUDENT_LOANS,
)


DATA_SOURCE_FILE_TYPE_CHOICES = (
    (DEBT_SETTLEMENT, 'Debt Settlement'),
    (STUDENT_LOANS, 'Student Loans'),
)


DATA_SOURCE_TYPE_CHOICES = (
    ('web_form', 'Web Form'),
    ('import', 'Import'),
)
