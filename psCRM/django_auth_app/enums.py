__author__ = 'Gaby'
from localflavor.us.us_states import US_STATES
from timezone_utils.choices import PRETTY_COMMON_TIMEZONES_CHOICES

GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
    ('O', 'Other')
)

US_STATES_I = list(US_STATES)
US_STATES_I.insert(0, ("", "Select the state of interest..."))
US_STATES_I = tuple(US_STATES_I)

US_STATES_R = list(US_STATES)
US_STATES_R.insert(0, ("", "Select the state of residence..."))
US_STATES_R = tuple(US_STATES_R)

FORMATTED_TIMEZONES = PRETTY_COMMON_TIMEZONES_CHOICES
