from django.contrib.auth.models import User
from django.core.management import BaseCommand
from sundog.management.commands.utils import print_script_header, get_or_create_model_instance, print_script_end
from sundog.models import Company


class Command(BaseCommand):
    ADMIN_USER_NAME = 'admin'

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

        print_script_header('Generate base Companies and Admin User results:')
        for company_data_kwargs in companies:
            company_message_kwargs = {'name': company_data_kwargs['name']}
            company_filter_kwargs = {'name': company_data_kwargs['name']}
            get_or_create_model_instance(Company, company_data_kwargs, company_filter_kwargs, company_message_kwargs,
                                         tabs=1)

        company = Company.objects.get(name='Performance Settlement')
        user_data_kwargs = {'username': Command.ADMIN_USER_NAME, 'password': 'Changeme12', 'email': '',
                            'company': company}
        user_filter_kwargs = {'username': Command.ADMIN_USER_NAME}
        get_or_create_model_instance(User, user_data_kwargs, user_filter_kwargs, Command.ADMIN_USER_NAME, tabs=1)
        print_script_end()
