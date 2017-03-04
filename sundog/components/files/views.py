from datatableview import Datatable
from datatableview.helpers import make_processor, through_filter
from django.contrib.auth.context_processors import PermWrapper
from django.forms import ClearableFileInput
from django.forms.models import ModelForm
from django.forms.widgets import Select
from django.shortcuts import redirect
from django.template.defaultfilters import date as date_filter
from django.urls import reverse
from django.views.generic.detail import BaseDetailView
from os.path import basename
from settings import SHORT_DATETIME_FORMAT
from sundog.components.files.models import File

from sundog.constants import (
    FILES_ACCESS_TAB,
    FILES_UPLOAD_MEDIA,
    FILES_VIEW_MEDIA,
    FILES_EDIT_MEDIA,
    FILES_DELETE_MEDIA,
)

from sundog.routing import route
from sundog.util.functional import modify_dict
from sundog.util.permission import require_permission

from sundog.util.views import (
    SundogAJAXAddView,
    SundogAJAXDeleteView,
    SundogAJAXEditView,
    SundogDatatableView,
    SundogEditView,
    format_column,
    template_column,
)

from sundog.utils import get_or_404


class FilesCRUDViewMixin:
    model = File

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'breadcrumbs': [
                ('Files', reverse('files')),
            ],
            'menu_page': 'files',
        }

    class form_class(ModelForm):
        class Meta:
            model = File

            fields = '''
                type
                title
                content
            '''.split()

            # The default file input field shows the full path to the file from
            # the root of the S3 bucket where it's stored.  This is noisy, as
            # the user cares only for the base name of the originally uploaded
            # file.  This is a slightly modified widget class that looks just
            # like the normal file input widget, but shows only the basename
            # of the uploaded file.
            class SimpleClearableFileInput(ClearableFileInput):
                def get_template_substitution_values(self, value):
                    return modify_dict(
                        dictionary=(
                            super().get_template_substitution_values(value)
                        ),
                        key='initial',
                        default='',
                        function=basename,
                    )

            widgets = {
                'type': Select(
                    attrs={
                        'class': 'selectpicker',
                    },
                ),
                'content': SimpleClearableFileInput,
            }

    class Meta:
        abstract = True


@route(
    regex=r'''
        ^files
        /?$
    ''',
    name='''
        files
        files.list
    '''.split()
)
@require_permission(FILES_ACCESS_TAB)
class FilesList(
    FilesCRUDViewMixin,
    SundogDatatableView,
):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'add_url': (
                reverse('files.add.ajax')
                if self.request.user.has_perm(
                    'sundog.file__upload_media',
                )
                else None
            ),
        }

    class datatable_class(Datatable):

        actions = template_column(
            label='Actions',
            template_name='sundog/files/list/actions.html',
            context_builder=lambda **kwargs: {
                'perms': PermWrapper(kwargs['view'].request.user),
            },
        )

        created_by_full_name = format_column(
            label='Created by',
            template='{created_by__first_name} {created_by__last_name}',
            fields='''
                created_by__first_name
                created_by__last_name
            '''.split(),
        )

        class Meta:
            structure_template = 'datatableview/bootstrap_structure.html'

            columns = '''
                id
                created_at
                created_by_full_name
                type
                title
                filename
            '''.split()

            ordering = '''
                -created_at
            '''.split()

            processors = {
                'created_at': through_filter(
                    date_filter,
                    arg=SHORT_DATETIME_FORMAT,
                ),
                'type': make_processor(
                    lambda type: File.TYPE_CHOICES_DICT[type]
                ),
            }


@route(
    regex=r'''
        ^files
        /(?P<pk>\d+)
        /view
        /?$
    ''',
    name='files.view',
)
@require_permission(FILES_VIEW_MEDIA)
@require_permission(FILES_ACCESS_TAB)
class FilesView(
    FilesCRUDViewMixin,
    BaseDetailView,
):

    def render_to_response(self, context):
        return redirect(
            get_or_404(
                File,
                pk=self.object.pk,
            )
        )


@route(
    regex=r'''
        ^files
        /(?P<pk>\d+)
        (?:/edit)?
        /?$
    ''',
    name='files.edit',
)
@require_permission(FILES_EDIT_MEDIA)
@require_permission(FILES_ACCESS_TAB)
class FilesEdit(
    FilesCRUDViewMixin,
    SundogEditView,
):
    pass


@route(
    regex=r'''
        ^files
        /add
        /ajax
        /?$
    ''',
    name='files.add.ajax',
)
@require_permission(FILES_UPLOAD_MEDIA)
@require_permission(FILES_ACCESS_TAB)
class FilesAddAJAX(
    FilesCRUDViewMixin,
    SundogAJAXAddView,
):

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.filename = form.instance.content.name
        return super().form_valid(form)


@route(
    regex=r'''
        ^files
        /(?P<pk>\d+)
        /delete
        /ajax
        /?$
    ''',
    name='files.delete.ajax',
)
@require_permission(FILES_DELETE_MEDIA)
@require_permission(FILES_ACCESS_TAB)
class FilesDeleteAJAX(
    FilesCRUDViewMixin,
    SundogAJAXDeleteView,
):
    pass


@route(
    regex=r'''
        ^files
        /(?P<pk>\d+)
        (?:/edit)?
        /ajax
        /?$
    ''',
    name='files.edit.ajax',
)
@require_permission(FILES_EDIT_MEDIA)
@require_permission(FILES_ACCESS_TAB)
class FilesEditAJAX(
    FilesCRUDViewMixin,
    SundogAJAXEditView,
):
    pass
