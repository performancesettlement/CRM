from django.core.management.base import BaseCommand
from sundog.models import Contact, LeadSource, User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.first()

        lead_source = LeadSource(
            name='Some lead source',
        )
        lead_source.save()

        contact_data = {
            'lead_source': lead_source,
            'call_center_representative': user,
            'assigned_to': user,
        }

        for i in range(1, 200):
            Contact(
                first_name='Some contact first name ' + str(i),
                last_name='Some contact last name ' + str(i),
                **contact_data,
            ).save()
