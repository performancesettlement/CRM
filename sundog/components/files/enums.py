from sundog.models import NONE_CHOICE_LABEL


TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('document', 'Document'),
    ('image', 'Image'),
    ('misc', 'Misc'),
    ('video', 'Video'),
)

TYPE_CHOICES_DICT = dict(TYPE_CHOICES)
