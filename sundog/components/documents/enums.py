from sundog.models import NONE_CHOICE_LABEL


TYPE_CHOICES = (
    (None, NONE_CHOICE_LABEL),
    ('1099c', '1099-C'),
    ('30_day_notice', '30 Day Notice (debt has moved)'),
    ('3rd_party_auth', '3rd Party Speaker Authorization'),
    ('ach_authorization', 'ACH Authorization'),
    ('auth_to_comm_with_cred', 'Auth. To Communicate w/ Creditors'),
    ('bank_statements', 'Bank Statements'),
    ('cancellation_letter', 'Cancellation Letter'),
    ('client_correspondence', 'Client Correspondence'),
    ('collector_correspondence', 'Collector Correspondence'),
    ('contract_agreement', 'Contract / Agreement'),
    ('creditor_correspondence', 'Creditor Correspondence'),
    ('credit_report', 'Credit Report'),
    ('custodial_document', 'Custodial Document'),
    ('general', 'General / Misc.'),
    ('hardship_notification', 'Hardship Notification Letter'),
    ('hardship_statement', 'Hardship Statement'),
    ('inc_exp_form', 'Inc/Exp Form'),
    ('legal_document', 'Legal Document'),
    ('legal_solicitation', 'Legal Solicitation Notice'),
    ('power_of_attorney', 'Power Of Attorney'),
    ('quality_control_rec', 'Quality Control Recording'),
    ('settlement_letter', 'Settlement Letter'),
    ('settlement_offer', 'Settlement Offer'),
    ('settlement_payment_confirmation', 'Settlement Payment Confirmation'),
    ('settlement_recording', 'Settlement Recording'),
    ('statement', 'Statement'),
    ('summons', 'Summons'),
    ('term_checker', 'Term Checker'),
    ('unknown_creditor', 'Unknown Creditor'),
    ('voided_check', 'Voided Check'),
)

TYPE_CHOICES_DICT = dict(TYPE_CHOICES)


STATE_CHOICES = (

    ('Armed Forces', (
        ('AA', 'Americas'),
        ('AP', 'Pacific'),
        ('AE', 'Other'),
    )),

    ('Australia', (
        ('NSW', 'New South Wales'),
        ('ANT', 'Northern Territory'),
        ('QLD', 'Queensland'),
        ('SA', 'South Australia'),
        ('TAS', 'Tasmania'),
        ('VIC', 'Victoria'),
        ('WAU', 'Western Australia'),
    )),

    ('Canada', (
        ('AB', 'Alberta'),
        ('BC', 'British Columbia'),
        ('MB', 'Manitoba'),
        ('NB', 'New Brunswick'),
        ('NL', 'Newfoundland'),
        ('NT', 'Northwest Territories'),
        ('NS', 'Nova Scotia'),
        ('NU', 'Nunavet'),
        ('ON', 'Ontario'),
        ('PE', 'Prince Edward Island'),
        ('QC', 'Quebec'),
        ('SK', 'Saskatchewan'),
        ('YT', 'Yukon'),
    )),

    ('U.S. States', (
        ('AL', 'Alabama'),
        ('AK', 'Alaska'),
        ('AZ', 'Arizona'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('CO', 'Colorado'),
        ('CT', 'Connecticut'),
        ('DE', 'Delaware'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('HI', 'Hawaii'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('IA', 'Iowa'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('ME', 'Maine'),
        ('MD', 'Maryland'),
        ('MA', 'Massachusetts'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MS', 'Mississippi'),
        ('MO', 'Missouri'),
        ('MT', 'Montana'),
        ('NE', 'Nebraska'),
        ('NV', 'Nevada'),
        ('NH', 'New Hampshire'),
        ('NJ', 'New Jersey'),
        ('NM', 'New Mexico'),
        ('NY', 'New York'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('OR', 'Oregon'),
        ('PA', 'Pennsylvania'),
        ('RI', 'Rhode Island'),
        ('SC', 'South Carolina'),
        ('SD', 'South Dakota'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VT', 'Vermont'),
        ('VA', 'Virginia'),
        ('WA', 'Washington'),
        ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'),
        ('WY', 'Wyoming'),
    )),

    ('U.S. Others', (
        ('AS', 'American Samoa'),
        ('DC', 'District of Columbia'),
        ('GU', 'Guam'),
        ('PR', 'Puerto Rico'),
        ('VI', 'U.S. Virgin Islands'),
    )),

)

STATE_CHOICES_DICT = {
    key: value
    for group, choices in STATE_CHOICES
    for key, value in choices
}
