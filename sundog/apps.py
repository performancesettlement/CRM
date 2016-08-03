from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db import connection
import settings

FILE_ID_SEQUENCE = "sundog_myfile_file_id_seq"


def check_my_file_seed(sender, **kwargs):
    pass
    # if hasattr(settings, 'SEED_FILE_ID'):
    #     seed_id = int(settings.SEED_FILE_ID)
    #     cursor = connection.cursor()
    #
    #     cursor.execute("SELECT last_value FROM " + FILE_ID_SEQUENCE)
    #     row = cursor.fetchone()[0]
    #     if row and row < seed_id:
    #         cursor.execute("ALTER SEQUENCE "+FILE_ID_SEQUENCE+" RESTART WITH " +str(seed_id)+";")


class SunDogConfig(AppConfig):
    name = 'sundog'
    verbose_name = 'SunDog'

    def ready(self):
        post_migrate.connect(check_my_file_seed, sender=self)
