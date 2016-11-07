from django.apps import AppConfig


class SunDogConfig(AppConfig):
    name = 'sundog'
    verbose_name = 'SunDog'

    def ready(self):
        pass
