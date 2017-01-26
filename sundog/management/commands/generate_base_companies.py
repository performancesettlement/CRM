from django.core.management import BaseCommand
from sundog.models import Company


class Command(BaseCommand):
    def handle(self, *args, **options):
        companies = [
            {
                'name': 'Performance Settlement',
                'type': 'servicing_company',
                'active': True,
                'contact_name': 'Danny Crenshaw',
                'ein': '46-3572903',
                'address': '4940 Camus Dr. Suite A',
                'city': 'Newport Beach',
                'state': 'CA',
                'zip': '92660',
                'phone': '8882146322',
                'fax': '8552839057',
                'email': 'support@performancesettlement.com'
            },
        ]
        for company_data in companies:
            previous_companies = Company.objects.filter(name=company_data['name'])
            if len(previous_companies) == 0:
                Company(**company_data).save()
                print("Company '{name}' has been successfully created.")
            else:
                print("Company '{name}' is already created.")
