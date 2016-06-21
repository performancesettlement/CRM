from django.shortcuts import render_to_response, redirect, render
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, StreamingHttpResponse
from django.http.response import HttpResponseBadRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.core.files import File
import settings
import os
import logging
import services
import utils
import messages
from constants import IMPORT_FILE_EXCEL_FILENAME, IMPORT_CLIENT_EXCEL_FILENAME, SHORT_DATE_FORMAT
from django.contrib.auth.models import User
from haystack.generic_views import SearchView
from sundog.forms import FileCustomForm, FileSearchForm, ClientForm
from datetime import datetime
from sundog.models import MyFile, Message, Document, FileStatusHistory


#initialize logger
logger = logging.getLogger(__name__)


# upload profile picture
def index(request):
    context = RequestContext(request, {'request': request, 'user': request.user})
    return render_to_response('landing.html', context_instance=context)


@login_required()
def files_recent(request):
    #get files recent
    recent_files_list = services.get_access_file_history(request.user)
    context = RequestContext(request, {'request': request,
                                       'user': request.user,
                                       'recent_files_list': recent_files_list})
    return render_to_response('file/recent_files.html', context_instance=context)


@login_required()
def help(request):
    context = RequestContext(request, {'request': request, 'user': request.user})
    return render_to_response('help.html', context_instance=context)


def render404(request):
    return render_to_response('404.html')


@login_required()
def display_log(request):
    try:
        log_file_path = os.path.join(settings.PROJECT_ROOT, 'log/sundog.log')
        content = open(log_file_path, 'r').read()
        response = StreamingHttpResponse(content)
        response['Content-Type'] = 'text/plain; charset=utf8'
        return response
    except Exception, e:
        logger.error("An error occurred trying to display the log.")
        logger.error(e.message)
        return HttpResponseRedirect(reverse("admin:index"))


@login_required()
def erase_log(request):
    try:
        if request.POST:
            log_file_path = os.path.join(settings.PROJECT_ROOT, 'log/sundog.log')
            with open(log_file_path, 'w'):
                pass
            return JsonResponse({'result': 'OK'})
    except Exception, e:
        logger.error("An error occurred trying to delete the log.")
        logger.error(e.message)
        return JsonResponse({'result': 'An error occurred!'})


@login_required()
def file_detail(request, file_id):
    my_file = services.get_file_by_id_for_user(file_id, request.user)

    if my_file is None:
        raise Http404()
    elif my_file == "Unavailable":
        context = RequestContext(request, {'request': request, 'user': request.user,'file_id': file_id})
        return render_to_response('file/file_disabled.html', context_instance=context)
    else:
        documents = Document.objects.filter(file__file_id=file_id)
        documents_json = []
        if documents:
            documents_json = [{'size': t.document.size, 'name': t.document.name, 'url': t.document.url, 'id': t.pk} for t in documents]

        context = RequestContext(request, {'request': request, 'user': request.user,
                                       'opts': MyFile._meta, 'file': my_file, 'documents': documents_json})
        return render_to_response('file/file.html', context_instance=context)


@permission_required('sundog.change_file')
def file_edit(request, file_id, message=None):
    my_file = services.get_file_by_id_for_user(file_id, request.user)
    if my_file is None:
        raise Http404()
    elif my_file == "Unavailable":
        context = RequestContext(request, {'request': request, 'user': request.user,'file_id': file_id})
        return render_to_response('file/file_disabled.html', context_instance=context)
    else:
        form_errors = None
        if request.user.has_perm('sundog.add_client'):
            form_client = ClientForm()
        else:
            form_client = None
        current_status = my_file.current_status
        form = FileCustomForm(instance=my_file)
        form.fields['current_status'].queryset = services.get_status_list_by_user(request.user)

        documents = services.get_file_documents(file_id)
        documents_json = []
        users_json = []
        if documents:
            documents_json = [{'size': t.document.size, 'name': t.document.name, 'url': t.document.url, 'id': t.pk} for t in documents]
        users = services.get_participants_options(file_id, my_file.current_status, list(my_file.participants.all()))
        if users:
            users_json = [{'full_name': u.get_full_name() if u.get_full_name() else u.username, 'id': u.pk} for u in users]

        if request.method == 'POST' and request.POST:
            form = FileCustomForm(request.POST, instance=my_file)
            form.fields['current_status'].queryset = services.get_status_list_by_user(request.user)
            if form.is_valid():
                my_file = form.save(commit=False)
                # TODO: MAKE SURE THE USER HAS CHANGE TAG PERMISSION
                if current_status.status_id != my_file.current_status.status_id:
                    try:
                        file_status_history = FileStatusHistory()
                        file_status_history.create_new_file_status_history(current_status, my_file.current_status, request.user)
                        my_file.file_status_history.add(file_status_history)
                    except Exception, e:
                        logger.error(messages.ERROR_SAVE_FILE_HISTORY % my_file.file_id)
                        logger.error(e)
                        pass

                my_file.stamp_updated_values(request.user)
                my_file.save()
            else:
                form_errors = []
                for field in form:
                    if field.errors:
                        for field_error in field.errors:
                            form_errors.append(strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error)
                for non_field_error in form.non_field_errors():
                    form_errors.append(non_field_error)
        context = RequestContext(request, {'request': request, 'user': request.user, 'form': form, 'file_id': file_id,
                                           'opts': MyFile._meta, 'file': my_file, 'documents': documents_json, 'message': message,
                                           'participant_options': users_json, 'form_errors': form_errors, 'form_client': form_client})
        return render_to_response('file/file_form.html', context_instance=context)


@permission_required('sundog.add_file')
def file_add(request):
    form_errors = None
    form = FileCustomForm(request.POST or None)
    form.fields['current_status'].queryset = services.get_status_list_by_user(request.user)
    if request.user.has_perm('sundog.add_client'):
        form_client = ClientForm()
    else:
        form_client = None
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            my_file = form.save(commit=False)
            my_file.stamp_created_values(request.user)
            my_file.save()

            try:
                file_status_history = FileStatusHistory()
                file_status_history.create_new_file_status_history(None, my_file.current_status, request.user)
                my_file.file_status_history.add(file_status_history)
            except Exception, e:
                logger.error(messages.ERROR_SAVE_FILE_HISTORY % my_file.file_id)
                logger.error(e)
                pass

            return redirect('file_detail', file_id=my_file.file_id)
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        form_errors.append(strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)

    context = RequestContext(request, {'request': request, 'user': request.user, 'form': form, 'form_client': form_client,
                                       'form_errors': form_errors})
    return render_to_response('file/file_new.html', context_instance=context)


@permission_required('sundog.import_files')
def file_import(request):
    if request.method == 'POST' and request.FILES:
        try:
            input_excel = request.FILES['file']
            error = services.upload_import_file(input_excel, request.user)
        except Exception, e:
            error = "Error trying to access the import file."
            pass

        if error:
            return JsonResponse({'result': error})
        else:
            return JsonResponse({'result': 'OK'})

    context = RequestContext(request, {'request': request, 'user': request.user})
    return render_to_response('file/file_import.html', context_instance=context)


@permission_required('sundog.import_files')
def check_file_import(request):
    if request.method == 'POST' and request.FILES:
        error = None
        warning = None
        try:
            input_excel = request.FILES['file']
            # warn the user if the file checksum exists
            checksum_file = utils.md5_for_file(input_excel.chunks())
            checksum_exists = services.check_file_history_checksum(checksum_file)

            if checksum_exists:
                warning = "The import file seems to be already uploaded on the server. Do you want to continue?"

        except Exception, e:
            error = "Error trying to access the file import excel."
            pass

        if error:
            return JsonResponse({'error': error})
        else:
            if warning:
                return JsonResponse({'warning': warning})
            else:
                return JsonResponse({'result': 'OK'})

    raise Http404()


@permission_required('sundog.add_client')
def add_client_ajax(request):
    if request.method == 'POST' and request.POST:
        error = None
        new_client = None
        try:
            form_client = ClientForm(request.POST or None)
            if form_client.is_valid():
                new_client = form_client.save()
            else:
                error = []
                for field in form_client:
                    if field.errors:
                        for field_error in field.errors:
                            error.append(strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error)
                for non_field_error in form_client.non_field_errors():
                    error.append(non_field_error)

        except Exception, e:
            error = "Error trying to save the new client."
            pass

        if error:
            return JsonResponse({'error': error})
        else:
            return JsonResponse({'result': {
                'client_id': new_client.client_id,
                'name': new_client.name
            }})

    raise Http404()


@permission_required('sundog.import_files')
def download_file_import_sample(request):
    path_to_file = os.path.join(settings.PROJECT_ROOT, 'import', 'sample', IMPORT_FILE_EXCEL_FILENAME)
    f = open(path_to_file, 'rb')
    myfile = File(f)
    response = HttpResponse(myfile, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=%s' % IMPORT_FILE_EXCEL_FILENAME
    response['Content-Length'] = os.path.getsize(path_to_file)
    return response


@permission_required('sundog.import_clients')
def client_import(request):
    if request.method == 'POST' and request.FILES:
        try:
            input_excel = request.FILES['file']
            error = services.upload_import_client(input_excel, request.user)
        except Exception, e:
            error = "Error trying to access the import excel file."
            pass

        if error:
            return JsonResponse({'result': error})
        else:
            return JsonResponse({'result': 'OK'})

    context = RequestContext(request, {'request': request, 'user': request.user})
    return render_to_response('client/client_import.html', context_instance=context)


@permission_required('sundog.import_clients')
def check_client_import(request):
    if request.method == 'POST' and request.FILES:
        error = None
        warning = None
        try:
            input_excel = request.FILES['file']
            # warn the user if the file checksum exists
            checksum_file = utils.md5_for_file(input_excel.chunks())
            checksum_exists = services.check_file_history_checksum(checksum_file)

            if checksum_exists:
                warning = "The import excel file seems to be already uploaded on the server. Do you want to continue?"

        except Exception, e:
            error = "Error trying to access the import excel file."
            pass

        if error:
            return JsonResponse({'error': error})
        else:
            if warning:
                return JsonResponse({'warning': warning})
            else:
                return JsonResponse({'result': 'OK'})

    raise Http404()


@permission_required('sundog.import_clients')
def download_client_import_sample(request):
    path_to_file = os.path.join(settings.PROJECT_ROOT, 'import', 'sample', IMPORT_CLIENT_EXCEL_FILENAME)
    f = open(path_to_file, 'rb')
    myfile = File(f)
    response = HttpResponse(myfile, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=%s' % IMPORT_CLIENT_EXCEL_FILENAME
    response['Content-Length'] = os.path.getsize(path_to_file)
    return response


@permission_required('sundog.change_file')
def documents_upload(request, file_id):
    if request.method == 'POST' and request.FILES:
        my_file = services.get_file_by_id_for_user(file_id, request.user)
        if my_file:
            document = Document(document=request.FILES['file'], file=my_file)
            document.save()
            return JsonResponse({'document_id': document.pk})
    raise Http404()


@permission_required('sundog.change_file_participant')
def file_remove_participant(request, file_id):
    if request.method == 'POST' and request.POST and file_id:
        if request.POST["user_id"]:
            user_id = request.POST["user_id"]
            user = User.objects.get(id=user_id)
            my_file = services.get_file_by_id_for_user(file_id, request.user)
            if my_file and user:
                my_file.participants.remove(user)
                my_file.save()
                return redirect('file_edit', file_id=file_id)

    return redirect('file_edit', file_id=file_id, message=messages.MESSAGE_REQUEST_FAILED)


@permission_required('sundog.change_file_participant')
def file_add_participant(request, file_id):
    my_file = services.get_file_by_id_for_user(file_id, request.user)
    if my_file and request.method == 'POST' and request.POST:
        if request.POST.getlist('new_participants'):
            new_participants = request.POST.getlist('new_participants')
            users = list(services.get_users_by_ids(new_participants))
            my_file.participants.add(*users)
            my_file.save()
            return redirect('file_edit', file_id=file_id)

    return redirect('file_edit', file_id=file_id, message=messages.MESSAGE_REQUEST_FAILED)


@permission_required('sundog.change_file')
def documents_delete(request, document_id):
    if request.method == 'POST' and document_id:
        db_doc = Document.objects.get(pk=document_id)

        # delete from FS
        if os.path.isfile(db_doc.document.path):
            os.remove(db_doc.document.path)
        # delete from DB
        db_doc.delete()
        return JsonResponse({'result': 'OK'})

    raise Http404()


@login_required()
def messages_upload(request, file_id):
    if request.method == 'POST' and request.POST:
        my_file = services.get_file_by_id_for_user(file_id, request.user)
        if my_file:
            message = Message(message=request.POST['message'])
            message.time = datetime.now()
            message.user = request.user
            message.save()
            my_file.messages.add(message)
            my_file.save()
            # change to localtime
            message_time = utils.set_date_to_user_timezone(message.time, request.user.id)
            return JsonResponse({'message': {
                'time': utils.format_date(message_time),
                'user_full_name': message.user.get_full_name()
            }})
    raise Http404()


class FileSearchView(SearchView):
    form_class = FileSearchForm
    template_name = 'home.html'

    def get_queryset(self):
        queryset = super(FileSearchView, self).get_queryset()
        participants = False
        try:
            radio_field = self.request.GET['radio_field']
            if radio_field == '1':
                participants = True
        except:
            pass
        if not self.request.user.is_superuser:
            # filter file for status permission
            permissions_name_array = services.get_user_status_permissions(self.request.user)

            # filter permission to view all files or only files where the user is participant
            if not self.request.user.has_perm('sundog.view_all_files') or participants:
                queryset = queryset.filter(status__in=permissions_name_array,
                                           participants=self.request.user.id)
            else:
                queryset = queryset.filter(status__in=permissions_name_array)
        else:
            if participants:
                queryset = queryset.filter(participants=self.request.user.id)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(FileSearchView, self).get_context_data(*args, **kwargs)
        # do something
        status_result = services.get_files_by_status_count(self.request.user)
        status_results_json = []
        status_names = []
        date_row = None
        dict_row = None
        for row in status_result:
            if not row.file_status.title() in status_names:
                status_names.append(row.file_status.title())
            if not date_row:
                dict_row = {'day': str(row.date_stat)}
                date_row = row.date_stat

            if date_row == row.date_stat:
                dict_row[row.file_status.title()] = row.file_count
            else:
                status_results_json.append(dict_row)
                date_row = None
        if dict_row:
            status_results_json.append(dict_row)
        context['chart_data'] = status_results_json
        context['chart_status_names'] = status_names
        return context

    def get_form(self, form_class=None):
        form = super(FileSearchView, self).get_form(form_class)
        form.fields['status'].queryset = services.get_status_list_by_user(self.request.user)

        return form

