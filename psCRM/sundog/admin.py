from django.contrib import admin
from sundog.models import *
from sundog.forms import FileForm
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import services
import messages


class FileStatusAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            content_type = ContentType.objects.get(app_label=MyFile._meta.app_label, model=MyFile._meta.model_name)
            try:
                Permission.objects.create(codename=obj.get_permission_codename(),
                                                       name=obj.get_permission_name(),
                                                       content_type=content_type)
            except Exception, e:
                logger.error(messages.ERROR_CREATE_STATUS_PERMISSION % obj.name)
                logger.error(e)
                pass

        else:
            if 'name' in form.changed_data:
                try:
                    current_status = FileStatus.objects.get(pk=obj.pk)
                    current_permission = Permission.objects.get(codename=current_status.get_permission_codename())
                    current_permission.codename = obj.get_permission_codename()
                    current_permission.name = obj.get_permission_name()
                    current_permission.save()
                except Exception, e:
                    logger.error(messages.ERROR_MODIFY_STATUS_PERMISSION % obj.name)
                    logger.error(e)
                    content_type = ContentType.objects.get(app_label=MyFile._meta.app_label, model=MyFile._meta.model_name)
                    try:
                        Permission.objects.create(codename=obj.get_permission_codename(),
                                                  name=obj.get_permission_name(),
                                                  content_type=content_type)
                    except Exception, e:
                        logger.error(messages.ERROR_CREATE_STATUS_PERMISSION % obj.name)
                        logger.error(e)
                        pass
                    pass
        super(FileStatusAdmin, self).save_model(request, obj, form, change)

    def get_queryset(self, request):
        return services.get_status_list_by_user(request.user, from_admin=True)


class FileAdmin(admin.ModelAdmin):
    form = FileForm

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return services.get_files_by_user(request.user, from_admin=True)

    def get_form(self, request, obj=None, **kwargs):
        form = super(FileAdmin, self).get_form(request, **kwargs)
        form.current_user = request.user
        return form

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.stamp_created_values(request.user)
            obj.save()
            try:
                file_status_history = FileStatusHistory()
                file_status_history.create_new_file_status_history(None, obj.current_status, request.user)
                obj.file_status_history.add(file_status_history)
            except Exception, e:
                logger.error(messages.ERROR_SAVE_FILE_HISTORY % obj.file_id)
                logger.error(e)
            pass
        else:
            obj.stamp_updated_values(request.user)
            if 'current_status' in form.changed_data:
                try:
                    current_file_state = MyFile.objects.get(pk=obj.pk)
                    if current_file_state.current_status != obj.current_status:
                        file_status_history = FileStatusHistory()
                        file_status_history.create_new_file_status_history(current_file_state, obj.current_status, request.user)
                        obj.file_status_history.add(file_status_history)
                except Exception, e:
                    logger.error(messages.ERROR_SAVE_FILE_HISTORY % obj.file_id)
                    logger.error(e)
                    pass

        super(FileAdmin, self).save_model(request, obj, form, change)

# Register the models that can be updated through the admin page.
#admin.site.register(AreaOfInterest)
#admin.site.register(CommunityOfInterest)
admin.site.register(FileStatus, FileStatusAdmin)
admin.site.register(MyFile, FileAdmin)
admin.site.register(ClientType)
admin.site.register(Tag)
admin.site.register(Client)
