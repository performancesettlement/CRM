from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.utils import unquote
from django.db import IntegrityError
from django.utils.encoding import force_text

from sundog.models import *
from sundog.forms import FileForm
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from sundog import services
from sundog import messages


class FileStatusAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        content_type = ContentType.objects.get(app_label=MyFile._meta.app_label, model=MyFile._meta.model_name)
        try:
            current_permission = Permission.objects.filter(codename=obj.get_permission_codename())
            if current_permission is not None and len(current_permission) > 0 and \
               obj.pk is not None and obj.ok == current_permission.status_id:
                current_permission.codename = obj.get_permission_codename()
                current_permission.name = obj.get_permission_name()
                current_permission.save()
            elif current_permission is not None and len(current_permission) == 0:
                Permission.objects.create(codename=obj.get_permission_codename(),
                                          name=obj.get_permission_name(),
                                          content_type=content_type)
        except Exception as e:
            logger.error(messages.ERROR_CREATE_STATUS_PERMISSION % obj.name)
            logger.error(e)
            pass

        super(FileStatusAdmin, self).save_model(request, obj, form, change)

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super(FileStatusAdmin, self).add_view(request, form_url, extra_context)
        except IntegrityError as e:
            logger.error(messages.ERROR_CREATE_STATUS_PERMISSION)
            logger.error(e)
            pass

            model = self.model
            opts = model._meta

            ModelForm = self.get_form(request)
            formsets = []
            inline_instances = self.get_inline_instances(request, None)
            form = ModelForm(request.POST, request.FILES)

            form.is_valid()
            form.add_error('name', 'File Status with this Name already exists.')


            adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
                                          self.get_prepopulated_fields(request),
                                          self.get_readonly_fields(request),
                                          model_admin=self)
            media = self.media + adminForm.media

            inline_admin_formsets = []
            for inline, formset in zip(inline_instances, formsets):
                fieldsets = list(inline.get_fieldsets(request))
                readonly = list(inline.get_readonly_fields(request))
                prepopulated = dict(inline.get_prepopulated_fields(request))
                inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                                                                  fieldsets, prepopulated, readonly, model_admin=self)
                inline_admin_formsets.append(inline_admin_formset)
                media = media + inline_admin_formset.media

            context = {
                'title': 'Add %s' % force_text(opts.verbose_name),
                'adminform': adminForm,
                'is_popup': IS_POPUP_VAR in request.REQUEST,
                'media': media,
                'inline_admin_formsets': inline_admin_formsets,
                'errors': helpers.AdminErrorList(form, formsets),
                'app_label': opts.app_label,
                'preserved_filters': self.get_preserved_filters(request),
            }
            context.update(extra_context or {})
            return self.render_change_form(request, context, form_url=form_url, add=True)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            return super(FileStatusAdmin, self).change_view(request, object_id, form_url, extra_context)

        except IntegrityError as e:
            logger.error(messages.ERROR_CREATE_STATUS_PERMISSION)
            logger.error(e)
            pass

            model = self.model
            opts = model._meta

            ModelForm = self.get_form(request)
            formsets = []
            inline_instances = self.get_inline_instances(request, None)
            form = ModelForm(request.POST, request.FILES)
            form.is_valid()

            form.add_error('name', 'File Status with this Name already exists.')

            adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
                                          self.get_prepopulated_fields(request),
                                          self.get_readonly_fields(request),
                                          model_admin=self)
            media = self.media + adminForm.media

            to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))

            obj = self.get_object(request, unquote(object_id), to_field)

            inline_admin_formsets = []
            for inline, formset in zip(inline_instances, formsets):
                fieldsets = list(inline.get_fieldsets(request))
                readonly = list(inline.get_readonly_fields(request))
                prepopulated = dict(inline.get_prepopulated_fields(request))
                inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                                                                  fieldsets, prepopulated, readonly, model_admin=self)
                inline_admin_formsets.append(inline_admin_formset)
                media = media + inline_admin_formset.media

            context = {
                'title': 'Change %s' % force_text(opts.verbose_name),
                'adminform': adminForm,
                'is_popup': IS_POPUP_VAR in request.REQUEST,
                'media': media,
                'object_id': object_id,
                'original': obj,
                'inline_admin_formsets': inline_admin_formsets,
                'errors': helpers.AdminErrorList(form, formsets),
                'app_label': opts.app_label,
                'preserved_filters': self.get_preserved_filters(request),
            }
            context.update(extra_context or {})
            return self.render_change_form(request, context, obj=obj, form_url=form_url)

    def get_queryset(self, request):
        return services.get_status_list_by_user(request.user, from_admin=True)


class FileAdmin(admin.ModelAdmin):
    form = FileForm

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def get_queryset(self, request):
        return services.get_files_by_user(request.user, from_admin=True)

    def get_form(self, request, obj=None, **kwargs):
        form = super(FileAdmin, self).get_form(request, **kwargs)
        form.current_user = request.user
        return form

    def save_model(self, request, obj, form, change):
        user_impersonator = None
        if hasattr(request, 'user_impersonator'):
            user_impersonator = request.user_impersonator
        if obj.pk is None:
            obj.stamp_created_values(request.user)
            obj.save()
            try:
                file_status_history = FileStatusHistory()
                file_status_history.create_new_file_status_history(
                    None, obj.current_status, request.user, user_impersonator)
                obj.file_status_history.add(file_status_history)
                services.create_file_permission(obj)
            except Exception as e:
                logger.error(messages.ERROR_SAVE_FILE_HISTORY % obj.file_id)
                logger.error(e)
            pass
        else:
            obj.stamp_updated_values(request.user)
            current_file_state = MyFile.objects.get(pk=obj.pk)
            current_permission = Permission.objects.filter(codename=obj.get_permission_codename())

            if current_permission is not None and len(current_permission) == 0:
                services.create_file_permission(obj)

            elif current_permission is not None and len(current_permission) > 0 and 'description' in form.changed_data:
                try:
                    current_permission.codename = obj.get_permission_codename()
                    current_permission.name = obj.get_permission_name()
                    current_permission.save()
                except Exception as e:
                    logger.error(messages.ERROR_MODIFY_STATUS_PERMISSION % obj.name)
                    logger.error(e)
                pass

            if 'current_status' in form.changed_data:
                try:
                    if current_file_state.current_status != obj.current_status:
                        file_status_history = FileStatusHistory()
                        file_status_history.create_new_file_status_history(
                            current_file_state, obj.current_status, request.user, user_impersonator)
                        obj.file_status_history.add(file_status_history)
                except Exception as e:
                    logger.error(messages.ERROR_SAVE_FILE_HISTORY % obj.file_id)
                    logger.error(e)
                pass

        super(FileAdmin, self).save_model(request, obj, form, change)


class ClientTypeAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        super(ClientTypeAdmin, self).save_model(request, obj, form, change)

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super(ClientTypeAdmin, self).add_view(request, form_url, extra_context)
        except IntegrityError as e:
            logger.error(messages.ERROR_CREATE_STATUS_PERMISSION)
            logger.error(e)
            pass

            model = self.model
            opts = model._meta

            ModelForm = self.get_form(request)
            formsets = []
            inline_instances = self.get_inline_instances(request, None)
            form = ModelForm(request.POST, request.FILES)

            form.is_valid()
            form.add_error('name', 'Client type with this Name already exists.')

            adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
                                          self.get_prepopulated_fields(request),
                                          self.get_readonly_fields(request),
                                          model_admin=self)
            media = self.media + adminForm.media

            inline_admin_formsets = []
            for inline, formset in zip(inline_instances, formsets):
                fieldsets = list(inline.get_fieldsets(request))
                readonly = list(inline.get_readonly_fields(request))
                prepopulated = dict(inline.get_prepopulated_fields(request))
                inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                                                                  fieldsets, prepopulated, readonly, model_admin=self)
                inline_admin_formsets.append(inline_admin_formset)
                media = media + inline_admin_formset.media

            context = {
                'title': 'Add %s' % force_text(opts.verbose_name),
                'adminform': adminForm,
                'is_popup': IS_POPUP_VAR in request.REQUEST,
                'media': media,
                'inline_admin_formsets': inline_admin_formsets,
                'errors': helpers.AdminErrorList(form, formsets),
                'app_label': opts.app_label,
                'preserved_filters': self.get_preserved_filters(request),
            }
            context.update(extra_context or {})
            return self.render_change_form(request, context, form_url=form_url, add=True)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        try:
            return super(ClientTypeAdmin, self).change_view(request, object_id, form_url, extra_context)

        except IntegrityError as e:
            logger.error(messages.ERROR_CREATE_STATUS_PERMISSION)
            logger.error(e)
            pass

            model = self.model
            opts = model._meta

            ModelForm = self.get_form(request)
            formsets = []
            inline_instances = self.get_inline_instances(request, None)
            form = ModelForm(request.POST, request.FILES)
            form.is_valid()

            form.add_error('name', 'Client type with this Name already exists.')

            to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))

            obj = self.get_object(request, unquote(object_id), to_field)

            adminForm = helpers.AdminForm(form, list(self.get_fieldsets(request)),
                                          self.get_prepopulated_fields(request),
                                          self.get_readonly_fields(request),
                                          model_admin=self)
            media = self.media + adminForm.media

            inline_admin_formsets = []
            for inline, formset in zip(inline_instances, formsets):
                fieldsets = list(inline.get_fieldsets(request))
                readonly = list(inline.get_readonly_fields(request))
                prepopulated = dict(inline.get_prepopulated_fields(request))
                inline_admin_formset = helpers.InlineAdminFormSet(inline, formset,
                                                                  fieldsets, prepopulated, readonly, model_admin=self)
                inline_admin_formsets.append(inline_admin_formset)
                media = media + inline_admin_formset.media

            context = {
                'title': 'Change %s' % force_text(opts.verbose_name),
                'adminform': adminForm,
                'is_popup': IS_POPUP_VAR in request.REQUEST,
                'media': media,
                'object_id': object_id,
                'original': obj,
                'inline_admin_formsets': inline_admin_formsets,
                'errors': helpers.AdminErrorList(form, formsets),
                'app_label': opts.app_label,
                'preserved_filters': self.get_preserved_filters(request),
            }
            context.update(extra_context or {})
            return self.render_change_form(request, context, obj=obj, form_url=form_url)

# Register the models that can be updated through the admin page.

admin.site.register(FileStatus, FileStatusAdmin)
admin.site.register(MyFile, FileAdmin)
admin.site.register(ClientType, ClientTypeAdmin)
admin.site.register(Tag)
admin.site.register(Client)
