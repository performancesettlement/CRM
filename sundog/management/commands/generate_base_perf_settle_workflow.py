from django.core.management import BaseCommand
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

        stage_order = 1
        for stage_data in stages:
            status_order = 1
            stage_name = stage_data['name']
            statuses = stage_data.pop('statuses')
            stage_data['type'] = DEBT_SETTLEMENT
            stage_data['order'] = stage_order
            stage = Stage.objects.filter(name=stage_name).first()
            if not stage:
                stage = Stage(**stage_data)
                stage.save()
                print("Stage '{name}' has been successfully created.".format(name=stage_name))
            else:
                print("Stage '{name}' is already created.".format(name=stage.name))
            for status_data in statuses:
                status = Status.objects.filter(name=status_data['name']).first()
                status_data['stage'] = stage
                status_data['order'] = status_order
                if not status:
                    status = Status(**status_data)
                    status.save()
                    print("Status '{status_name}' has been successfully created and associated to '{stage_name}'.".format(
                        status_name=status.name, stage_name=stage_name))
                else:
                    print("Status '{status_name}' is already created and associated to '{stage_name}'.".format(
                        status_name=status.name, stage_name=stage.name))
                status_order += 1
            stage_order += 1
