from django.core.management.base import BaseCommand
from sundog.models import Contact, User


class Command(BaseCommand):
    def handle(self, *args, **options):
        user = User.objects.first()

        contact_data = {
            'call_center_representative': user,
            'assigned_to': user,
        }

        for i in range(1, 200):
            Contact(
                first_name='Some contact first name ' + str(i),
                last_name='Some contact last name ' + str(i),
                **contact_data,
            ).save()
