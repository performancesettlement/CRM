import copy
import json
import smtplib
import chardet
from django.core import mail
from django.core.paginator import Paginator
import sys
from django_auth_app.utils import serialize_user
from django.shortcuts import render_to_response, redirect
from django.template.context import RequestContext
from django.contrib.auth.decorators import permission_required, user_passes_test, login_required
from django.http import Http404, StreamingHttpResponse
from django.http.response import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from django.core.files import File
from django_auth_app.views import login_user
import settings
import os
import logging
from sundog import services
from sundog import utils
from sundog import messages
from sundog.cache.user.info import get_cache_user
from sundog.constants import IMPORT_FILE_EXCEL_FILENAME, IMPORT_CLIENT_EXCEL_FILENAME, MY_CONTACTS, ALL_CONTACTS
from django.contrib.auth.models import Permission
from haystack.generic_views import SearchView
from sundog.decorators import bypass_impersonation_login_required
from sundog.forms import FileCustomForm, FileSearchForm, ContactForm, ImpersonateUserForm, StageForm, StatusForm, \
    CampaignForm, SourceForm, ContactStatusForm, BankAccountForm, NoteForm, CallForm, EmailForm, UploadedForm, \
    ExpensesForm, IncomesForm, CreditorForm, DebtForm, DebtNoteForm, EnrollmentPlanForm, FeeForm, FeeProfileForm, \
    FeeProfileRuleForm
from datetime import datetime
from sundog.messages import MESSAGE_REQUEST_FAILED_CODE, CODES_TO_MESSAGE
from sundog.models import MyFile, Message, Document, FileStatusHistory, Contact, Stage, STAGE_TYPE_CHOICES, Status, \
    Campaign, BankAccount, Activity, Uploaded, Expenses, Incomes, Creditor, Debt, DebtNote, Enrollment, EnrollmentPlan, \
    FeeProfile, FeeProfileRule
from sundog.services import reorder_stages, reorder_status
from sundog.utils import get_form_errors, get_data

logger = logging.getLogger(__name__)


def _render_response(request, context_info, template_path):
    context = RequestContext(request, context_info)
    return render_to_response(template_path, context_instance=context)


def index(request):
    context_info = {'request': request, 'user': request.user}
    if settings.INDEX_PAGE.endswith(".html"):
        return _render_response(request, context_info, settings.INDEX_PAGE)
    else:
        return HttpResponseRedirect(settings.INDEX_PAGE)


@login_required
def list_contacts(request):
    order_by_list = ['type', 'created_at', 'company', 'assigned_to', 'last_name,first_name', 'phone_number', 'email',
                     'stage', 'status']
    page = int(request.GET.get('page', '1'))
    selected_list = request.GET.get('selected_list', MY_CONTACTS)
    order_by = request.GET.get('order_by', 'created_at')

    if order_by in order_by_list:
        i = order_by_list.index(order_by)
        order_by_list[i] = '-' + order_by

    sort = {'name': order_by.replace('-', ''), 'class': 'sorting_desc' if order_by.find('-') else 'sorting_asc'}

    if order_by == 'last_name,first_name':
        order_by = ['last_name', 'first_name']
    elif order_by == '-last_name,first_name':
        order_by = ['-last_name', '-first_name']
    else:
        order_by = [order_by]

    contacts_filter = {}
    if MY_CONTACTS == selected_list:
        contacts_filter['assigned_to'] = request.user

    contacts = Contact.objects.filter(**contacts_filter).order_by(*order_by)
    paginator = Paginator(contacts, 100)
    page = paginator.page(page)
    lists = [
        ('My Contacts', MY_CONTACTS),
        ('All Contacts', ALL_CONTACTS),
    ]

    context_info = {
        'sort': sort,
        'selected_list': selected_list,
        'order_by_list': order_by_list,
        'request': request,
        'user': request.user,
        'page': page,
        'paginator': paginator,
        'lists': lists,
        'menu_page': 'contacts'
    }
    template_path = 'contact/contact_list.html'
    return _render_response(request, context_info, template_path)


@login_required
def contact_dashboard(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').get(contact_id=contact_id)
    bank_account = contact.bank_account.all() if contact else None
    bank_account = bank_account[0] if bank_account else None
    form_bank_account = BankAccountForm(instance=bank_account)
    form_bank_account.fields['contact'].initial = contact
    form_note = NoteForm(contact, request.user)
    form_call = CallForm(contact, request.user)
    form_email = EmailForm(contact, request.user)
    form_upload = UploadedForm(contact, request.user)
    form_expenses = ExpensesForm(contact)
    form_incomes = IncomesForm(contact)
    form_debt_note = DebtNoteForm()
    e_signed_docs = list(contact.e_signed_docs.all())
    generated_docs = list(contact.generated_docs.all())
    uploaded_docs = list(contact.uploaded_docs.all())
    enrolled_debts = contact.contact_debts.filter(enrolled=True)
    not_enrolled_debts = contact.contact_debts.filter(enrolled=False)
    activities = Activity.objects.filter(contact__contact_id=contact_id)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'form_bank_account': form_bank_account,
        'form_note': form_note,
        'form_call': form_call,
        'form_email': form_email,
        'form_upload': form_upload,
        'form_incomes': form_incomes,
        'form_expenses': form_expenses,
        'form_debt_note': form_debt_note,
        'activities': activities,
        'e_signed_docs': e_signed_docs,
        'generated_docs': generated_docs,
        'uploaded_docs': uploaded_docs,
        'enrolled_debts': enrolled_debts,
        'not_enrolled_debts': not_enrolled_debts,
        'menu_page': 'contacts',
    }
    template_path = 'contact/contact_dashboard.html'
    return _render_response(request, context_info, template_path)


@login_required
def budget_analysis(request, contact_id):
    contact = Contact.objects.get(contact_id=contact_id)
    try:
        incomes = Incomes.objects.get(contact__contact_id=contact_id)
    except Incomes.DoesNotExist as e:
        incomes = None
    try:
        expenses = Expenses.objects.get(contact__contact_id=contact_id)
    except Expenses.DoesNotExist as e:
        expenses = None
    form_incomes = IncomesForm(contact, instance=incomes)
    form_expenses = ExpensesForm(contact, instance=expenses)

    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'form_incomes': form_incomes,
        'form_expenses': form_expenses,
        'menu_page': 'contacts',
    }
    template_path = 'contact/budget_analysis.html'
    return _render_response(request, context_info, template_path)


@login_required
def budget_analysis_save(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        try:
            incomes = Incomes.objects.get(contact__contact_id=contact_id)
        except Incomes.DoesNotExist as e:
            incomes = None
        form_incomes = IncomesForm(contact, request.POST, instance=incomes)
        try:
            expenses = Expenses.objects.get(contact__contact_id=contact_id)
        except Expenses.DoesNotExist as e:
            expenses = None
        form_expenses = ExpensesForm(contact, request.POST, instance=expenses)
        form_errors = []
        if not form_incomes.is_valid():
            for field in form_incomes:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form_incomes.non_field_errors():
                form_errors.append(non_field_error)
        if not form_expenses.is_valid():
            for field in form_expenses:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form_expenses.non_field_errors():
                form_errors.append(non_field_error)
        if not form_errors:
            form_incomes.save()
            form_expenses.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def delete_budget_analysis(request, contact_id):
    if request.method == 'DELETE':
        try:
            expenses = Expenses.objects.get(contact__contact_id=contact_id)
            expenses.delete()
        except Expenses.DoesNotExist as e:
            pass
        try:
            incomes = Incomes.objects.get(contact__contact_id=contact_id)
            incomes.delete()
        except Incomes.DoesNotExist as e:
            pass
        return JsonResponse({'result': 'Ok'})


@login_required
def add_note(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = NoteForm(contact, request.user, request.POST)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def add_email(request, contact_id):
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        contact = Contact.objects.get(contact_id=contact_id)
        files = request.FILES
        if files:
            attachment = ''
            for file in files.values():
                if attachment:
                    attachment += ',' + file.name
                else:
                    attachment += file.name
            post_data['attachment'] = attachment
        form = EmailForm(contact, request.user, post_data)
        form_errors = []
        if form.is_valid():
            email_data = form.cleaned_data
            emails_to = []
            for email_to in email_data['emails_to'].split(','):
                emails_to.append(email_to.strip())
            email = mail.EmailMessage(
                email_data['subject'],
                email_data['message'],
                email_data['email_from'],
                emails_to,
            )
            for file in files.values():
                email.attach(file.name, file.read(), file.content_type)
            try:
                email.send()
                form.save()
            except Exception as e:
                form_errors.append('There was a error sending the email')
            if form_errors:
                response = {'errors': form_errors}
            else:
                response_data = 'Ok'
                response = {'result': response_data}
        else:
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def upload_file(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = UploadedForm(contact, request.user, request.POST, request.FILES)
        form_errors = []
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def add_call(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = CallForm(contact, request.user, request.POST)
        form_errors = []
        if form.is_valid():
            contact_status = form.cleaned_data.pop('contact_status')
            form.save()
            if contact_status and contact.status.status_id != contact_status.status_id:
                status_form = ContactStatusForm({'contact_id': contact_id, 'status': contact_status.status_id, 'stage': contact_status.stage.stage_id}, instance=contact)
                status_form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


def uploaded_file_view(request, contact_id, uploaded_id):
    doc = Uploaded.objects.get(uploaded_id=uploaded_id)
    with open(doc.content.path, 'rb') as file:
        if doc.get_type() == 'pdf':
            response = HttpResponse(file.read(), content_type=doc.mime_type)
            response['Content-Disposition'] = 'inline; filename=%s' % doc.name
        else:
            response = HttpResponse()
        return response


def uploaded_file_download(request, contact_id, uploaded_id):
    doc = Uploaded.objects.get(uploaded_id=uploaded_id)
    response = HttpResponse(doc.content, content_type=doc.mime_type)
    response['Content-Disposition'] = 'attachment; filename=%s' % doc.name
    response['Content-Length'] = os.path.getsize(doc.content.path)
    return response


def uploaded_file_delete(request, contact_id, uploaded_id):
    if request.method == 'DELETE':
        doc = Uploaded.objects.get(uploaded_id=uploaded_id)
        os.remove(doc.content.path)
        doc.delete()
        return JsonResponse({'result': 'Ok'})


@login_required
def workflows(request):
    if not request.GET or 'type' not in request.GET:
        type = STAGE_TYPE_CHOICES[0][0]
    else:
        type = request.GET['type']
    form_stage = StageForm()
    edit_form_stage = StageForm()
    form_status = StatusForm(type)
    edit_form_status = StatusForm(type)
    stages = Stage.objects.all()
    stage_types = STAGE_TYPE_CHOICES

    context_info = {
        'request': request,
        'user': request.user,
        'form_stage': form_stage,
        'form_status': form_status,
        'edit_form_status': edit_form_status,
        'edit_form_stage': edit_form_stage,
        'stages': stages,
        'stage_types': stage_types,
        'stage_type': type,
        'menu_page': 'contacts'
    }
    template_path = 'contact/workflows.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_stage(request):
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        post_data.pop('stage_type')
        form = StageForm(post_data)
        if form.is_valid():
            stages = list(Stage.objects.all())
            previous_last_order = len(stages)
            stage = form.save(commit=False)
            stage.order = previous_last_order + 1
            stage.save()
            stage_data = 'Ok'
            response = {'result': stage_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def edit_stage(request):
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        post_data.pop('stage_type')
        stage_id = post_data['stage_id']
        instance = Stage.objects.get(stage_id=stage_id)
        form = StageForm(post_data, instance=instance)
        if form.is_valid():
            form.save()
            status_data = 'Ok'
            response = {'result': status_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def add_status(request):
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        type = post_data.pop('stage_type')[0]
        form = StatusForm(type, post_data)
        if form.is_valid():
            stage_id = request.POST['stage']
            statuses = list(Status.objects.filter(stage__stage_id=stage_id))
            previous_last_order = len(statuses)
            status = form.save(commit=False)
            status.order = previous_last_order + 1
            status.save()
            status_data = 'Ok'
            response = {'result': status_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def edit_status(request):
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        type = post_data.pop('stage_type')[0]
        status_id = request.POST['status_id']
        instance = Status.objects.get(status_id=status_id)
        form = StatusForm(type, post_data, instance=instance)
        if form.is_valid():
            form.save()
            status_data = 'Ok'
            response = {'result': status_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def update_stage_order(request):
    if not request.is_ajax():
        redirect('home') # TODO: handle this a generic way perhaps
    response = {'result': None}
    if request.method == 'POST' and request.POST:
        new_order = copy.copy(request.POST)
        new_order.pop('csrfmiddlewaretoken')
        new_order_list = []
        for i in range(0, len(new_order)):
            stage_id_str = new_order[str(i)]
            new_order_list.append(int(stage_id_str))
        reorder_stages(new_order_list)
        response['result'] = 'Ok'
    return JsonResponse(response)


@login_required
def update_status_order(request):
    if not request.is_ajax():
        redirect('home')  # TODO: handle this a generic way perhaps
    response = {'result': None}
    if request.method == 'POST' and request.POST:
        new_order = copy.copy(request.POST)
        new_order.pop('csrfmiddlewaretoken')
        stage_id = new_order.pop('stageId')[0]
        new_order_list = []
        for i in range(0, len(new_order)):
            stage_id_str = new_order[str(i)]
            new_order_list.append(int(stage_id_str))
        reorder_status(new_order_list, stage_id)
        response['result'] = 'Ok'
    return JsonResponse(response)


@login_required
def campaigns(request):
    order_by_list = [
        'active',
        'created_at',
        'created_by',
        'title',
        'source',
        'cost',
        'priority',
        'media_type',
        'purchase_amount'
    ]
    page = int(request.GET.get('page', '1'))
    order_by = request.GET.get('order_by', 'created_at')

    if order_by in order_by_list:
        index = order_by_list.index(order_by)
        order_by_list[index] = '-' + order_by

    sort = {'name': order_by.replace('-', ''), 'class': 'sorting_desc' if order_by.find('-') else 'sorting_asc'}
    order_by = [order_by]

    form_campaign = CampaignForm()
    edit_form_campaign = CampaignForm()
    form_source = SourceForm()
    campaign_list = Campaign.objects.all().order_by(*order_by)
    paginator = Paginator(campaign_list, 100)
    page = paginator.page(page)

    context_info = {
        'request': request,
        'user': request.user,
        'sort': sort,
        'order_by_list': order_by_list,
        'form_source': form_source,
        'form_campaign': form_campaign,
        'edit_form_campaign': edit_form_campaign,
        'paginator': paginator,
        'page': page,
        'menu_page': 'contacts'
    }
    template_path = 'contact/campaigns.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_campaign(request):
    if request.method == 'POST' and request.POST:
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def edit_campaign(request):
    if request.method == 'POST' and request.POST:
        campaign_id = request.POST['campaign_id']
        instance = Campaign.objects.get(campaign_id=campaign_id)
        form = CampaignForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def add_source(request):
    if request.method == 'POST' and request.POST:
        form = SourceForm(request.POST)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def add_contact(request):
    form_errors = None
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            return redirect('list_contacts')
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': form_errors,
        'templates':  [('Add a Client', 'add_a_client')],
        'label': 'Add',
        'menu_page': 'contacts',
    }
    template_path = 'contact/contact.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_contact(request, contact_id):
    form_errors = []
    instance = Contact.objects.get(contact_id=contact_id)
    form = ContactForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            return redirect('list_contacts')
        else:
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'contact_id': contact_id,
        'form_errors': form_errors,
        'templates':  [('Add a Client', 'add_a_client')],
        'label': 'Edit',
        'menu_page': 'contacts'
    }
    template_path = 'contact/contact.html'
    return _render_response(request, context_info, template_path)


@login_required
def delete_contact(request, contact_id):
    if request.method == 'DELETE':
        try:
            contact = Contact.objects.get(contact_id=contact_id)
            contact.delete()
        except Contact.DoesNotExist as e:
            pass
        except Exception:
            return JsonResponse({'result': 'error'})
        return JsonResponse({'result': 'Ok'})


@login_required
def get_stage_statuses(request):
    if request.POST and 'stage_id' in request.POST:
        stage_id = request.POST['stage_id']
        statuses = [{'id': status.status_id, 'name': status.name} for status in list(Status.objects.filter(stage__stage_id=stage_id))]
        return JsonResponse({'statuses': statuses})


@login_required
def edit_bank_account(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        bank_account = contact.bank_account.all() if contact else None
        bank_account = bank_account[0] if bank_account else None
        if bank_account:
            form = BankAccountForm(request.POST, instance=bank_account)
        else:
            form = BankAccountForm(request.POST)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def edit_contact_status(request, contact_id):
    form_errors = None
    instance = Contact.objects.get(contact_id=contact_id)
    form = ContactStatusForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            return redirect('list_contacts')
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': instance,
        'form': form,
        'form_errors': form_errors,
        'menu_page': 'contacts'
    }
    template_path = 'contact/edit_contact_status.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_lead_source(request):
    form_errors = None
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            lead_source = form.save()
            # TODO: redirect to lead sources list?
            return redirect('home')
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': form_errors,
    }
    template_path = 'lead_source/add_lead_source.html'
    return _render_response(request, context_info, template_path)


@login_required
def creditors_list(request):
    order_by_list = ['name', 'address_1', 'city', 'state', 'zip_code', 'debtors', 'total_debts', 'avg']
    page = int(request.GET.get('page', '1'))
    order_by = request.GET.get('order_by', 'name')
    sort = {'name': order_by.replace('-', ''), 'class': 'sorting_desc' if order_by.find('-') else 'sorting_asc'}
    if order_by in order_by_list:
        i = order_by_list.index(order_by)
        order_by_list[i] = '-' + order_by
    query = Creditor.objects.prefetch_related('creditor_debts').prefetch_related('bought_debts')
    if order_by.replace('-', '') not in ['debtors', 'total_debts', 'avg']:
        order_by = [order_by]
        contacts = query.all().order_by(*order_by)
    else:
        contacts = query.all()
        if order_by == 'total_debts':
            contacts.sort(key=lambda c: c.total_debts())
        elif order_by == '-total_debts':
            contacts.sort(key=lambda c: -c.total_debts())
        elif order_by == 'debtors':
            contacts.sort(key=lambda c: c.total_debtors())
        elif order_by == '-debtors':
            contacts.sort(key=lambda c: -c.total_debtors())
        elif order_by == 'avg':
            contacts.sort(key=lambda c: c.avg_settled())
        elif order_by == '-avg':
            contacts.sort(key=lambda c: -c.avg_settled())

    paginator = Paginator(contacts, 20)
    page = paginator.page(page)
    context_info = {
        'sort': sort,
        'order_by_list': order_by_list,
        'request': request,
        'user': request.user,
        'page': page,
        'paginator': paginator,
        'menu_page': 'creditors'
    }
    template_path = 'creditor/creditors_list.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_creditor(request):
    form_errors = None
    form = CreditorForm(request.POST or None)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            return redirect('creditors_list')
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': form_errors,
        'menu_page': 'creditors',
    }
    template_path = 'creditor/add_creditor.html'
    return _render_response(request, context_info, template_path)


@login_required
def contact_debts(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').get(contact_id=contact_id)
    order_by_list = [
        'original_creditor',
        'debt_buyer',
        'original_creditor_account_number',
        'account_type',
        'current_debt_amount',
        'whose_debts',
        'current_payment',
        'last_payment',
        'notes',
        'enrolled',
    ]
    page = int(request.GET.get('page', '1'))
    order_by = request.GET.get('order_by', 'original_creditor')

    if order_by in order_by_list:
        i = order_by_list.index(order_by)
        order_by_list[i] = '-' + order_by

    sort = {'name': order_by.replace('-', ''), 'class': 'sorting_desc' if order_by.find('-') else 'sorting_asc'}
    query = Debt.objects.prefetch_related('notes').filter(contact__contact_id=contact_id)
    if order_by.replace('-', '') != 'notes':
        order_by = [order_by]
        debts = list(query.order_by(*order_by))
    else:
        debts = list(query)
        if order_by == 'notes':
            debts.sort(key=lambda d: d.notes_count())
        elif order_by == '-notes':
            debts.sort(key=lambda d: -d.notes_count())

    form_debt = DebtForm(contact)
    form_edit_debt = DebtForm(contact)
    paginator = Paginator(debts, 20)
    page = paginator.page(page)

    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'sort': sort,
        'order_by_list': order_by_list,
        'form_debt': form_debt,
        'form_edit_debt': form_edit_debt,
        'paginator': paginator,
        'page': page,
        'menu_page': 'contacts'
    }
    template_path = 'contact/contact_debts.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_debt(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = DebtForm(contact, request.POST)
        if form.is_valid():
            note_content = form.cleaned_data['note']
            debt = form.save()
            if note_content:
                debt_note = DebtNote(content=note_content, debt=debt)
                debt_note.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def edit_debt(request, contact_id):
    if request.method == 'POST' and request.POST:
        debt_id = request.POST.get('debt_id')
        contact = Contact.objects.get(contact_id=contact_id)
        instance = Debt.objects.get(debt_id=debt_id)
        form = DebtForm(contact, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def edit_debt_enrolled(request, contact_id):
    if request.method == 'POST' and request.POST:
        debt_id = request.POST.get('debt_id')
        enrolled_string = request.POST.get('enrolled')
        response = {}
        if enrolled_string is not None:
            enrolled = True if enrolled_string == 'true' else False
            debt = Debt.objects.get(debt_id=debt_id)
            debt.enrolled = enrolled
            debt.save()
            response_data = 'Ok'
            response['result'] = response_data
        return JsonResponse(response)


def debt_add_note(request):
    if request.method == 'POST' and request.POST:
        form = DebtNoteForm(request.POST)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
            response = {'errors': form_errors}
        return JsonResponse(response)


def add_enrollment_plan(request):
    form_errors = None
    form_fee_1 = FeeForm(prefix='1')
    form_fee_2 = FeeForm(prefix='2')
    form = EnrollmentPlanForm(request.POST)
    enrollment_plans = EnrollmentPlan.objects.all()
    if request.method == 'POST' and request.POST:
        form_fee_1 = FeeForm(get_data('1', request.POST), prefix='1')
        fee_data_2 = get_data('2', request.POST)
        if fee_data_2:
            form_fee_2 = FeeForm(request.POST, prefix='2')
        if form.is_valid() and form_fee_1.is_valid() and (not fee_data_2 or (fee_data_2 and form_fee_2.is_valid())):
            enrollment_plan = form.save()
            fee_1 = form_fee_1.save(commit=False)
            fee_1.enrollment_plan = enrollment_plan
            fee_1.save()
            if fee_data_2:
                fee_2 = form_fee_2.save(commit=False)
                fee_2.enrollment_plan = enrollment_plan
                fee_2.save()
            return redirect('edit_enrollment_plan', enrollment_plan_id=enrollment_plan.enrollment_plan_id)
        else:
            form_errors = get_form_errors(form) + get_form_errors(form_fee_1)
            if fee_data_2:
                form_errors += get_form_errors(form_fee_2)
    plans = [('', '--New Plan--')] + [(plan.enrollment_plan_id, plan.name) for plan in enrollment_plans]
    has_second_fee = form_errors and next((x for x in form_errors if '2-' in x), False)
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_fee_1': form_fee_1,
        'form_fee_2': form_fee_2,
        'form_errors': form_errors,
        'has_second_fee': has_second_fee,
        'plans': plans,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/add_enrollment_plan.html'
    return _render_response(request, context_info, template_path)


def edit_enrollment_plan(request, enrollment_plan_id):
    form_errors = None
    instance = EnrollmentPlan.objects.get(enrollment_plan_id=int(enrollment_plan_id))
    form = EnrollmentPlanForm(request.POST or None, instance=instance)
    fees = list(instance.fees.all())
    fee_count = len(fees)
    form_fee_1 = FeeForm(prefix='1', instance=fees[0])
    enrollment_plans = EnrollmentPlan.objects.all()
    if request.method == 'POST' and request.POST:
        form_fee_1 = FeeForm(get_data('1', request.POST), prefix='1', instance=fees[0])
        fee_data_2 = get_data('2', request.POST)
        if fee_data_2 and fee_count == 1:
            form_fee_2 = FeeForm(request.POST, prefix='2')
        elif fee_count > 1 and fee_data_2:
            form_fee_2 = FeeForm(request.POST, instance=fees[1], prefix='2')
        if form.is_valid() and form_fee_1.is_valid() and (not fee_data_2 or (fee_data_2 and form_fee_2.is_valid())):
            enrollment_plan = form.save()
            fee_1 = form_fee_1.save(commit=False)
            fee_1.enrollment_plan = enrollment_plan
            fee_1.save()
            if fee_data_2:
                fee_2 = form_fee_2.save(commit=False)
                fee_2.enrollment_plan = enrollment_plan
                fee_2.save()
            elif fee_count == 2 and not fee_data_2:
                fees[1].delete()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            form_errors = get_form_errors(form) + get_form_errors(form_fee_1)
            if fee_data_2:
                form_errors += get_form_errors(form_fee_2)
            response = {'errors': form_errors}
        return JsonResponse(response)
    plans = [('', '--New Plan--')] + [(plan.enrollment_plan_id, plan.name) for plan in enrollment_plans]
    form_fee_2 = FeeForm(prefix='2')
    if len(fees) > 1:
        form_fee_2 = FeeForm(prefix='2', instance=fees[1])
    has_second_fee = (form_errors and next((x for x in form_errors if '2-' in x), False)) or (len(fees) > 1)
    context_info = {
        'request': request,
        'user': request.user,
        'enrollment_plan_id': int(enrollment_plan_id),
        'form': form,
        'form_fee_1': form_fee_1,
        'form_fee_2': form_fee_2,
        'form_errors': form_errors,
        'has_second_fee': has_second_fee,
        'plans': plans,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/edit_enrollment_plan.html'
    return _render_response(request, context_info, template_path)


def delete_enrollment_plan(request, enrollment_plan_id):
    if request.method == 'DELETE':
        try:
            EnrollmentPlan.objects.get(enrollment_plan_id=enrollment_plan_id).delete()
        except EnrollmentPlan.DoesNotExist as e:
            pass
        except Exception:
            return JsonResponse({'result': 'error'})
        return JsonResponse({'result': 'Ok'})


def add_fee_profile(request):
    form_errors = None
    forms_range = range(1, 11)
    profile_rules_forms = [FeeProfileRuleForm(get_data(str(i), request.POST), prefix=str(i)) for i in forms_range]
    form = FeeProfileForm(request.POST or None)
    fee_profiles = FeeProfile.objects.all()
    if request.method == 'POST' and request.POST:
        received_profile_rules_forms = []
        for i in forms_range:
            prefix = str(i)
            data = get_data(prefix, request.POST)
            if data:
                received_profile_rules_forms.append(FeeProfileRuleForm(data, prefix=prefix))
        if form.is_valid() and all([form.is_valid() for form in received_profile_rules_forms]):
            fee_profile = form.save()
            for form_rule in received_profile_rules_forms:
                rule = form_rule.save(commit=False)
                rule.fee_profile = fee_profile
                rule.save()
            return redirect('edit_fee_profile', fee_profile_id=fee_profile.fee_profile_id)
        else:
            list_of_error_lists = list((get_form_errors(form) for form in received_profile_rules_forms))
            form_errors = get_form_errors(form) + list(error for sub_list in list_of_error_lists for error in sub_list)
    profiles = [('', '--Add Profile--')] + [(profile.fee_profile_id, profile.name) for profile in fee_profiles]
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'profile_rules_forms': profile_rules_forms,
        'form_errors': form_errors,
        'profiles': profiles,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/add_fee_profile.html'
    return _render_response(request, context_info, template_path)


def edit_fee_profile(request, fee_profile_id):
    form_errors = None
    instance = FeeProfile.objects.prefetch_related('rules').get(fee_profile_id=fee_profile_id)
    rules = list(instance.rules.all())
    form = FeeProfileForm(request.POST or None, instance=instance)
    fee_profiles = FeeProfile.objects.all()
    profile_rules_forms = []
    remove_rules = []
    number_of_previous_rule_count = 0
    for rule in rules:
        number_of_previous_rule_count += 1
        prefix = str(number_of_previous_rule_count)
        data = get_data(prefix, request.POST)
        if not request.POST or (request.POST and data):
            profile_rules_forms.append(FeeProfileRuleForm(data, instance=rule, prefix=prefix))
        elif request.POST and not data:
            remove_rules.append(rule.fee_profile_rule_id)
    if request.method == 'POST' and request.POST:
        received_profile_rules_forms = []
        for i in range(number_of_previous_rule_count + 1, 11):
            prefix = str(i)
            data = get_data(prefix, request.POST)
            if data:
                received_profile_rules_forms.append(FeeProfileRuleForm(data, prefix=prefix))
        received_profile_rules_forms.extend(profile_rules_forms)
        if form.is_valid() and all([form.is_valid() for form in received_profile_rules_forms]):
            fee_profile = form.save()
            for form_rule in received_profile_rules_forms:
                rule = form_rule.save(commit=False)
                rule.fee_profile = fee_profile
                rule.save()
            if remove_rules:
                FeeProfileRule.objects.filter(fee_profile_rule_id__in=remove_rules).delete()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            list_of_error_lists = list((get_form_errors(form) for form in received_profile_rules_forms))
            form_errors = get_form_errors(form) + list(error for sub_list in list_of_error_lists for error in sub_list)
            response = {'errors': form_errors}
        return JsonResponse(response)
    profile_rules_forms += [FeeProfileRuleForm(get_data(str(i), request.POST), prefix=str(i)) for i in range(number_of_previous_rule_count + 1, 11)]
    profiles = [('', '--Add Profile--')] + [(profile.fee_profile_id, profile.name) for profile in fee_profiles]
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'profile_rules_forms': profile_rules_forms,
        'fee_profile_id': int(fee_profile_id),
        'form_errors': form_errors,
        'profiles': profiles,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/edit_fee_profile.html'
    return _render_response(request, context_info, template_path)


def delete_fee_profile(request, fee_profile_id):
    if request.method == 'DELETE':
        try:
            FeeProfile.objects.get(fee_profile_id=fee_profile_id).delete()
        except FeeProfile.DoesNotExist as e:
            pass
        except Exception:
            return JsonResponse({'result': 'error'})
        return JsonResponse({'result': 'Ok'})


def enrollments_list(request):
    order_by_list = ['full_name', 'state', 'next_payment', 'payments_made', 'balance', 'created_at']
    page = int(request.GET.get('page', '1'))
    order_by = request.GET.get('order_by', 'full_name')

    if order_by in order_by_list:
        i = order_by_list.index(order_by)
        order_by_list[i] = '-' + order_by

    sort = {'name': order_by.replace('-', ''), 'class': 'sorting_desc' if order_by.find('-') else 'sorting_asc'}
    query = Enrollment.objects.prefetch_related('contact')
    if order_by.replace('-', '') == 'created_at':
        order_by = [order_by]
        enrollments = list(query.order_by(*order_by))
    else:
        enrollments = list(query)
        if order_by == 'full_name':
            enrollments.sort(key=lambda d: d.contact.full_name_straight())
        elif order_by == '-full_name':
            enrollments.sort(key=lambda d: -d.contact.full_name_straight())
        elif order_by == 'next_payment':
            enrollments.sort(key=lambda d: d.next_payment().total_seconds() if d.next_payment() else 0)
        elif order_by == '-next_payment':
            enrollments.sort(key=lambda d: -d.next_payment().total_seconds() if d.next_payment() else sys.maxsize)
        elif order_by == 'payments_made':
            enrollments.sort(key=lambda d: d.payments_made())
        elif order_by == '-payments_made':
            enrollments.sort(key=lambda d: -d.payments_made())
        elif order_by == 'balance':
            enrollments.sort(key=lambda d: d.balance())
        elif order_by == '-balance':
            enrollments.sort(key=lambda d: -d.balance())

    paginator = Paginator(enrollments, 100)
    page = paginator.page(page)

    context_info = {
        'sort': sort,
        'order_by_list': order_by_list,
        'request': request,
        'user': request.user,
        'page': page,
        'paginator': paginator,
        'menu_page': 'enrollments'
    }
    template_path = 'enrollment/enrollments_list.html'
    return _render_response(request, context_info, template_path)

#######################################################################


@bypass_impersonation_login_required
def files_recent(request):
    recent_files_list = services.get_access_file_history(request.user)
    context_info = {'request': request, 'user': request.user, 'recent_files_list': recent_files_list}
    return _render_response(request, context_info, 'file/recent_files.html')


@bypass_impersonation_login_required
def help(request):
    context_info = {'request': request, 'user': request.user}
    return _render_response(request, context_info, 'file/recent_files.html')


def terms(request):
    return render_to_response('sundog/terms.html')


def render404(request):
    return render_to_response('404.html')


@bypass_impersonation_login_required
@user_passes_test(lambda u: u.is_superuser)
def display_log(request):
    try:
        log_file_path = os.path.join(settings.PROJECT_ROOT, 'log/sundog.log')
        content = open(log_file_path, 'r').read()
        response = StreamingHttpResponse(content)
        response['Content-Type'] = 'text/plain; charset=utf8'
        return response
    except Exception as e:
        logger.error("An error occurred trying to display the log.")
        logger.error(str(e))
        return HttpResponseRedirect(reverse("admin:index"))


@permission_required('auth.impersonate_user')
def impersonate_user(request):
    post_data = request.POST
    form = ImpersonateUserForm(id=request.user.id)
    context_info = {'request': request, 'form': form}
    template_path = 'impersonate_user.html'
    if post_data:
        impersonated_user_id = post_data.get('id')
        form_errors = []
        if impersonated_user_id:
            request.session["user_impersonation"] = True
            request.session["user_impersonator"] = serialize_user(request.user)
            try:
                impersonated_user = get_cache_user(impersonated_user_id)
                request.session["user_impersonated"] = serialize_user(impersonated_user)
                return redirect('home')
            except Exception as e:
                logger.error("An error occurred trying to impersonate user.")
                logger.error(str(e))
                form_errors.append("Invalid user for impersonation.")
        else:
            form_errors.append("User is required for impersonation.")
        context_info["form_errors"] = form_errors
        return _render_response(request, context_info, template_path)
    else:
        return _render_response(request, context_info, template_path)


@bypass_impersonation_login_required
def stop_impersonate_user(request):
    if request.session:
        user_impersonation = request.session.get("user_impersonation", False)
        if user_impersonation:
            request.session["user_impersonation"] = False
            request.session["user_impersonated"] = None
            request.session["user_impersonator"] = None
            return redirect('home')
        else:
            logger.error("An error occurred trying to stop impersonating user.")
            logger.error("There is no user being impersonated.")
            pass  # TODO: Return error no user impersonated


@bypass_impersonation_login_required
def erase_log(request):
    try:
        if request.POST:
            log_file_path = os.path.join(settings.PROJECT_ROOT, 'log/sundog.log')
            with open(log_file_path, 'w'):
                pass
            return JsonResponse({'result': 'OK'})
    except Exception as e:
        logger.error("An error occurred trying to delete the log.")
        logger.error(str(e))
        return JsonResponse({'result': 'An error occurred!'})


@bypass_impersonation_login_required
def file_detail(request, file_id):
    my_file = services.get_file_by_id_for_user(file_id, request.user)
    if my_file is None:
        raise Http404()
    else:
        if my_file == "Unavailable":
            context_info = {'request': request, 'user': request.user, 'file_id': file_id}
            template_path = 'file/file_disabled.html'
        else:
            documents = Document.objects.filter(file__file_id=file_id)
            client = Contact.objects.get(client_id=my_file.client.client_id)
            # print
            form_client = ContactForm(instance=client)
            documents_json = []
            if documents:
                documents_json = [
                    {
                        'size': t.document.size,
                        'name': t.document.name,
                        'url': t.document.url,
                        'id': t.pk
                    } for t in documents
                    ]
            context_info = {
                'request': request,
                'user': request.user,
                'opts': MyFile._meta,
                'file': my_file,
                'documents': documents_json,
                'form_client': form_client
            }
            template_path = 'file/file.html'
        return _render_response(request, context_info, template_path)


@permission_required('sundog.change_myfile')
def file_edit(request, file_id):
    error_code = 0
    if 'error_code' in request.session:
        error_code = request.session['error_code']
        request.session.pop('error_code')
    my_file = services.get_file_by_id_for_user(file_id, request.user)
    if my_file is None:
        raise Http404()
    else:
        if my_file == "Unavailable":
            context_info = {'request': request, 'user': request.user, 'file_id': file_id}
            template_path = 'file/file_form.html'
        else:
            form_errors = None
            if request.user.has_perm('sundog.add_client'):
                form_client = ContactForm()
            else:
                form_client = None
            current_status = my_file.current_status
            form = FileCustomForm(instance=my_file)
            form.fields['current_status'].queryset = services.get_status_list_by_user(request.user)

            documents = services.get_file_documents(file_id)
            documents_json = []
            users_json = []
            if documents:
                documents_json = [
                    {
                        'size': t.document.size,
                        'name': t.document.name,
                        'url': t.document.url,
                        'id': t.pk
                    } for t in documents
                ]
            users = services.get_participants_options_by_file(my_file, list(my_file.participants.all()))
            if users:
                users_json = [
                    {'full_name': u.get_full_name() if u.get_full_name() else u.username, 'id': u.pk} for u in users
                ]
            if request.method == 'POST' and request.POST:
                response = None
                form = FileCustomForm(request.POST, instance=my_file)
                form.fields['current_status'].queryset = services.get_status_list_by_user(request.user)
                if form.is_valid():
                    my_file = form.save(commit=False)
                    # TODO: MAKE SURE THE USER HAS CHANGE TAG PERMISSION
                    if current_status.status_id != my_file.current_status.status_id:
                        try:
                            user_impersonator = None
                            if hasattr(request, 'user_impersonator'):
                                user_impersonator = request.user_impersonator
                            file_status_history = FileStatusHistory()
                            file_status_history.create_new_file_status_history(
                                current_status, my_file.current_status, request.user, user_impersonator)
                            my_file.file_status_history.add(file_status_history)
                        except Exception as e:
                            logger.error(messages.ERROR_SAVE_FILE_HISTORY % my_file.file_id)
                            logger.error(e)

                    my_file.stamp_updated_values(request.user)
                    if 'description' in form.changed_data:
                        current_permission = Permission.objects.get(codename=my_file.get_permission_codename())
                        try:
                            current_permission.codename = my_file.get_permission_codename()
                            current_permission.name = my_file.get_permission_name()
                            current_permission.save()
                        except Exception as e:
                            logger.error(messages.ERROR_MODIFY_STATUS_PERMISSION % my_file.name)
                            logger.error(e)
                    actual_file = MyFile.objects.get(file_id=file_id)
                    if actual_file.get_hashcode() == request.POST.get('hashcode') or request.POST.get('override'):
                        form.save_m2m()
                        my_file.save()
                        response = {"noChanges": True}
                    else:
                        response = {"noChanges": False, "changedBy": my_file.last_update_user_username}
                else:
                    form_errors = []
                    for field in form:
                        if field.errors:
                            for field_error in field.errors:
                                form_errors.append(strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error)
                    for non_field_error in form.non_field_errors():
                        form_errors.append(non_field_error)
                    response = {"form_errors": form_errors}
                return HttpResponse(json.dumps(response), content_type="application/json")
            context_info = {
                'request': request, 'user': request.user, 'form': form, 'file_id': file_id, 'opts': MyFile._meta,
                'file': my_file, 'documents': documents_json, 'message': CODES_TO_MESSAGE[error_code],
                'participant_options': users_json, 'form_errors': form_errors, 'form_client': form_client,
            }
            template_path = 'file/file_form.html'
        return _render_response(request, context_info, template_path)


@permission_required('sundog.add_myfile')
def file_add(request):
    form_errors = None
    form = FileCustomForm(request.POST or None)
    form.fields['current_status'].queryset = services.get_status_list_by_user(request.user)
    if request.user.has_perm('sundog.add_client'):
        form_client = ContactForm()
    else:
        form_client = None
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            my_file = form.save(commit=False)
            my_file.stamp_created_values(request.user)
            my_file.save()
            try:
                user_impersonator = None
                if hasattr(request, 'user_impersonator'):
                    user_impersonator = request.user_impersonator
                services.create_file_permission(my_file)
                file_status_history = FileStatusHistory()
                file_status_history.create_new_file_status_history(
                    None, my_file.current_status, request.user, user_impersonator)
                my_file.file_status_history.add(file_status_history)
            except Exception as e:
                logger.error(messages.ERROR_SAVE_FILE_HISTORY % my_file.file_id)
                logger.error(e)

            return redirect('file_detail', file_id=my_file.file_id)
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        error = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)

    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_client': form_client,
        'form_errors': form_errors
    }
    template_path = 'file/file_new.html'
    return _render_response(request, context_info, template_path)


@permission_required('sundog.import_files')
def file_import(request):
    if request.method == 'POST' and request.FILES:
        user_impersonator = None
        if hasattr(request, 'user_impersonator'):
            user_impersonator = request.user_impersonator
        try:
            input_excel = request.FILES['file']
            error = services.upload_import_file(input_excel, request.user, user_impersonator)
        except Exception:
            error = "Error trying to access the import file."
        if error:
            return JsonResponse({'result': error})
        else:
            return JsonResponse({'result': 'OK'})
    context_info = {'request': request, 'user': request.user}
    template_path = 'file/file_import.html'
    return _render_response(request, context_info, template_path)


@permission_required('sundog.import_files')
def check_file_import(request):
    if request.method == 'POST' and request.FILES:
        error = None
        warning = None
        try:
            input_excel = request.FILES['file']
            checksum_file = utils.md5_for_file(input_excel.chunks())
            checksum_exists = services.check_file_history_checksum(checksum_file)
            if checksum_exists:
                warning = "The import file seems to be already uploaded on the server. Do you want to continue?"
        except Exception:
            error = "Error trying to access the file import excel."
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
        instance = None
        try:
            data = request.POST
            if "client_id" in data:
                instance = Contact.objects.filter(client_id=data["client_id"])
            if instance and len(instance) > 0:
                form_client = ContactForm(data, instance=instance[0])
            else:
                form_client = ContactForm(data)

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
        except Exception:
            error = "Error trying to save the new client."
        if error:
            return JsonResponse({'error': error})
        else:
            return JsonResponse({'result': {'client_id': new_client.client_id, 'name': new_client.first_name}})
    raise Http404()


@permission_required('sundog.import_files')
def download_file_import_sample(request):
    path_to_file = os.path.join(settings.PROJECT_ROOT, 'import', 'sample', IMPORT_FILE_EXCEL_FILENAME)
    f = open(path_to_file, 'rb')
    my_file = File(f)
    response = HttpResponse(my_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=%s' % IMPORT_FILE_EXCEL_FILENAME
    response['Content-Length'] = os.path.getsize(path_to_file)
    return response


@permission_required('sundog.import_clients')
def client_import(request):
    if request.method == 'POST' and request.FILES:
        try:
            user_impersonator = None
            if hasattr(request, 'user_impersonator'):
                user_impersonator = request.user_impersonator
            input_excel = request.FILES['file']
            error = services.upload_import_client(input_excel, request.user, user_impersonator)
        except Exception as e:
            error = "Error trying to access the import excel file."
        if error:
            return JsonResponse({'result': error})
        else:
            return JsonResponse({'result': 'OK'})

    context_info = {'request': request, 'user': request.user}
    template_path = 'client/client_import.html'
    return _render_response(request, context_info, template_path)


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
        except Exception as e:
            error = "Error trying to access the import excel file."
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
    my_file = File(f)
    response = HttpResponse(my_file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
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
    my_file = services.get_file_by_id_for_user(file_id, request.user)
    error_code = MESSAGE_REQUEST_FAILED_CODE
    if request.method == 'POST' and request.POST and file_id:
        if request.POST["user_id"]:
            user_id = request.POST["user_id"]
            user = get_cache_user(user_id)
            if my_file and user:
                my_file.participants.remove(user)
                my_file.save()
                return redirect('file_edit', file_id=file_id)
    request.session['error_code'] = error_code
    return redirect('file_edit', file_id=file_id)


@permission_required('sundog.change_file_participant')
def file_add_participant(request, file_id):
    my_file = services.get_file_by_id_for_user(file_id, request.user)
    error_code = MESSAGE_REQUEST_FAILED_CODE
    if my_file and request.method == 'POST' and request.POST:
        if request.POST.getlist('new_participants'):
            new_participants = request.POST.getlist('new_participants')
            users = list(services.get_users_by_ids(new_participants))
            my_file.participants.add(*users)
            my_file.save()
            return redirect('file_edit', file_id=file_id)
    request.session['error_code'] = error_code
    return redirect('file_edit', file_id=file_id)


@permission_required('sundog.change_file')
def documents_delete(request, document_id):
    if request.method == 'POST' and document_id:
        db_doc = Document.objects.get(pk=document_id)
        if os.path.isfile(db_doc.document.path):
            os.remove(db_doc.document.path)
        db_doc.delete()
        return JsonResponse({'result': 'OK'})
    raise Http404()


@bypass_impersonation_login_required
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
            user = get_cache_user(message.user.id)
            user_full_name = user.get_full_name() if user.get_full_name() != '' else user.username
            return JsonResponse({
                'message': {
                    'time': utils.format_date(message_time),
                    'user_full_name': user_full_name
                },
                'count': my_file.messages.count()
            })
    raise Http404()


class FileSearchView(SearchView):
    form_class = FileSearchForm
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        request.GET = request.GET.copy()
        created_end = request.GET.get('created_end')
        created_start = request.GET.get('created_start')
        if created_start == '01/01/1970':
            request.GET['created_start'] = ''
        if (created_end and created_start == '') or (created_end == '' and created_start):
            if created_end and created_start == '':
                request.GET['created_start'] = '01/01/1970'
            if created_end == '' and created_start:
                request.GET['created_end'] = datetime.now().strftime("%m/%d/%Y")
        return super(FileSearchView, self).get(request, *args, **kwargs)

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
