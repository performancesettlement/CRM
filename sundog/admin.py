from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.options import IS_POPUP_VAR, TO_FIELD_VAR
from django.contrib.admin.utils import unquote
from django.db import IntegrityError
from django.utils.encoding import force_text

from sundog import messages
from sundog.models import ClientType, Contact

import logging


logger = logging.getLogger(__name__)


class ClientTypeAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def add_view(self, request, form_url='', extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
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
            return super().change_view(request, object_id, form_url, extra_context)

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

admin.site.register(ClientType, ClientTypeAdmin)
admin.site.register(Contact)
