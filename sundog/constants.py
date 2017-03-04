SHORT_DATE_FORMAT = "%m/%d/%Y"
CACHE_IMPORT_EXPIRATION = 30
STATUS_CODENAME_PREFIX = 'can_use_status_'
FILE_CODENAME_PREFIX = 'can_use_file_'


MY_CONTACTS = 'my_contacts'
ALL_CONTACTS = 'all_contacts'

CONTACTS_STATIC_LIST = [
    MY_CONTACTS,
    ALL_CONTACTS
]

FIXED_VALUES = [
    'fixed',
    'fixedamort'
]

CONTACT_DEFAULT_STAGE = 'Contact'
CONTACT_DEFAULT_STATUS = 'Prospect'

#  PERMISSION CONSTANTS

CONTACT_BASE_CODENAME = 'contact'
CREDITOR_BASE_CODENAME = 'creditor'
ENROLLMENT_BASE_CODENAME = 'enrollment'
SETTLEMENT_BASE_CODENAME = 'settlement'
DOCS_BASE_CODENAME = 'document'
FILES_BASE_CODENAME = 'file'
E_MARKETING_BASE_CODENAME = 'e_marketing'
ADMIN_BASE_CODENAME = 'admin'
COMPANY_BASE_CODENAME = 'company'
ACCOUNTING_BASE_CODENAME = 'accounting'

CONTACT_ACCESS_TAB = CONTACT_BASE_CODENAME + '__access_tab'
CONTACT_VIEW_ALL_CONTACTS = CONTACT_BASE_CODENAME + '__view_all_contacts'  # TODO: Add permission
CONTACT_SEARCH_ALL = CONTACT_BASE_CODENAME + '__search_all'  # TODO: Add permission
CONTACT_CREATE = CONTACT_BASE_CODENAME + '__create_contacts'
CONTACT_EDIT = CONTACT_BASE_CODENAME + '__edit_contacts'
CONTACT_DELETE = CONTACT_BASE_CODENAME + '__delete_contacts'  # There is no delete user
CONTACT_VIEW_CONTACT_DETAILS = CONTACT_BASE_CODENAME + '__view_contact_details'
CONTACT_MARK_PUBLIC = CONTACT_BASE_CODENAME + '__mark_contact_public'
CONTACT_MARK_PRIVATE = CONTACT_BASE_CODENAME + '__mark_contacts_private'
CONTACT_PRIMARY_ASSIGNED = CONTACT_BASE_CODENAME + '__change_primary_assigned'  # Assigned person?
CONTACT_CHANGE_STATUS = CONTACT_BASE_CODENAME + '__change_contact_status'
CONTACT_CREATE_NOTES = CONTACT_BASE_CODENAME + '__create_notes'
CONTACT_DELETE_NOTES = CONTACT_BASE_CODENAME + '__delete_notes'  # Still not implemented
CONTACT_GENERATE_PDF = CONTACT_BASE_CODENAME + '__generate_pdfs'  # Ask About this
CONTACT_DOWNLOAD_FILES = CONTACT_BASE_CODENAME + '__download_files'  # Ask About this
CONTACT_DELETE_DOCUMENTS = CONTACT_BASE_CODENAME + '__delete_documents'  # Ask About this
CONTACT_CREATE_ALERTS = CONTACT_BASE_CODENAME + '__create_alerts'  # Still not implemented
CONTACT_EDIT_ALERTS = CONTACT_BASE_CODENAME + '__edit_alerts'  # Still not implemented
CONTACT_DELETE_ALERTS = CONTACT_BASE_CODENAME + '__delete_alerts'  # Still not implemented
CONTACT_SEND_EMAILS = CONTACT_BASE_CODENAME + '__send_emails'
CONTACT_SEND_EXTERNAL_FORMS = CONTACT_BASE_CODENAME + '__send_external_forms'  # Ask About this
CONTACT_CREATE_CALL_ACTIVITY = CONTACT_BASE_CODENAME + '__create_call_activity'
CONTACT_VIEW_CONTACT_LIST = CONTACT_BASE_CODENAME + '__view_contact_list'  # TODO: Add permission
CONTACT_VIEW_LIST_DATA = CONTACT_BASE_CODENAME + '__view_list_data'  # Still not implemented
CONTACT_CREATE_LISTS = CONTACT_BASE_CODENAME + '__create_lists'  # Still not implemented
CONTACT_EDIT_LISTS = CONTACT_BASE_CODENAME + '__edit_lists'  # Still not implemented
CONTACT_DELETE_LISTS = CONTACT_BASE_CODENAME + '__delete_lists'  # Still not implemented
CONTACT_SEARCH = CONTACT_BASE_CODENAME + '__search_contacts'  # TODO: Add permission
CONTACT_EXPORT = CONTACT_BASE_CODENAME + '__export_contacts'  # Still not implemented
CONTACT_VIEW_WORKFLOW = CONTACT_BASE_CODENAME + '__view_workflow'
CONTACT_CREATE_WORKFLOW = CONTACT_BASE_CODENAME + '__create_workflow'
CONTACT_EDIT_WORKFLOW = CONTACT_BASE_CODENAME + '__edit_workflow'
CONTACT_DELETE_WORKFLOW = CONTACT_BASE_CODENAME + '__delete_workflow'
CONTACT_MANAGE_CAMPAIGNS = CONTACT_BASE_CODENAME + '__manage_campaigns'
CONTACT_CREATE_DATA_SOURCES = CONTACT_BASE_CODENAME + '__create_data_sources'
CONTACT_EDIT_DATA_SOURCES = CONTACT_BASE_CODENAME + '__edit_data_sources'
CONTACT_DELETE_DATA_SOURCES = CONTACT_BASE_CODENAME + '__delete_data_sources'
CONTACT_EDIT_WEBHOOKS = CONTACT_BASE_CODENAME + '__edit_webhooks'  # Ask About this
CONTACT_VIEW_SAVED_BANK_ACCOUNT = CONTACT_BASE_CODENAME + '__view_saved_bank_account'
CONTACT_SHOW_ACCOUNT_NUMBERS = CONTACT_BASE_CODENAME + '__show_account_numbers'  # How this applies
CONTACT_DELETE_CONTACT_HISTORY = CONTACT_BASE_CODENAME + '__delete_contact_history'  # NOT MVP
CONTACT_PULL_CREDIT_REPORT = CONTACT_BASE_CODENAME + '__pull_credit_report'  # Still not implemented

CREDITOR_ACCESS_TAB = CREDITOR_BASE_CODENAME + '__access_tab'
CREDITOR_CREATE = CREDITOR_BASE_CODENAME + '__create_creditors'
CREDITOR_EDIT = CREDITOR_BASE_CODENAME + '__edit_creditors'  # Still not implemented?
CREDITOR_DELETE = CREDITOR_BASE_CODENAME + '__delete_creditors'  # Still not implemented?

ENROLLMENT_ACCESS_TAB = ENROLLMENT_BASE_CODENAME + '__access_tab'
ENROLLMENT_PAUSE_PAYMENTS = ENROLLMENT_BASE_CODENAME + '__pause_payments'  # Still not implemented
ENROLLMENT_RESUME_PAYMENTS = ENROLLMENT_BASE_CODENAME + '__resume_payments'  # Still not implemented
ENROLLMENT_CREATE_INCOME_EXPENSE = ENROLLMENT_BASE_CODENAME + '__create_income_expense'
ENROLLMENT_INCOME_REPORT = ENROLLMENT_BASE_CODENAME + '__edit_income_report'
ENROLLMENT_DELETE_INCOME_REPORT = ENROLLMENT_BASE_CODENAME + '__delete_income_report'
ENROLLMENT_SAVE_CLIENT_ENROLLMENTS = ENROLLMENT_BASE_CODENAME + '__save_client_enrollments'
ENROLLMENT_SUBMIT_FILE = ENROLLMENT_BASE_CODENAME + '__submit_file'  # Still not implemented
ENROLLMENT_RESUBMIT_FILE = ENROLLMENT_BASE_CODENAME + '__re_submit_file'  # Still not implemented
ENROLLMENT_APPROVE_FILE = ENROLLMENT_BASE_CODENAME + '__approve_file'  # Still not implemented
ENROLLMENT_SECONDARY_APPROVAL = ENROLLMENT_BASE_CODENAME + '__secondary_approval'  # Still not implemented
ENROLLMENT_RETURN_FILE = ENROLLMENT_BASE_CODENAME + '__return_file'  # Still not implemented
ENROLLMENT_APPLY_SPLIT_TEMPLATES = ENROLLMENT_BASE_CODENAME + '__apply_split_templates'
ENROLLMENT_COMPLETE = ENROLLMENT_BASE_CODENAME + '__complete_enrollment'  # Still not implemented
ENROLLMENT_GRADUATE_CLIENT = ENROLLMENT_BASE_CODENAME + '__graduate_clients'  # Still not implemented
ENROLLMENT_UNGRADUATE_CLIENT = ENROLLMENT_BASE_CODENAME + '__un_graduate_client'  # Still not implemented
ENROLLMENT_CANCEL_ENROLLMENT = ENROLLMENT_BASE_CODENAME + '__cancel_enrollment'  # Still not implemented
ENROLLMENT_EDIT_SUBMITTED_CONTACTS = ENROLLMENT_BASE_CODENAME + '__edit_submitted_contacts'  # Still not implemented
ENROLLMENT_EDIT_ENROLLED_CONTACTS = ENROLLMENT_BASE_CODENAME + '__edit_enrolled_contacts'  # Still not implemented
ENROLLMENT_RESET_CLIENT = ENROLLMENT_BASE_CODENAME + '__reset_clients'  # Still not implemented
ENROLLMENT_VIEW_LIST_DATA = ENROLLMENT_BASE_CODENAME + '__view_list_data'  # CHECK IF THIS APPLIES
ENROLLMENT_VIEW_REPORTS = ENROLLMENT_BASE_CODENAME + '__view_reports'  # Still not implemented
ENROLLMENT_CREATE_REPORTS = ENROLLMENT_BASE_CODENAME + '__create_reports'  # Still not implemented
ENROLLMENT_CREATE_PLAN = ENROLLMENT_BASE_CODENAME + '__create_enrollment_plans'
ENROLLMENT_EDIT_PLAN = ENROLLMENT_BASE_CODENAME + '__edit_enrollment_plans'
ENROLLMENT_CHANGE_SETTINGS = ENROLLMENT_BASE_CODENAME + '__change_enrollment_settings'
ENROLLMENT_VIEW_PAYMENT_DETAILS = ENROLLMENT_BASE_CODENAME + '__view_payment_details'  # Still not implemented (no reports or lists)
ENROLLMENT_MANUAL_TRANSACTION = ENROLLMENT_BASE_CODENAME + '__manual_transactions'  # Still not implemented
ENROLLMENT_SEARCH_TRANSACTION = ENROLLMENT_BASE_CODENAME + '__search_transactions'  # Still not implemented
ENROLLMENT_SCHEDULE_TRANSFERS = ENROLLMENT_BASE_CODENAME + '__schedule_transfers'  # Still not implemented
ENROLLMENT_EXPORT_REPORTS = ENROLLMENT_BASE_CODENAME + '__export_reports'  # Still not implemented

ACCOUNTING_ACCESS_TAB = ACCOUNTING_BASE_CODENAME + '__access_tab'  # Still not implemented
ACCOUNTING_CREATE_REPORTS = ACCOUNTING_BASE_CODENAME + '__create_reports'  # Still not implemented
ACCOUNTING_EXPORT_REPORTS = ACCOUNTING_BASE_CODENAME + '__export_reports'  # Still not implemented
ACCOUNTING_MODIFY_REPORTS = ACCOUNTING_BASE_CODENAME + '__modify_reports'  # Still not implemented
ACCOUNTING_DELETE_REPORTS = ACCOUNTING_BASE_CODENAME + '__delete_reports'  # Still not implemented
ACCOUNTING_VIEW_ACCOUNTING = ACCOUNTING_BASE_CODENAME + '__view_accounting'  # Still not implemented

SETTLEMENT_ACCESS_TAB = SETTLEMENT_BASE_CODENAME + '__access_tab'
SETTLEMENT_CREATE_OFFERS = SETTLEMENT_BASE_CODENAME + '__create_offers'
SETTLEMENT_ACCEPT_OFFERS = SETTLEMENT_BASE_CODENAME + '__accept_offers'
SETTLEMENT_DELETE_OFFERS = SETTLEMENT_BASE_CODENAME + '__delete_offers'  # There is no delete settlement
SETTLEMENT_VOID = SETTLEMENT_BASE_CODENAME + '__void_settlements'  # Still not implemented

DOCS_ACCESS_TAB = DOCS_BASE_CODENAME + '__access_tab'
DOCS_VIEW_DOCUMENT_TEMPLATE = DOCS_BASE_CODENAME + '__view_document_templates'
DOCS_CREATE_DOCUMENT_TEMPLATE = DOCS_BASE_CODENAME + '__create_document_templates'
DOCS_EDIT_DOCUMENT_TEMPLATE = DOCS_BASE_CODENAME + '__edit_document_templates'
DOCS_DELETE_DOCUMENT_TEMPLATE = DOCS_BASE_CODENAME + '__delete_document_templates'

FILES_ACCESS_TAB = FILES_BASE_CODENAME + '__access_tab'
FILES_VIEW_MEDIA = FILES_BASE_CODENAME + '__view_media'
FILES_UPLOAD_MEDIA = FILES_BASE_CODENAME + '__upload_media'
FILES_EDIT_MEDIA = FILES_BASE_CODENAME + '__edit_media'
FILES_DELETE_MEDIA = FILES_BASE_CODENAME + '__delete_media'
FILES_VIEW_FTP = FILES_BASE_CODENAME + '__view_ftp'  # Does this applies?
FILES_CREATE_FTP = FILES_BASE_CODENAME + '__create_ftp'  # Does this applies?
FILES_DELETE_FTP = FILES_BASE_CODENAME + '__delete_ftp'  # Does this applies?

E_MARKETING_ACCESS_TAB = E_MARKETING_BASE_CODENAME + '__access_tab'
E_MARKETING_CREATE_CAMPAIGN_DESIGN = E_MARKETING_BASE_CODENAME + '__create_campaign_designs'
E_MARKETING_EDIT_CAMPAIGN_DESIGN = E_MARKETING_BASE_CODENAME + '__edit_campaign_designs'
E_MARKETING_DELETE_CAMPAIGN_DESIGN = E_MARKETING_BASE_CODENAME + '__delete_campaign_designs'
E_MARKETING_SCHEDULE_CAMPAIGN_LAUNCHES = E_MARKETING_BASE_CODENAME + '__schedule_campaign_launches'  # Ask About this
E_MARKETING_VIEW_CAMPAIGN_STATISTICS = E_MARKETING_BASE_CODENAME + '__view_campaign_statistics'  # Ask About this
E_MARKETING_EDIT_CAMPAIGN_CATEGORIES = E_MARKETING_BASE_CODENAME + '__edit_campaign_categories'  # Ask About this
E_MARKETING_CREATE_SENDER = E_MARKETING_BASE_CODENAME + '__create_senders'
E_MARKETING_DELETE_SENDER = E_MARKETING_BASE_CODENAME + '__delete_senders'
E_MARKETING_EDIT_SENDER = E_MARKETING_BASE_CODENAME + '__edit_senders'

ADMIN_ACCESS_TAB = ADMIN_BASE_CODENAME + '__access_tab'
ADMIN_CREATE_COMPANIES = ADMIN_BASE_CODENAME + '__create_companies'
ADMIN_EDIT_COMPANIES = ADMIN_BASE_CODENAME + '__edit_companies'
ADMIN_CREATE_USERS = ADMIN_BASE_CODENAME + '__create_users'
ADMIN_EDIT_USERS = ADMIN_BASE_CODENAME + '__edit_users'
ADMIN_DELETE_USERS = ADMIN_BASE_CODENAME + '__delete_users'  # There is no delete user
ADMIN_CREATE_ROLES = ADMIN_BASE_CODENAME + '__create_roles'
ADMIN_EDIT_ROLES = ADMIN_BASE_CODENAME + '__edit_roles'
ADMIN_DELETE_ROLES = ADMIN_BASE_CODENAME + '__delete_roles'  # There is no delete role
ADMIN_CREATE_TEAMS = ADMIN_BASE_CODENAME + '__create_teams'
ADMIN_EDIT_TEAMS = ADMIN_BASE_CODENAME + '__edit_teams'
ADMIN_DELETE_TEAMS = ADMIN_BASE_CODENAME + '__delete_teams'
ADMIN_EDIT_TRIGGERS = ADMIN_BASE_CODENAME + '__edit_triggers'  # Still not implemented?
ADMIN_CREATE_COMPENSATION_TEMPLATES = ADMIN_BASE_CODENAME + '__create_compensation_templates'
ADMIN_EDIT_COMPENSATION_TEMPLATES = ADMIN_BASE_CODENAME + '__edit_compensation_templates'
ADMIN_CREATE_PAYEES = ADMIN_BASE_CODENAME + '__create_payees'
ADMIN_EDIT_PAYEES = ADMIN_BASE_CODENAME + '__edit_payees'
ADMIN_VIEW_SYSTEM_LOG = ADMIN_BASE_CODENAME + '__view_system_log'  # Still not implemented
ADMIN_EDIT_SYSTEM_SETTINGS = ADMIN_BASE_CODENAME + '__edit_system_setting'  # Still not implemented
