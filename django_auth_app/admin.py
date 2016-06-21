from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.auth.models import User


class CustomUserAdmin(UserAdmin):

    def save_model(self, request, obj, form, change):
        obj.username = obj.username.strip().lower()

        super(CustomUserAdmin, self).save_model(request, obj, form, change)

# Register your models here.
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
