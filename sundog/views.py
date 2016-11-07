from _decimal import ROUND_UP
from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required
from django.core import mail
from django.core.paginator import Paginator
from django.db import transaction

from django.http import Http404
from django.http.response import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, render_to_response, redirect
from django.urls import reverse

from django_auth_app.utils import serialize_user
from numpy import arange
from sundog import services
from sundog.cache.user.info import get_cache_user
from sundog.constants import SHORT_DATE_FORMAT, FIXED_VALUES
from sundog.decorators import bypass_impersonation_login_required

from sundog.forms import ContactForm, ImpersonateUserForm, StageForm, StatusForm, \
    CampaignForm, SourceForm, ContactStatusForm, BankAccountForm, NoteForm, CallForm, EmailForm, UploadedForm, \
    ExpensesForm, IncomesForm, CreditorForm, DebtForm, DebtNoteForm, EnrollmentPlanForm, FeePlanForm, FeeProfileForm, \
    FeeProfileRuleForm, WorkflowSettingsForm, EnrollmentForm, FeeForm, PaymentForm, CompensationTemplateForm, \
    CompensationTemplatePayeeForm
from datetime import datetime, timedelta
from sundog.models import Contact, Stage, STAGE_TYPE_CHOICES, Status, \
    Campaign, Activity, Uploaded, Expenses, Incomes, Creditor, Debt, DebtNote, Enrollment, EnrollmentPlan, \
    FeeProfile, FeeProfileRule, WorkflowSettings, DEBT_SETTLEMENT, Payment, Company, CompensationTemplate, \
    NONE_CHOICE_LABEL

from sundog.services import reorder_stages, reorder_status
from sundog.templatetags.my_filters import currency, percent
from sundog.utils import (
    add_months,
    get_data,
    get_debts_ids,
    get_fees_values,
    get_form_errors,
    get_next_work_date,
    get_now,
    get_or_404,
    get_payments_data,
    to_int,
    get_forms)

import copy
import logging
import settings
import sys


logger = logging.getLogger(__name__)


def _render_response(request, context_info, template_path):
    return render(request, template_path, context_info)


def index(request):
    context_info = {'request': request, 'user': request.user}
    if settings.INDEX_PAGE.endswith(".html"):
        return _render_response(request, context_info, settings.INDEX_PAGE)
    else:
        return HttpResponseRedirect(settings.INDEX_PAGE)


@login_required
def contact_dashboard(request, contact_id):
    contact = (
        Contact
        .objects
        .prefetch_related('contact_debts')
        .get(
            contact_id=contact_id,
        )
    )
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
    except Incomes.DoesNotExist:
        incomes = None
    try:
        expenses = Expenses.objects.get(contact__contact_id=contact_id)
    except Expenses.DoesNotExist:
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
        except Incomes.DoesNotExist:
            incomes = None
        form_incomes = IncomesForm(contact, request.POST, instance=incomes)
        try:
            expenses = Expenses.objects.get(contact__contact_id=contact_id)
        except Expenses.DoesNotExist:
            expenses = None
        form_expenses = ExpensesForm(contact, request.POST, instance=expenses)
        form_errors = []
        if not form_incomes.is_valid():
            form_errors += get_form_errors(form_incomes)
        if not form_expenses.is_valid():
            form_errors += get_form_errors(form_expenses)
        if not form_errors:
            form_incomes.save()
            form_expenses.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': form_errors}
        return JsonResponse(response)


@login_required
def delete_budget_analysis(request, contact_id):
    if request.method == 'DELETE':
        try:
            expenses = Expenses.objects.get(contact__contact_id=contact_id)
            expenses.delete()
        except Expenses.DoesNotExist:
            pass
        try:
            incomes = Incomes.objects.get(contact__contact_id=contact_id)
            incomes.delete()
        except Incomes.DoesNotExist:
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
            response = {'errors': get_form_errors(form)}
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
            except Exception:
                form_errors.append('There was a error sending the email')
            if form_errors:
                response = {'errors': form_errors}
            else:
                response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def upload_file(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = UploadedForm(contact, request.user, request.POST, request.FILES)
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def add_call(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = CallForm(contact, request.user, request.POST)
        if form.is_valid():
            contact_status = form.cleaned_data.pop('contact_status')
            form.save()
            if contact_status and contact.status.status_id != contact_status.status_id:
                status_form = ContactStatusForm({'contact_id': contact_id, 'status': contact_status.status_id, 'stage': contact_status.stage.stage_id}, instance=contact)
                status_form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def uploaded_file_view(request, contact_id, uploaded_id):
    return redirect(
        get_or_404(
            Uploaded,
            uploaded_id=uploaded_id
        )
    )


@login_required
def uploaded_file_delete(request, contact_id, uploaded_id):
    if request.method == 'DELETE':
        doc = Uploaded.objects.get(uploaded_id=uploaded_id)
        doc.content.delete()
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
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
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
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
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
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
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
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def update_stage_order(request):
    if not request.is_ajax():
        redirect('home')  # TODO: handle this a generic way perhaps
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
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def edit_campaign(request):
    if request.method == 'POST' and request.POST:
        campaign_id = request.POST['campaign_id']
        instance = Campaign.objects.get(campaign_id=campaign_id)
        form = CampaignForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def add_source(request):
    if request.method == 'POST' and request.POST:
        form = SourceForm(request.POST)
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def add_contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and request.POST and form.is_valid():
        form.save()
        return redirect('list_contacts')
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': get_form_errors(form) or None,
        'templates':  [('Add a Client', 'add_a_client')],
        'label': 'Add',
        'menu_page': 'contacts',
    }
    template_path = 'contact/contact.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_contact(request, contact_id):
    instance = Contact.objects.get(contact_id=contact_id)
    form = ContactForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST and form.is_valid():
        form.save()
        return redirect('list_contacts')
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'contact_id': contact_id,
        'form_errors': get_form_errors(form) or None,
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
        except Contact.DoesNotExist:
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
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def edit_contact_status(request, contact_id):
    instance = Contact.objects.get(contact_id=contact_id)
    form = ContactStatusForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST and form.is_valid():
        form.save()
        return redirect('list_contacts')
    context_info = {
        'request': request,
        'user': request.user,
        'contact': instance,
        'form': form,
        'form_errors': get_form_errors(form) or None,
        'menu_page': 'contacts'
    }
    template_path = 'contact/edit_contact_status.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_lead_source(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and request.POST and form.is_valid():
        lead_source = form.save() # TODO: redirect to lead sources list? # noqa
        return redirect('home')
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': get_form_errors(form) or None,
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
    form = CreditorForm(request.POST or None)
    if request.method == 'POST' and request.POST and form.is_valid():
        form.save()
        return redirect('creditors_list')
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': get_form_errors(form) or None,
        'menu_page': 'creditors',
    }
    template_path = 'creditor/add_creditor.html'
    return _render_response(request, context_info, template_path)


@login_required
def contact_debts(request, contact_id):
    contact = (
        Contact
        .objects
        .prefetch_related('contact_debts')
        .get(contact_id=contact_id)
    )
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
            response = {'errors': get_form_errors(form)}
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
            response = {'errors': get_form_errors(form)}
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


@login_required
def debt_add_note(request):
    if request.method == 'POST' and request.POST:
        form = DebtNoteForm(request.POST)
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def add_enrollment_plan(request):
    form_errors = None
    form_fee_1 = FeePlanForm(prefix='1')
    form_fee_2 = FeePlanForm(prefix='2')
    form = EnrollmentPlanForm(request.POST)
    enrollment_plans = EnrollmentPlan.objects.all()
    if request.method == 'POST' and request.POST:
        form_fee_1 = FeePlanForm(get_data('1', request.POST), prefix='1')
        fee_data_2 = get_data('2', request.POST)
        if fee_data_2:
            form_fee_2 = FeePlanForm(request.POST, prefix='2')
        if (
            form.is_valid() and
            form_fee_1.is_valid() and (
                not fee_data_2 or (
                    fee_data_2 and
                    form_fee_2.is_valid()
                )
            )
        ):
            enrollment_plan = form.save()
            fee_1 = form_fee_1.save(commit=False)
            fee_1.enrollment_plan = enrollment_plan
            fee_1.save()
            if fee_data_2:
                fee_2 = form_fee_2.save(commit=False)
                fee_2.enrollment_plan = enrollment_plan
                fee_2.save()
            return redirect(
                'edit_enrollment_plan',
                enrollment_plan_id=enrollment_plan.enrollment_plan_id,
            )
        else:
            form_errors = get_form_errors(form) + get_form_errors(form_fee_1)
            if fee_data_2:
                form_errors += get_form_errors(form_fee_2)
    plans = [('', '--New Plan--')] + [
        (plan.enrollment_plan_id, plan.name) for plan in enrollment_plans
    ]
    has_second_fee = (
        form_errors and
        next(
            (x for x in form_errors if '2-' in x),
            False,
        )
    )
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_fee_1': form_fee_1,
        'form_fee_2': form_fee_2,
        'form_errors': form_errors,
        'has_second_fee': has_second_fee,
        'plans': plans,
        'fixed_values': FIXED_VALUES,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/add_enrollment_plan.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_enrollment_plan(request, enrollment_plan_id):
    form_errors = None
    instance = (
        EnrollmentPlan
        .objects
        .get(
            enrollment_plan_id=int(enrollment_plan_id),
        )
    )
    form = EnrollmentPlanForm(request.POST or None, instance=instance)
    fees = list(instance.fee_plans.all())
    fee_count = len(fees)
    fee_instance = fees[0] if fees else None
    form_fee_1 = FeePlanForm(prefix='1', instance=fee_instance)
    enrollment_plans = EnrollmentPlan.objects.all()
    if request.method == 'POST' and request.POST:
        form_fee_1 = FeePlanForm(
            get_data('1', request.POST),
            prefix='1',
            instance=fee_instance
        )
        fee_data_2 = get_data('2', request.POST)
        if fee_count > 1 and fee_data_2:
            form_fee_2 = FeePlanForm(request.POST, instance=fees[1], prefix='2')
        else:
            form_fee_2 = FeePlanForm(request.POST, prefix='2')
        if (
            form.is_valid() and
            form_fee_1.is_valid() and (
                not fee_data_2 or (
                    fee_data_2 and
                    form_fee_2.is_valid()
                )
            )
        ):
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
    plans = [
        ('', '--New Plan--'),
    ] + [
        (plan.enrollment_plan_id, plan.name)
        for plan in enrollment_plans
    ]
    form_fee_2 = FeePlanForm(prefix='2')
    if len(fees) > 1:
        form_fee_2 = FeePlanForm(prefix='2', instance=fees[1])
    has_second_fee = (
        form_errors and
        next(
            (x for x in form_errors if '2-' in x),
            False,
        )
    ) or (len(fees) > 1)
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
        'fixed_values': FIXED_VALUES,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/edit_enrollment_plan.html'
    return _render_response(request, context_info, template_path)


@login_required
def delete_enrollment_plan(request, enrollment_plan_id):
    if request.method == 'DELETE':
        try:
            (
                EnrollmentPlan
                .objects
                .get(enrollment_plan_id=enrollment_plan_id)
                .delete()
            )
        except EnrollmentPlan.DoesNotExist:
            pass
        except Exception:
            return JsonResponse({'result': 'error'})
        return JsonResponse({'result': 'Ok'})


@login_required
def add_fee_profile(request):
    form_errors = None
    forms_range = range(1, 11)
    profile_rules_forms = [
        FeeProfileRuleForm(
            get_data(
                str(i),
                request.POST
            ),
            prefix=str(i),
        )
        for i in forms_range
    ]
    form = FeeProfileForm(request.POST or None)
    fee_profiles = FeeProfile.objects.all()
    if request.method == 'POST' and request.POST:
        received_profile_rules_forms = []
        for i in forms_range:
            prefix = str(i)
            data = get_data(prefix, request.POST)
            if data:
                received_profile_rules_forms.append(
                    FeeProfileRuleForm(
                        data,
                        prefix=prefix,
                    )
                )
        if (
            form.is_valid() and
            all([
                form.is_valid()
                for form in received_profile_rules_forms
            ])
        ):
            fee_profile = form.save()
            for form_rule in received_profile_rules_forms:
                rule = form_rule.save(commit=False)
                rule.fee_profile = fee_profile
                rule.save()
            return redirect(
                'edit_fee_profile',
                fee_profile_id=fee_profile.fee_profile_id,
            )
        else:
            list_of_error_lists = list(
                (
                    get_form_errors(form)
                    for form in received_profile_rules_forms
                )
            )
            form_errors = get_form_errors(form) + list(
                error
                for sub_list in list_of_error_lists
                for error in sub_list
            )
    profiles = (
        [('', '--Add Profile--')] +
        [
            (profile.fee_profile_id, profile.name)
            for profile in fee_profiles
        ]
    )
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


@login_required
def edit_fee_profile(request, fee_profile_id):
    form_errors = None
    instance = (
        FeeProfile
        .objects
        .prefetch_related('rules')
        .get(fee_profile_id=fee_profile_id)
    )
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
            profile_rules_forms.append(
                FeeProfileRuleForm(
                    data,
                    instance=rule,
                    prefix=prefix,
                )
            )
        elif request.POST and not data:
            remove_rules.append(rule.fee_profile_rule_id)
    if request.method == 'POST' and request.POST:
        received_profile_rules_forms = []
        for i in range(number_of_previous_rule_count + 1, 11):
            prefix = str(i)
            data = get_data(prefix, request.POST)
            if data:
                received_profile_rules_forms.append(
                    FeeProfileRuleForm(
                        data,
                        prefix=prefix,
                    )
                )
        received_profile_rules_forms.extend(profile_rules_forms)
        if (
            form.is_valid() and
            all([
                form.is_valid()
                for form in received_profile_rules_forms
            ])
        ):
            fee_profile = form.save()
            for form_rule in received_profile_rules_forms:
                rule = form_rule.save(commit=False)
                rule.fee_profile = fee_profile
                rule.save()
            if remove_rules:
                FeeProfileRule.objects.filter(
                    fee_profile_rule_id__in=remove_rules,
                ).delete()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            list_of_error_lists = list(
                (
                    get_form_errors(form)
                    for form in received_profile_rules_forms
                )
            )
            form_errors = (
                get_form_errors(form) +
                list(
                    error
                    for sub_list in list_of_error_lists
                    for error in sub_list
                )
            )
            response = {'errors': form_errors}
        return JsonResponse(response)
    profile_rules_forms += [
        FeeProfileRuleForm(
            get_data(
                str(i),
                request.POST,
            ),
            prefix=str(i),
        )
        for i in range(number_of_previous_rule_count + 1, 11)
    ]
    profiles = (
        [('', '--Add Profile--')] +
        [
            (profile.fee_profile_id, profile.name)
            for profile in fee_profiles
        ]
    )
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


@login_required
def delete_fee_profile(request, fee_profile_id):
    if request.method == 'DELETE':
        try:
            FeeProfile.objects.get(
                fee_profile_id=fee_profile_id,
            ).delete()
        except FeeProfile.DoesNotExist:
            pass
        except Exception:
            return JsonResponse({'result': 'error'})
        return JsonResponse({'result': 'Ok'})


@login_required
def enrollments_list(request):
    order_by_list = [
        'full_name',
        'state',
        'next_payment',
        'payments_made',
        'balance',
        'created_at',
    ]
    page = int(request.GET.get('page', '1'))
    order_by = request.GET.get('order_by', 'full_name')

    if order_by in order_by_list:
        i = order_by_list.index(order_by)
        order_by_list[i] = '-' + order_by

    sort = {
        'name': order_by.replace('-', ''),
        'class': (
            'sorting_desc'
            if order_by.find('-')
            else 'sorting_asc'
        ),
    }

    query = (
        Enrollment
        .objects
        .prefetch_related('contact')
        .prefetch_related('payments')
    )

    if order_by.replace('-', '') == 'created_at':
        order_by = [order_by]
        enrollments = list(query.order_by(*order_by))
    else:
        enrollments = list(query)
        if order_by == 'full_name':
            enrollments.sort(key=lambda d: d.contact.full_name_straight)
        elif order_by == '-full_name':
            enrollments.sort(key=lambda d: -d.contact.full_name_straight)
        elif order_by == 'next_payment':
            enrollments.sort(
                key=lambda d: (
                    d.next_payment().total_seconds()
                    if d.next_payment()
                    else 0
                )
            )
        elif order_by == '-next_payment':
            enrollments.sort(
                key=lambda d: (
                    -d.next_payment().total_seconds()
                    if d.next_payment()
                    else sys.maxsize
                )
            )
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


@login_required
def workflow_settings(request):
    workflow_type = request.GET.get('type', DEBT_SETTLEMENT)
    try:
        instance = WorkflowSettings.objects.get(type=workflow_type)
    except WorkflowSettings.DoesNotExist:
        instance = None
    form = WorkflowSettingsForm(instance=instance)
    context_info = {
        'request': request,
        'user': request.user,
        'selected_type': workflow_type,
        'types': STAGE_TYPE_CHOICES,
        'form': form,
        'menu_page': 'enrollments',
    }
    template_path = 'enrollment/workflow_settings.html'
    return _render_response(request, context_info, template_path)


@login_required
def workflow_settings_save(request):
    if request.method == 'POST' and request.POST:
        workflow_type = request.POST.get('type', DEBT_SETTLEMENT)
        try:
            instance = WorkflowSettings.objects.get(type=workflow_type)
        except WorkflowSettings.DoesNotExist:
            instance = None
        form = WorkflowSettingsForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def add_contact_enrollment(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').prefetch_related('incomes').prefetch_related('expenses').get(contact_id=contact_id)
    try:
        enrollment = Enrollment.objects.get(contact=contact)
    except Enrollment.DoesNotExist:
        enrollment = None
    if enrollment:
        return redirect('contact_enrollment_details', contact_id=contact_id)
    form_errors = []
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        if 'first_date' not in post_data:
            post_data['first_date'] = (get_now() + timedelta(days=1)).strftime(SHORT_DATE_FORMAT)
        form = EnrollmentForm(contact, post_data)
        form_fee_1 = FeeForm(get_data('1', post_data), prefix='1')
        form_fee_2 = None
        form_2_data = get_data('2', post_data)
        if form_2_data:
            form_fee_2 = FeeForm(form_2_data, prefix='2')
        if form.is_valid() and form_fee_1.is_valid() and (not form_fee_2 or (form_fee_2 and form_fee_2.is_valid())):
            with transaction.atomic():
                enrollment = form.save()
                fee_1 = form_fee_1.save(commit=False)
                fee_1.enrollment = enrollment
                fee_1.save()
                if form_fee_2:
                    fee_2 = form_fee_2.save(commit=False)
                    fee_2.enrollment = enrollment
                    fee_2.save()
                payments_data = get_payments_data(post_data)
                for payment_data in payments_data:
                    date = payment_data.pop('date')
                    amount = payment_data.pop('amount')
                    for key, value in payment_data.items():
                        amount -= value
                        payment = Payment(date=date, amount=amount, status='open', type='ACH Client Debit',
                                          enrollment=enrollment, charge_type='payment')
                    payment.save()
                    for key, value in payment_data.items():
                        fee = Payment(date=date, amount=value, type=key, status='open', enrollment=enrollment,
                                      charge_type='fee', related_payment=payment)
                        fee.save()
            response_data = 'Ok'
            response = {'result': response_data,
                        'redirect_url': reverse('contact_enrollment_details', kwargs={'contact_id': contact_id})}
        else:
            form_errors = get_form_errors(form) + get_form_errors(form_fee_1)
            if form_fee_2:
                form_errors += get_form_errors(form_fee_2)
            response = {'errors': form_errors}
        return JsonResponse(response)
    debts = list(contact.contact_debts.all())
    form = EnrollmentForm(contact)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'debts': debts,
        'form': form,
        'fixed_values': FIXED_VALUES,
        'form_errors': form_errors,
        'menu_page': 'contacts',
    }
    template_path = 'contact/add_contact_enrollment.html'
    return _render_response(request, context_info, template_path)


@login_required
def contact_enrollment_details(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').prefetch_related('incomes').prefetch_related('expenses').get(contact_id=contact_id)
    try:
        enrollment = Enrollment.objects.prefetch_related('payments').get(contact=contact)
    except Enrollment.DoesNotExist:
        enrollment = None
    if not enrollment:
        return redirect('add_contact_enrollment', contact_id=contact_id)
    form_add_payment = PaymentForm()
    form_edit_payment = PaymentForm()
    payments = list(enrollment.payments.all())
    context_info = {
        'request': request,
        'user': request.user,
        'form_add_payment': form_add_payment,
        'form_edit_payment': form_edit_payment,
        'contact': contact,
        'enrollment': enrollment,
        'payments': payments,
        'menu_page': 'contacts',
    }
    template_path = 'contact/enrollment_details.html'
    return _render_response(request, context_info, template_path)


@login_required
def get_enrollment_plan_info(request, contact_id, enrollment_plan_id):
    if not request.is_ajax():
        return redirect('home')
    response = {'result': None}
    if request.method == 'GET' and request.GET:
        contact = Contact.objects.prefetch_related('contact_debts').get(contact_id=contact_id)
        now = get_now()
        first_date_str = request.GET.get('first_date')
        first_date = datetime.strptime((first_date_str if first_date_str else (now + timedelta(days=1)).strftime(SHORT_DATE_FORMAT)), SHORT_DATE_FORMAT)
        start_date_str = request.GET.get('start_date')
        start_date = datetime.strptime((start_date_str if start_date_str else (first_date + timedelta(days=32)).strftime(SHORT_DATE_FORMAT)), SHORT_DATE_FORMAT)
        second_date_str = request.GET.get('second_date')
        second_date = datetime.strptime(second_date_str, SHORT_DATE_FORMAT) if second_date_str else None
        debt_ids = get_debts_ids(request.GET)
        fee_values = get_fees_values(request.GET)
        total_debt = contact.total_enrolled_current_debts(ids=debt_ids)
        payments = []
        plan = EnrollmentPlan.objects.prefetch_related('fee_profile').prefetch_related('fee_profile__rules').get(enrollment_plan_id=enrollment_plan_id)
        default_months = None
        if to_int(plan.program_length_default) != -1:
            default_months = int(plan.program_length_default)
        months = to_int(request.GET.get('months'), default=default_months)
        if plan.two_monthly_drafts and not second_date:
            second_date = start_date + timedelta(days=15)
        elif not plan.two_monthly_drafts:
            second_date = None
        difference_between_dates = None
        if second_date:
            difference_between_dates = second_date - start_date
        fee_profile = plan.fee_profile if plan.fee_profile else None
        rules = list(fee_profile.rules.all()) if fee_profile else []
        rule_for_fee = None
        for rule in rules:
            if rule.debt_high >= total_debt >= rule.debt_low:
                rule_for_fee = rule
                break
        number_of_payments = months if not second_date else months * 2
        monthly_debt = total_debt / number_of_payments
        est_settlement = contact.est_sett(ids=debt_ids)
        fees = {}
        min_length = to_int(plan.program_length_minimum)
        max_length = to_int(plan.program_length_maximum)
        program_lengths = [(str(x), ('{} Months' if x > 1 else '{} Month').format(x)) for x in range(min_length, max_length + 1, plan.program_length_increment)]
        fees_amounts = Decimal('0.00')
        total_fees_amounts = Decimal('0.00')
        fee_plans = plan.fee_plans.all()
        fee_index = 0
        for fee_plan in fee_plans:
            if fee_plan.type in FIXED_VALUES:
                amount = Decimal(fee_plan.amount) * number_of_payments
                options = [(str(amount / number_of_payments), currency(amount / number_of_payments))]
            else:
                if fee_values and len(fee_values) > fee_index:
                    base_amount = fee_values[fee_index]
                    fee_index += 1
                else:
                    base_amount = fee_plan.amount
                perc = Decimal(base_amount)
                amount = total_debt * (perc / 100)
                if rule_for_fee:
                    options = [(str(op), percent(op)) for op in arange(rule_for_fee.sett_fee_low, rule_for_fee.sett_fee_high + 1, rule_for_fee.sett_fee_inc)]
                else:
                    if perc:
                        options = [(str(perc), percent(perc))]
                    else:
                        options = [(str(amount / number_of_payments), currency(amount / number_of_payments))]
            total_fees_amounts += amount
            if fee_plan.defer == 'yes':
                fees_amounts += amount
            fees[fee_plan.name] = {
                'name': fee_plan.name,
                'amount': amount,
                'fee_plan_id': fee_plan.fee_plan_id,
                'type': fee_plan.type,
                'defer': fee_plan.defer,
                'options': options,
                'monthly_payment': amount / number_of_payments
            }
        total_payment = est_settlement + total_fees_amounts
        monthly_amount_paid = (total_payment / number_of_payments).quantize(Decimal('.01'), rounding=ROUND_UP)

        monthly_amount_acct_balance = (est_settlement + fees_amounts) / number_of_payments
        savings = total_debt - total_payment
        date = get_next_work_date(first_date)
        std_timedelta = add_months(start_date, 1) - start_date
        monthly_savings = monthly_debt - monthly_amount_paid
        accumulated_paid_amount = Decimal('0.00')
        payment_monthly_savings_total = Decimal('0.00')
        payment_monthly_amount_paid_total = Decimal('0.00')
        payment_fees_total = {fee['name']: Decimal('0.00') for fee in fees.values()}
        for payment_index in range(0, number_of_payments):
            accumulated_paid_amount += monthly_amount_acct_balance
            payment_monthly_savings_total += monthly_savings
            payment_monthly_amount_paid_total += monthly_amount_paid
            if payment_index == number_of_payments - 1:
                monthly_savings += savings - payment_monthly_savings_total
                monthly_amount_paid += total_payment - payment_monthly_amount_paid_total
            payment = {
                'order': payment_index + 1,
                'date': get_next_work_date(date).strftime(SHORT_DATE_FORMAT),
                'savings': currency(monthly_savings),
                'payment': currency(monthly_amount_paid),
                'acct_balance': currency(accumulated_paid_amount),
            }
            for fee_plan in fee_plans:
                payment[fee_plan.name] = fees[fee_plan.name]['monthly_payment']
                payment_fees_total[fee_plan.name] += fees[fee_plan.name]['monthly_payment']
                if payment_index == number_of_payments - 1:
                    payment[fee_plan.name] += fees[fee_plan.name]['amount'] - payment_fees_total[fee_plan.name]
                payment[fee_plan.name] = currency(payment[fee_plan.name])
            payments.append(payment)
            if date != first_date:
                if difference_between_dates:
                    if payment_index % 2 == 1:
                        delta = difference_between_dates
                    else:
                        delta = std_timedelta - difference_between_dates
                        std_timedelta = add_months(date, 1) - date
                else:
                    std_timedelta = add_months(date, 1) - date
                    delta = std_timedelta
                date += delta
            else:
                date = start_date
        for _, fee_data in fees.items():
            fee_data['amount'] = currency(fee_data['amount'])
            fee_data['monthly_payment'] = currency(fee_data['monthly_payment'])
        data = {
            'total_savings': currency(savings),
            'total_fees': currency(total_fees_amounts),
            'total_sett': currency(est_settlement),
            'total_debt': currency(total_debt),
            'total_payment': currency(total_payment),
            'program_lengths': program_lengths,
            'length_selected': months,
            'select_first_date': plan.select_first_payment,
            'first_date': first_date.strftime(SHORT_DATE_FORMAT),
            'start_date': start_date.strftime(SHORT_DATE_FORMAT),
            'fees': list(fees.values()),
            'payments': payments,
        }
        if second_date:
            data['second_date'] = second_date.strftime(SHORT_DATE_FORMAT)
        response['result'] = 'Ok'
        response['data'] = data
    return JsonResponse(response)


@login_required
def get_debts_info(request, contact_id):
    if not request.is_ajax():
        return redirect('home')
    response = {'result': None}
    if request.method == 'GET' and request.GET:
        contact = Contact.objects.prefetch_related('contact_debts').get(contact_id=contact_id)
        debt_ids = get_debts_ids(request.GET)
        total_debt = contact.total_enrolled_current_debts(ids=debt_ids)
        est_settlement = contact.est_sett(ids=debt_ids)
        total_payment = est_settlement
        savings = total_debt - total_payment
        data = {
            'total_savings': currency(savings),
            'total_sett': currency(est_settlement),
            'total_debt': currency(total_debt),
        }
        response['result'] = 'Ok'
        response['data'] = data
    return JsonResponse(response)


@login_required
def add_payment(request, contact_id):
    response = {'result': None}
    if request.method == 'POST' and request.POST:
        try:
            enrollment = Enrollment.objects.get(contact__contact_id=contact_id)
        except Enrollment.DoesNotExist:
            enrollment = None
        if enrollment:
            form = PaymentForm(request.POST)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.enrollment = enrollment
                payment.status = 'open'
                payment.save()
                response['result'] = 'Ok'
            else:
                response['result'] = 'No Enrollment'
    return JsonResponse(response)


@login_required
def edit_payment(request, contact_id):
    response = {'result': None}
    if request.method == 'POST' and request.POST:
        try:
            enrollment = Enrollment.objects.get(contact__contact_id=contact_id)
        except Enrollment.DoesNotExist:
            enrollment = None
        if enrollment:
            payment_id = request.POST.get('payment_id')
            instance = None
            try:
                instance = Payment.objects.get(payment_id=payment_id)
            except:
                pass
            if instance:
                form = PaymentForm(request.POST)
                if form.is_valid():
                    payment = form.save(commit=False)
                    payment.enrollment = enrollment
                    payment.save()
                    response['result'] = 'Ok'
                    response['data'] = {
                        'payment_id': payment.payment_id,
                        'active': payment.active,
                        'date': payment.date,
                        'type': payment.type,
                        'sub_type': payment.sub_type,
                        'memo': payment.memo,
                        'amount': payment.amount,
                    }
                else:
                    response['result'] = 'No Enrollment'
    return JsonResponse(response)


def add_compensation_template(request, company_id):
    compensation_templates = CompensationTemplate.objects.filter(company__company_id=company_id)
    form = CompensationTemplateForm(request.POST or None)
    forms = [CompensationTemplatePayeeForm(prefix=1)]
    form_errors = []
    if request.method == 'POST' and request.POST:
        forms, _ = get_forms(request.POST, CompensationTemplatePayeeForm)
        forms_validation = sum(Decimal(form.data[str(form.prefix) + '-fee_amount']) for form in forms) == Decimal('100.00')
        if form.is_valid() and len(forms) > 0 and all([form.is_valid() for form in forms]) and forms_validation:
            company = Company.objects.get(company_id=company_id)
            with transaction.atomic():
                compensation_template = form.save(commit=False)
                compensation_template.company = company
                compensation_template.save()
                for form_payee in forms:
                    payee = form_payee.save(commit=False)
                    payee.compensation_template = compensation_template
                    payee.save()
            redirect('add_compensation_template', company_id=company_id)
        else:
            list_of_error_lists = list((get_form_errors(form) for form in forms))
            form_errors = get_form_errors(form) + list(error for sub_list in list_of_error_lists for error in sub_list)
            if not forms_validation:
                form_errors.append('The fee amounts of all payees must add 100 percent.')
    compensation_templates_choices = [('', '--Add new compensation template--')] + \
                                     [(str(template.compensation_template_id), template.name)
                                      for template in compensation_templates]
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'forms': forms,
        'company_id': company_id,
        'form_errors': form_errors,
        'compensation_templates_choices': compensation_templates_choices,
        'menu_page': 'companies',
    }
    template_path = 'company/add_compensation_template.html'
    return _render_response(request, context_info, template_path)


def edit_compensation_template(request, company_id, compensation_template_id):
    compensation_templates = CompensationTemplate.objects.filter(company__company_id=company_id)
    instance = CompensationTemplate.objects.get(compensation_template_id=compensation_template_id)
    form = CompensationTemplateForm(request.POST or None, instance=instance)
    instances = list(instance.payees.all())
    if request.method == 'POST' and request.POST:
        forms, instances = get_forms(request.POST, CompensationTemplatePayeeForm, instances=instances)
        forms_validation = sum(Decimal(form.data[str(form.prefix) + '-fee_amount']) for form in forms) == Decimal('100.00')
        if form.is_valid() and len(forms) > 0 and all([form.is_valid() for form in forms]) and forms_validation:
            company = Company.objects.get(company_id=company_id)
            with transaction.atomic():
                try:
                    compensation_template = form.save(commit=False)
                    compensation_template.company = company
                    compensation_template.save()
                    for form_payee in forms:
                        payee = form_payee.save(commit=False)
                        payee.compensation_template = compensation_template
                        payee.save()
                    for instance_to_delete in instances:
                        instance_to_delete.delete()
                    response = {'result': 'Ok'}
                except:
                    response = {'errors': 'Error saving the data please try again later.'}
        else:
            list_of_error_lists = list((get_form_errors(form) for form in forms))
            form_errors = get_form_errors(form) + list(error for sub_list in list_of_error_lists for error in sub_list)
            if not forms_validation:
                form_errors.append('The fee amounts of all payees must add 100 percent.')
            response = {'errors': form_errors}
        return JsonResponse(response)
    else:
        forms = [CompensationTemplatePayeeForm(instance=payee, prefix=ind + 1) for ind, payee in enumerate(instances)]

        form_errors = []
    compensation_templates_choices = [('', '--Add new compensation template--')] + \
                                     [(str(template.compensation_template_id), template.name)
                                      for template in compensation_templates]
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'forms': forms,
        'company_id': company_id,
        'form_errors': form_errors,
        'compensation_templates_choices': compensation_templates_choices,
        'compensation_template_id': str(compensation_template_id),
        'menu_page': 'companies',
    }
    template_path = 'company/edit_compensation_template.html'
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
    return render(request, '404.html', status=404)


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
                request.session["user_impersonated"] = \
                    serialize_user(impersonated_user)
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
                error = get_form_errors(form_client)
        except Exception:
            error = "Error trying to save the new client."
        if error:
            return JsonResponse({'error': error})
        else:
            return JsonResponse({
                'result': {
                    'client_id': new_client.client_id,
                    'name': new_client.first_name,
                }
            })
    raise Http404()
