from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from sundog.constants import *
from sundog.management.commands.utils import get_or_create_model_instance, print_script_header, print_script_end


class Command(BaseCommand):
    def handle(self, *args, **options):
        permissions = [
            # Contact
            {'codename': CONTACT_ACCESS_TAB, 'name': 'Access Tab', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_VIEW_ALL_CONTACTS, 'name': 'View All Contacts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_SEARCH_ALL, 'name': "Search All, Can't Edit", 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE, 'name': 'Create Contacts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EDIT, 'name': 'Edit Contacts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE, 'name': 'Delete Contacts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_VIEW_CONTACT_DETAILS, 'name': 'View Contact Details', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_MARK_PUBLIC, 'name': 'Mark Contacts Public', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_MARK_PRIVATE, 'name': 'Mark Contacts Private', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_PRIMARY_ASSIGNED, 'name': 'Change Primary Assigned', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CHANGE_STATUS, 'name': 'Change Contact Status', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE_NOTES, 'name': 'Add Notes', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.view_attorney_notes', 'name': 'View Attorney Notes', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_NOTES, 'name': 'Delete Notes', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_GENERATE_PDF, 'name': 'Generate PDFs', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DOWNLOAD_FILES, 'name': 'Download Files', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_DOCUMENTS, 'name': 'Delete Documents', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE_ALERTS, 'name': 'Create Alerts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EDIT_ALERTS, 'name': 'Edit Alerts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_ALERTS, 'name': 'Delete Alerts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_SEND_EMAILS, 'name': 'Send Emails', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_SEND_EXTERNAL_FORMS, 'name': 'Send External Forms', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE_CALL_ACTIVITY, 'name': 'Create Call Activity', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_VIEW_CONTACT_LIST, 'name': 'View Contact List', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_VIEW_LIST_DATA, 'name': 'View List Data', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE_LISTS, 'name': 'Create Lists', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EDIT_LISTS, 'name': 'Edit Lists', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_LISTS, 'name': 'Delete Lists', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_SEARCH, 'name': 'Search Contacts', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EXPORT, 'name': 'Export Contacts', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.view_custom_fields', 'name': 'View Custom Fields', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.create_custom_fields', 'name': 'Create Custom Fields', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.edit_custom_fields', 'name': 'Edit Custom Fields', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.delete_custom_fields', 'name': 'Delete Custom Fields', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_VIEW_WORKFLOW, 'name': 'View Workflow', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE_WORKFLOW, 'name': 'Create Workflow', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EDIT_WORKFLOW, 'name': 'Edit Workflow', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_WORKFLOW, 'name': 'Delete Workflow', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_MANAGE_CAMPAIGNS, 'name': 'Manage Campaigns', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_CREATE_DATA_SOURCES, 'name': 'Create Data Sources', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EDIT_DATA_SOURCES, 'name': 'Edit Data Sources', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_DATA_SOURCES, 'name': 'Delete Data Sources', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_EDIT_WEBHOOKS, 'name': 'Edit Webhooks', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_VIEW_SAVED_BANK_ACCOUNT, 'name': 'View Saved Bank Account / CC', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_SHOW_ACCOUNT_NUMBERS, 'name': 'Show Account Numbers', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_DELETE_CONTACT_HISTORY, 'name': 'Delete Contact History', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.reset_portal_password', 'name': 'Reset Portal Password', 'content_type': CONTACT_BASE_CODENAME}, #  CHECK IF THIS APPLIES???
            # {'codename': CONTACT_BASE_CODENAME + '.mass_edit', 'name': 'Mass Edit', 'content_type': CONTACT_BASE_CODENAME},
            # {'codename': CONTACT_BASE_CODENAME + '.mass_delete', 'name': 'Mass Delete', 'content_type': CONTACT_BASE_CODENAME},
            {'codename': CONTACT_PULL_CREDIT_REPORT, 'name': 'Pull Credit Report', 'content_type': CONTACT_BASE_CODENAME},

            # Creditors
            {'codename': CREDITOR_ACCESS_TAB, 'name': 'Access Tab', 'content_type': CREDITOR_BASE_CODENAME},
            {'codename': CREDITOR_CREATE, 'name': 'Add Creditors', 'content_type': CREDITOR_BASE_CODENAME},
            # {'codename': CREDITOR_EDIT, 'name': 'Edit Creditors', 'content_type': CREDITOR_BASE_CODENAME},
            # {'codename': CREDITOR_BASE_CODENAME + '.merge_creditors', 'name': 'Merge Creditors', 'content_type': CREDITOR_BASE_CODENAME},  # ????
            # {'codename': CREDITOR_DELETE, 'name': 'Delete Creditors', 'content_type': CREDITOR_BASE_CODENAME},
            # {'codename': CREDITOR_BASE_CODENAME + '.generate_creditor_letters', 'name': 'Generate Creditor Letters', 'content_type': CREDITOR_BASE_CODENAME},  # ????

            # Enrollments
            {'codename': ENROLLMENT_ACCESS_TAB, 'name': 'Access Tab', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_PAUSE_PAYMENTS, 'name': 'Pause Payments', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_RESUME_PAYMENTS, 'name': 'Resume Payments', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_CREATE_INCOME_EXPENSE, 'name': 'Create Income / Expense', 'content_type': ENROLLMENT_BASE_CODENAME},  # CHECK THIS
            {'codename': ENROLLMENT_INCOME_REPORT, 'name': 'Edit Income Report', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_DELETE_INCOME_REPORT, 'name': 'Delete Income Report', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_SAVE_CLIENT_ENROLLMENTS, 'name': 'Save Client Enrollments', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_SUBMIT_FILE, 'name': 'Submit File', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_RESUBMIT_FILE, 'name': 'Re-Submit File', 'content_type': ENROLLMENT_BASE_CODENAME},  # CHECK THIS
            {'codename': ENROLLMENT_APPROVE_FILE, 'name': 'Approve File', 'content_type': ENROLLMENT_BASE_CODENAME},  # CHECK THIS
            {'codename': ENROLLMENT_SECONDARY_APPROVAL, 'name': 'Secondary Approval', 'content_type': ENROLLMENT_BASE_CODENAME},  # CHECK THIS
            {'codename': ENROLLMENT_RETURN_FILE, 'name': 'Return File', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_APPLY_SPLIT_TEMPLATES, 'name': 'Apply Split Templates', 'content_type': ENROLLMENT_BASE_CODENAME},  # CHECK THIS
            {'codename': ENROLLMENT_COMPLETE, 'name': 'Complete Enrollment', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_GRADUATE_CLIENT, 'name': 'Graduate Clients', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_UNGRADUATE_CLIENT, 'name': 'Un-Graduate Clients', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_CANCEL_ENROLLMENT, 'name': 'Cancel Enrollment', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_EDIT_SUBMITTED_CONTACTS, 'name': 'Edit Submitted Contacts', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_EDIT_ENROLLED_CONTACTS, 'name': 'Edit Enrolled Contacts', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_RESET_CLIENT, 'name': 'Reset Clients', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_VIEW_LIST_DATA, 'name': 'View List Data', 'content_type': ENROLLMENT_BASE_CODENAME},  # CHECK THIS
            {'codename': ENROLLMENT_VIEW_REPORTS, 'name': 'View Reports', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_CREATE_REPORTS, 'name': 'Create Reports', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_CREATE_PLAN, 'name': 'Create Enrollment Plans', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_EDIT_PLAN, 'name': 'Edit Enrollment Plans', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_CHANGE_SETTINGS, 'name': 'Change Enrollment Settings', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_VIEW_PAYMENT_DETAILS, 'name': 'View Payment Details', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_MANUAL_TRANSACTION, 'name': 'Manual Transactions', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_SEARCH_TRANSACTION, 'name': 'Search Transactions', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_SCHEDULE_TRANFERS, 'name': 'Schedule Transfers', 'content_type': ENROLLMENT_BASE_CODENAME},
            {'codename': ENROLLMENT_EXPORT_REPORTS, 'name': 'Export Reports', 'content_type': ENROLLMENT_BASE_CODENAME},

            # Accounting
            {'codename': ACCOUNTING_ACCESS_TAB, 'name': 'Access Tab', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ACCOUNTING_CREATE_REPORTS, 'name': 'Create Reports', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ACCOUNTING_EXPORT_REPORTS, 'name': 'Export Reports', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ACCOUNTING_MODIFY_REPORTS, 'name': 'Modify Reports', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ACCOUNTING_DELETE_REPORTS, 'name': 'Delete Reports', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ACCOUNTING_BASE_CODENAME + '.view_fee_accounts', 'name': 'View Fee Accounts', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ACCOUNTING_BASE_CODENAME + '.edit_fee_accounts', 'name': 'Edit Fee Accounts', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ACCOUNTING_VIEW_ACCOUNTING, 'name': 'View Accounting Summaries', 'content_type': COMPANY_BASE_CODENAME},  #  CHECK THIS
            # {'codename': ACCOUNTING_BASE_CODENAME + '.view_pipeline_report', 'name': 'View Pipeline Report', 'content_type': COMPANY_BASE_CODENAME},

            # Settlements
            {'codename': SETTLEMENT_ACCESS_TAB, 'name': 'Access Tab', 'content_type': SETTLEMENT_BASE_CODENAME},
            {'codename': SETTLEMENT_CREATE_OFFERS, 'name': 'Create Offers', 'content_type': SETTLEMENT_BASE_CODENAME},
            {'codename': SETTLEMENT_ACCEPT_OFFERS, 'name': 'Accept Offers', 'content_type': SETTLEMENT_BASE_CODENAME},
            {'codename': SETTLEMENT_DELETE_OFFERS, 'name': 'Delete Offers', 'content_type': SETTLEMENT_BASE_CODENAME},
            {'codename': SETTLEMENT_VOID, 'name': 'Void Settlements', 'content_type': SETTLEMENT_BASE_CODENAME},

            # Documents
            {'codename': DOCS_ACCESS_TAB, 'name': 'Access Tab', 'content_type': DOCS_BASE_CODENAME},
            {'codename': DOCS_CREATE_DOCUMENT_TEMPLATE, 'name': 'Create Document Templates', 'content_type': DOCS_BASE_CODENAME},
            {'codename': DOCS_EDIT_DOCUMENT_TEMPLATE, 'name': 'Edit Document Templates', 'content_type': DOCS_BASE_CODENAME},
            {'codename': DOCS_DELETE_DOCUMENT_TEMPLATE, 'name': 'Delete Document Templates', 'content_type': DOCS_BASE_CODENAME},

            # Files
            {'codename': FILES_ACCESS_TAB, 'name': 'Access Tab', 'content_type': DOCS_BASE_CODENAME},
            {'codename': FILES_UPLOAD_MEDIA, 'name': 'Upload Media', 'content_type': DOCS_BASE_CODENAME},
            {'codename': FILES_DELETE_MEDIA, 'name': 'Delete Media', 'content_type': DOCS_BASE_CODENAME},
            {'codename': FILES_VIEW_FTP, 'name': "View FTP's", 'content_type': DOCS_BASE_CODENAME},
            {'codename': FILES_CREATE_FTP, 'name': "Create FTP's", 'content_type': DOCS_BASE_CODENAME},
            {'codename': FILES_DELETE_FTP, 'name': "Delete FTP's", 'content_type': DOCS_BASE_CODENAME},

            # E-Marketing
            {'codename': E_MARKETING_ACCESS_TAB, 'name': 'Access Tab', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_VIEW_CAMPAIGN_DESIGN, 'name': 'View Campaign Designs', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_CREATE_CAMPAIGN_DESIGN, 'name': 'Create Campaign Designs', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_DELETE_CAMPAIGN_DESIGN, 'name': 'Delete Campaign Designs', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_SCHEDULE_CAMPAIGN_LAUNCHES, 'name': 'Schedule Campaign Launches', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_VIEW_CAMPAIGN_STATISTICS, 'name': 'View Campaign Statistics', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_EDIT_CAMPAIGN_CATEGORIES, 'name': 'Edit Campaign Categories', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_CREATE_SENDER, 'name': 'Create Senders', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': E_MARKETING_DELETE_SENDER, 'name': 'Delete Senders', 'content_type': COMPANY_BASE_CODENAME},

            # Admin
            {'codename': ADMIN_ACCESS_TAB, 'name': 'Access Tab', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_CREATE_COMPANIES, 'name': 'Create Companies', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_EDIT_COMPANIES, 'name': 'Edit Companies', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_CREATE_USERS, 'name': 'Create Users', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_EDIT_USERS, 'name': 'Edit Users', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_DELETE_USERS, 'name': 'Delete Users', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_CREATE_ROLES, 'name': 'Create Roles', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_EDIT_ROLES, 'name': 'Edit Roles', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_DELETE_ROLES, 'name': 'Delete Roles', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_CREATE_TEAMS, 'name': 'Create Teams', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_EDIT_TEAMS, 'name': 'Edit Teams', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_DELETE_TEAMS, 'name': 'Delete Teams', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ADMIN_EDIT_TRIGGERS, 'name': 'Edit Triggers', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ADMIN_BASE_CODENAME + '.edit_program_options', 'name': 'Edit Program Options', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_CREATE_COMPENSATION_TEMPLATES, 'name': 'Create Compensation Templates', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_EDIT_COMPENSATION_TEMPLATES, 'name': 'Edit Compensation Templates', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_CREATE_PAYEES, 'name': 'Create Payees', 'content_type': COMPANY_BASE_CODENAME},
            {'codename': ADMIN_EDIT_PAYEES, 'name': 'Edit Payees', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ADMIN_VIEW_SYSTEM_LOG, 'name': 'View System Log', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ADMIN_EDIT_SYSTEM_SETTINGS, 'name': 'Edit System Settings', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ADMIN_BASE_CODENAME + '.edit_ip_whitelisting', 'name': 'Edit IP Whitelisting', 'content_type': COMPANY_BASE_CODENAME},
            # {'codename': ADMIN_BASE_CODENAME + '.login_as_other_users', 'name': 'Login As Other Users', 'content_type': COMPANY_BASE_CODENAME},
        ]

        content_types = {}
        print_script_header('Generate base Permissions results:')
        for permission_data_kwargs in permissions:
            model = permission_data_kwargs.pop('content_type')
            if model not in content_types.keys():
                content_types[model] = ContentType.objects.get(model=model, app_label='sundog')
            permission_data_kwargs['content_type'] = content_types[model]
            filter_kwargs = {'codename': permission_data_kwargs['codename']}
            message_name = permission_data_kwargs['name']
            get_or_create_model_instance(Permission, permission_data_kwargs, filter_kwargs, message_name, tabs=1)
        print_script_end()
