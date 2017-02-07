from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import BaseCommand
from sundog.management.commands.utils import get_or_create_model_instance, print_script_header, print_script_end

CONTACT_BASE_CODENAME = 'contact'
CREDITOR_BASE_CODENAME = 'creditor'
ENROLLMENT_BASE_CODENAME = 'enrollment'
SETTLEMENT_BASE_CODENAME = 'settlement'
DOCS_BASE_CODENAME = 'doc'
FILES_BASE_CODENAME = 'file'
E_MARKETING_BASE_CODENAME = 'e_marketing'
ADMIN_BASE_CODENAME = 'admin'


class Command(BaseCommand):
    def handle(self, *args, **options):
        permissions = [
            # Contact
            {'codename': CONTACT_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_all_contacts', 'name': 'View All Contacts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.search_all_cant_edit', 'name': "Search All, Can't Edit", 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_contacts', 'name': 'Create Contacts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_contacts', 'name': 'Edit Contacts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_contacts', 'name': 'Delete Contacts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_contact_details', 'name': 'View Contact Details', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.mark_contact_public', 'name': 'Mark Contacts Public', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.mark_contacts_private', 'name': 'Mark Contacts Private', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.change_primary_assigned', 'name': 'Change Primary Assigned', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.change_contact_status', 'name': 'Change Contact Status', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.add_notes', 'name': 'Add Notes', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_attorney_notes', 'name': 'View Attorney Notes', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_notes', 'name': 'Delete Notes', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.generate_pdfs', 'name': 'Generate PDFs', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.download_files', 'name': 'Download Files', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_documents', 'name': 'Delete Documents', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_alerts', 'name': 'Create Alerts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_alerts', 'name': 'Edit Alerts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_alerts', 'name': 'Delete Alerts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.send_emails', 'name': 'Send Emails', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.send_external_forms', 'name': 'Send External Forms', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_call_activity', 'name': 'Create Call Activity', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_contact_list', 'name': 'View Contact List', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_list_data', 'name': 'View List Data', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_lists', 'name': 'Create Lists', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_lists', 'name': 'Edit Lists', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_lists', 'name': 'Delete Lists', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.search_contacts', 'name': 'Search Contacts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.export_contacts', 'name': 'Export Contacts', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_custom_fields', 'name': 'View Custom Fields', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_custom_fields', 'name': 'Create Custom Fields', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_custom_fields', 'name': 'Edit Custom Fields', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_custom_fields', 'name': 'Delete Custom Fields', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_workflow', 'name': 'View Workflow', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_workflow', 'name': 'Create Workflow', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_workflow', 'name': 'Edit Workflow', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_workflow', 'name': 'Delete Workflow', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.manage_campaigns', 'name': 'Manage Campaigns', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.create_data_sources', 'name': 'Create Data Sources', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_data_sources', 'name': 'Edit Data Sources', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_data_sources', 'name': 'Delete Data Sources', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.edit_webhooks', 'name': 'Edit Webhooks', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.view_saved_bank_account', 'name': 'View Saved Bank Account / CC', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.show_account_numbers', 'name': 'Show Account Numbers', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.delete_contact_history', 'name': 'Delete Contact History', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.reset_portal_password', 'name': 'Reset Portal Password', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.mass_edit', 'name': 'Mass Edit', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.mass_delete', 'name': 'Mass Delete', 'content_type': 'contact'},
            {'codename': CONTACT_BASE_CODENAME + '.pull_credit_report', 'name': 'Pull Credit Report', 'content_type': 'contact'},

            # Creditors
            {'codename': CREDITOR_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'creditor'},
            {'codename': CREDITOR_BASE_CODENAME + '.add_creditors', 'name': 'Add Creditors', 'content_type': 'creditor'},
            {'codename': CREDITOR_BASE_CODENAME + '.edit_creditors', 'name': 'Edit Creditors', 'content_type': 'creditor'},
            {'codename': CREDITOR_BASE_CODENAME + '.merge_creditors', 'name': 'Merge Creditors', 'content_type': 'creditor'},
            {'codename': CREDITOR_BASE_CODENAME + '.delete_creditors', 'name': 'Delete Creditors', 'content_type': 'creditor'},
            {'codename': CREDITOR_BASE_CODENAME + '.generate_creditor_letters', 'name': 'Generate Creditor Letters', 'content_type': 'creditor'},

            # Enrollments
            {'codename': ENROLLMENT_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.pause_payments', 'name': 'Pause Payments', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.resume_payments', 'name': 'Resume Payments', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.create_income_expense', 'name': 'Create Income / Expense', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.edit_income_report', 'name': 'Edit Income Report', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.delete_income_report', 'name': 'Delete Income Report', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.save_client_enrollments', 'name': 'Save Client Enrollments', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.submit_file', 'name': 'Submit File', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.re_submit_file', 'name': 'Re-Submit File', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.approve_file', 'name': 'Approve File', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.secondary_approval', 'name': 'Secondary Approval', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.return_file', 'name': 'Return File', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.apply_split_templates', 'name': 'Apply Split Templates', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.complete_enrollment', 'name': 'Complete Enrollment', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.graduate_clients', 'name': 'Graduate Clients', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.un_graduate_client', 'name': 'Un-Graduate Clients', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.cancel_enrollment', 'name': 'Cancel Enrollment', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.edit_submitted_contacts', 'name': 'Edit Submitted Contacts', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.edit_enrolled_contacts', 'name': 'Edit Enrolled Contacts', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.reset_clients', 'name': 'Reset Clients', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.view_list_data', 'name': 'View List Data', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.view_reports', 'name': 'View Reports', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.create_reports', 'name': 'Create Reports', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.create_enrollment_plans', 'name': 'Create Enrollment Plans', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.edit_enrollment_plans', 'name': 'Edit Enrollment Plans', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.change_enrollment_settings', 'name': 'Change Enrollment Settings', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.view_payment_details', 'name': 'View Payment Details', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.manual_transactions', 'name': 'Manual Transactions', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.search_transactions', 'name': 'Search Transactions', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.schedule_transfers', 'name': 'Schedule Transfers', 'content_type': 'enrollment'},
            {'codename': ENROLLMENT_BASE_CODENAME + '.export_reports', 'name': 'Export Reports', 'content_type': 'enrollment'},

            # Accounting
            {'codename': 'accounting.access_tab', 'name': 'Access Tab', 'content_type': ''},
            {'codename': 'accounting.create_reports', 'name': 'Create Reports', 'content_type': ''},
            {'codename': 'accounting.export_reports', 'name': 'Export Reports', 'content_type': ''},
            {'codename': 'accounting.modify_reports', 'name': 'Modify Reports', 'content_type': ''},
            {'codename': 'accounting.delete_reports', 'name': 'Delete Reports', 'content_type': ''},
            {'codename': 'accounting.view_fee_accounts', 'name': 'View Fee Accounts', 'content_type': ''},
            {'codename': 'accounting.edit_fee_accounts', 'name': 'Edit Fee Accounts', 'content_type': ''},
            {'codename': 'accounting.view_accounting', 'name': 'View Accounting Summaries', 'content_type': ''},
            {'codename': 'accounting.view_pipeline_report', 'name': 'View Pipeline Report', 'content_type': ''},

            # Settlements
            {'codename': SETTLEMENT_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'settlement'},
            {'codename': SETTLEMENT_BASE_CODENAME + '.create_offers', 'name': 'Create Offers', 'content_type': 'settlement'},
            {'codename': SETTLEMENT_BASE_CODENAME + '.accept_offers', 'name': 'Accept Offers', 'content_type': 'settlement'},
            {'codename': SETTLEMENT_BASE_CODENAME + '.delete_offers', 'name': 'Delete Offers', 'content_type': 'settlement'},
            {'codename': SETTLEMENT_BASE_CODENAME + '.void_settlements', 'name': 'Void Settlements', 'content_type': 'settlement'},

            # Documents
            {'codename': DOCS_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'document'},
            {'codename': DOCS_BASE_CODENAME + '.create_document_templates', 'name': 'Create Document Templates', 'content_type': 'document'},
            {'codename': DOCS_BASE_CODENAME + '.edit_document_templates', 'name': 'Edit Document Templates', 'content_type': 'document'},
            {'codename': DOCS_BASE_CODENAME + '.delete_document_templates', 'name': 'Delete Document Templates', 'content_type': 'document'},

            # Files
            {'codename': FILES_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'document'},
            {'codename': FILES_BASE_CODENAME + '.upload_media', 'name': 'Upload Media', 'content_type': 'document'},
            {'codename': FILES_BASE_CODENAME + '.delete_media', 'name': 'Delete Media', 'content_type': 'document'},
            {'codename': FILES_BASE_CODENAME + '.view_ftp', 'name': "View FTP's", 'content_type': 'document'},
            {'codename': FILES_BASE_CODENAME + '.create_ftp', 'name': "Create FTP's", 'content_type': 'document'},
            {'codename': FILES_BASE_CODENAME + '.delete_ftp', 'name': "Delete FTP's", 'content_type': 'document'},

            # E-Marketing
            {'codename': E_MARKETING_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.view_campaign_designs', 'name': 'View Campaign Designs', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.create_campaign_desings', 'name': 'Create Campaign Designs', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.delete_campaigns_designs', 'name': 'Delete Campaign Designs', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.schedule_campaign_launches', 'name': 'Schedule Campaign Launches', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.view_campaign_statistics', 'name': 'View Campaign Statistics', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.edit_campaign_categories', 'name': 'Edit Campaign Categories', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.create_senders', 'name': 'Create Senders', 'content_type': 'company'},
            {'codename': E_MARKETING_BASE_CODENAME + '.delete_senders', 'name': 'Delete Senders', 'content_type': 'company'},

            # Reports
            # {'codename': 'reports.access_tab', 'name': 'Access Tab', 'content_type': ''},
            # {'codename': 'reports.create_reports', 'name': 'Create Reports', 'content_type': ''},
            # {'codename': 'reports.export_reports', 'name': 'Export Reports', 'content_type': ''},
            # {'codename': 'reports.delete_reports', 'name': 'Delete Reports', 'content_type': ''},

            # Admin
            {'codename': ADMIN_BASE_CODENAME + '.access_tab', 'name': 'Access Tab', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.create_companies', 'name': 'Create Companies', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.create_users', 'name': 'Create Users', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_users', 'name': 'Edit Users', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.delete_users', 'name': 'Delete Users', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.view_roles', 'name': 'View Roles', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.create_roles', 'name': 'Create Roles', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.delete_roles', 'name': 'Delete Roles', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_teams', 'name': 'Create Teams', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_teams', 'name': 'Edit Teams', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.delete_teams', 'name': 'Delete Teams', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_triggers', 'name': 'Edit Triggers', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_program_options', 'name': 'Edit Program Options', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_compensation_templates', 'name': 'Edit Compensation Templates', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_payees', 'name': 'Edit Payees', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.setup_filed_permissions', 'name': 'Setup Field Permissions', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.view_system_log', 'name': 'View System Log', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_system_setting', 'name': 'Edit System Settings', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.edit_ip_whitelisting', 'name': 'Edit IP Whitelisting', 'content_type': 'company'},
            {'codename': ADMIN_BASE_CODENAME + '.login_as_other_users', 'name': 'Login As Other Users', 'content_type': 'company'},
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
