from django.core.management import BaseCommand
from sundog.management.commands.utils import get_or_create_model_instance, print_script_header, print_script_end
from sundog.models import Stage, DEBT_SETTLEMENT, Status


class Command(BaseCommand):
    def handle(self, *args, **options):
        stages = [
            {
                'name': 'Contact',
                'statuses': [
                    {'name': 'Prospect', 'color': '#FFFFFF'},
                    {'name': 'Application', 'color': '#000000'},
                    {'name': 'Pitched', 'color': '#FFFFFF'},
                    {'name': 'Not Enough Debt', 'color': '#FF2F0F'},
                    {'name': 'Can Not Afford', 'color': '#FF2F0F'},
                    {'name': 'Not Interested - Credit', 'color': '#FF2F0F'},
                    {'name': 'Not Interested - Other', 'color': '#FF2F0F'},
                    {'name': 'De-Enrolled', 'color': '#FFFFFF'},
                    {'name': 'Returned By Underwriting', 'color': '#FFFFFF'},
                    {'name': 'Returned & Dead', 'color': '#FF2F0F'},
                ]
            },
            {
                'name': 'Processing',
                'statuses': [
                    {'name': 'QC Needed', 'color': '#FFFFFF'},
                    {'name': 'QC Issue', 'color': '#FFFFFF'},
                    {'name': 'QC & Welcome Call Needed', 'color': '#FFFFFF'},
                    {'name': 'Under Review', 'color': '#FFFFFF'},
                    {'name': 'Approved', 'color': '#FFFFFF'},
                ]
            },
            {
                'name': 'Client',
                'statuses': [
                    {'name': 'Active', 'color': '#10822E'},
                    {'name': 'Cancelled', 'color': '#FF2F0F'},
                    {'name': 'Cancelled: Do Not Contact', 'color': '#FF2F0F'},
                    {'name': 'Paused: Manager Hold', 'color': '#FFB217'},
                    {'name': 'Paused: Manager Hold For Fees Owed', 'color': '#FFB217'},
                    {'name': 'Graduated', 'color': '#56D166'},
                    {'name': 'NSF Problem', 'color': '#FF2F0F'},
                    {'name': 'Paused: Bailout Loan Is Being Processed', 'color': '#FFB217'},
                    {'name': 'Paused: Cancellation Request Received 2+ Drafts Made', 'color': '#FFB217'},
                    {'name': 'Paused: Cancellation Request Received Less Than 2 Drafts Made', 'color': '#FFB217'},
                    {'name': 'Paused For Unresolved Trust Account Issues', 'color': '#FFB217'},
                    {'name': 'Paused: NSF and Gone Dark', 'color': '#FFB217'},
                    {'name': 'Paused Temporarily For Financial Reasons', 'color': '#FFB217'},
                    {'name': 'Settlement Authorization Needed', 'color': '#7214FF'},
                    {'name': 'Welcome Call Needed', 'color': '#2B72FF'},
                ]
            },
            {
                'name': 'Partner Lead',
                'statuses': [
                    {'name': 'Submit To Student Loan Partner', 'color': '#FFFFFF'},
                ]
            },
        ]

        print_script_header('Generate base Performance Settlement Workflow Stage/Status results:')
        stage_order = 1
        for stage_data_kwargs in stages:
            status_order = 1
            statuses = stage_data_kwargs.pop('statuses')
            stage_data_kwargs['type'] = DEBT_SETTLEMENT
            stage_data_kwargs['order'] = stage_order
            stage_name = stage_data_kwargs['name']
            stage_filter_kwargs = {'name': stage_name}
            stage = get_or_create_model_instance(Stage, stage_data_kwargs, stage_filter_kwargs, stage_name, tabs=1)
            for status_data_kwargs in statuses:
                status_name = status_data_kwargs['name']
                status_data_kwargs['stage'] = stage
                status_data_kwargs['order'] = status_order
                status_filter_kwargs = {'name': status_data_kwargs['name']}
                get_or_create_model_instance(
                    Status, status_data_kwargs, status_filter_kwargs, status_name, associated_to=stage_name, tabs=2)
                status_order += 1
            stage_order += 1
        print_script_end()
