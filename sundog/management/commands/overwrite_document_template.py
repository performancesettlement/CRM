from django.core.management.base import BaseCommand
from sundog.models import Document
from sundog.util.functional import mutate


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--document_id', required=True)
        parser.add_argument('--filename', required=True)

    def handle(self, *args, **options):
        mutate(
            Document.objects.get(
                pk=options['document_id'],
            ),
            lambda d:
                setattr(
                    d,
                    'template_body',
                    open(
                        options['filename'],
                        'r',
                    ).read(),
                )
        ).save()
