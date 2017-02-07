from _decimal import ROUND_UP
from decimal import Decimal
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, Group, User
from django.core import mail
from django.core.paginator import Paginator
from django.db import transaction

from django.http import Http404
from django.http.response import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.timezone import now

from numpy import arange
import pytz

from sundog.constants import SHORT_DATE_FORMAT, FIXED_VALUES
from sundog.decorators import bypass_impersonation_login_required

from sundog.forms import ContactForm, StageForm, StatusForm, \
    CampaignForm, SourceForm, ContactStatusForm, BankAccountForm, NoteForm, CallForm, EmailForm, UploadedForm, \
    ExpensesForm, IncomesForm, CreditorForm, DebtForm, DebtNoteForm, EnrollmentPlanForm, FeePlanForm, FeeProfileForm, \
    FeeProfileRuleForm, WorkflowSettingsForm, EnrollmentForm, PaymentForm, CompensationTemplateForm, \
    CompensationTemplatePayeeForm, SettlementOfferForm, SettlementForm, FeeForm, AdjustPaymentForm, GroupForm, TeamForm, \
    CompanyForm, PayeeForm, CreateUserForm, EditUserForm, LoginForm
from datetime import datetime, timedelta
from sundog.management.commands.generate_base_permissions import CONTACT_BASE_CODENAME, CREDITOR_BASE_CODENAME, \
    ENROLLMENT_BASE_CODENAME, SETTLEMENT_BASE_CODENAME, DOCS_BASE_CODENAME, FILES_BASE_CODENAME, \
    E_MARKETING_BASE_CODENAME, ADMIN_BASE_CODENAME
from sundog.models import CAMPAIGN_SOURCES_CHOICES, Contact, Stage, STAGE_TYPE_CHOICES, Status, \
    Campaign, Activity, Uploaded, Expenses, Incomes, Creditor, Debt, DebtNote, Enrollment, EnrollmentPlan, \
    FeeProfile, FeeProfileRule, WorkflowSettings, DEBT_SETTLEMENT, Payment, Company, CompensationTemplate, \
    SettlementOffer, SETTLEMENT_SUB_TYPE_CHOICES, Settlement, Team, Payee

from sundog.services import reorder_stages, reorder_status
from sundog.templatetags.my_filters import currency, percent
from sundog.utils import (
    add_months,
    get_data,
    get_debts_ids,
    get_fees_values,
    get_form_errors,
    get_next_work_date,
    get_or_404,
    get_payments_data,
    to_int,
    get_forms, FOUR_PLACES, roundup_places, get_date_from_str)

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


def login_user(request):
    form = LoginForm(request.POST or None)
    form_errors = None
    user_tz = 'US/Pacific'
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            user = form.login(request)
            if user:
                login(request, user)
                now_date = now()
                now_date.replace(tzinfo=pytz.utc)
                profile = user.userprofile
                profile.last_login = now_date
                profile.save()
                if user_tz:
                    request.session['django_timezone'] = user_tz
                else:
                    try:
                        user_tz = request.POST["timezone"]
                        request.session['django_timezone'] = user_tz
                    except:
                        pass
                return HttpResponseRedirect(reverse('list_contacts'))
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        field_error_text = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(field_error_text)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    template_path = 'auth/login.html'
    return _render_response(request, {'form': form, 'form_errors': form_errors}, template_path)


def logout_user(request):
    logout(request)
    return redirect('login')


@login_required
def contact_dashboard(request, contact_id):
    section = request.GET.get('section', 'activity')
    contact = (
        Contact
        .objects
        .prefetch_related('contact_debts')
        .get(
            contact_id=contact_id,
        )
    )
    form_bank_account = BankAccountForm(
        instance=(
            contact.get_bank_account()
            if hasattr(contact, 'bank_account')
            else None
        ),
    )
    form_bank_account.fields['contact'].initial = contact
    form_note = NoteForm(contact, request.user)
    form_call = CallForm(contact, request.user)
    form_email = EmailForm(contact, request.user)
    form_upload = UploadedForm(contact, request.user)
    form_expenses = ExpensesForm(contact)
    form_incomes = IncomesForm(contact)
    form_debt_note = DebtNoteForm()
    e_signed_docs = list(contact.e_signed_docs.all())
    generated_documents = list(contact.generated_documents.all())
    uploaded_docs = list(contact.uploaded_docs.all())
    enrolled_debts = contact.contact_debts.filter(enrolled=True)
    not_enrolled_debts = contact.contact_debts.filter(enrolled=False)
    activities = Activity.objects.filter(contact__contact_id=contact_id)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'section': section,
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
        'generated_documents': generated_documents,
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
                status_form = ContactStatusForm({'contact_id': contact_id, 'status': contact_status.status_id,
                                                 'stage': contact_status.stage.stage_id}, instance=contact)
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
            form.save_m2m()
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
            form.save_m2m()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def delete_stage(request, stage_id):
    try:
        stage = Stage.objects.get(stage_id=stage_id)
        stage.delete()
    except Stage.DoesNotExist:
        pass
    except Exception:
        return JsonResponse({'result': 'error'})
    return JsonResponse({'result': 'Ok'})


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
            form.save_m2m()
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
            form.save_m2m()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)


@login_required
def delete_status(request, status_id):
    try:
        status_to_delete = Status.objects.get(status_id=status_id)
        status_id = int(status_id)
        statuses = Status.objects.filter(stage=status_to_delete.stage)
        status_deleted = False
        with transaction.atomic():
            for status in statuses:
                if status_deleted:
                    status.order -= 1
                    status.save()
                if status.status_id == status_id:
                    status_to_delete.delete()
                    status_deleted = True
    except Status.DoesNotExist:
        pass
    except Exception:
        return JsonResponse({'result': 'error'})
    return JsonResponse({'result': 'Ok'})


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
        'menu_page': 'contacts',
        'media_types': dict(CAMPAIGN_SOURCES_CHOICES),
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


def _get_users_by_company():
    users_by_company = {}
    for user in list(User.objects.prefetch_related('userprofile').prefetch_related('userprofile__company').all()):
        if user.company and user.company.company_id not in users_by_company:
            users_by_company[user.company.company_id] = []
            users_by_company[user.company.company_id].append({'id': str(user.id), 'name': user.get_full_name()})
    return users_by_company


@login_required
def add_contact(request):
    post_data = request.POST.copy()
    if post_data:
        post_data['created_by'] = request.user.id
    form = ContactForm(post_data or None)
    if request.method == 'POST' and request.POST and form.is_valid():
        form.save()
        return redirect('list_contacts')
    users_by_company = _get_users_by_company()
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'form_errors': get_form_errors(form) or None,
        'templates': [('Add a Client', 'add_a_client')],
        'label': 'Add',
        'users_by_company': users_by_company,
        'menu_page': 'contacts',
    }
    template_path = 'contact/contact.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_contact(request, contact_id):
    instance = Contact.objects.get(contact_id=contact_id)
    post_data = request.POST.copy()
    if post_data:
        post_data['created_by'] = request.user.id
    form = ContactForm(post_data or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    users_by_company = _get_users_by_company()
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'contact_id': contact_id,
        'form_errors': get_form_errors(form) or None,
        'templates': [('Add a Client', 'add_a_client')],
        'label': 'Edit',
        'users_by_company': users_by_company,
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
        statuses = [{'id': status.status_id, 'name': status.name} for status in
                    list(Status.objects.filter(stage__stage_id=stage_id))]
        return JsonResponse({'statuses': statuses})


@login_required
def edit_bank_account(request, contact_id):
    if request.method == 'POST' and request.POST:
        contact = Contact.objects.get(contact_id=contact_id)
        form = BankAccountForm(
            request.POST,
            instance=(
                contact.get_bank_account()
                if hasattr(contact, 'bank_account')
                else None
            ),
        )
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
    post_data = request.POST.copy()
    if post_data:
        post_data['created_by'] = request.user.id
    form = ContactForm(post_data or None)
    if request.method == 'POST' and request.POST and form.is_valid():
        lead_source = form.save()  # TODO: redirect to lead sources list? # noqa
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
def add_debt(request, contact_id):
    contact = Contact.objects.get(contact_id=contact_id)
    form = DebtForm(contact, request.POST or None)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            note_content = form.cleaned_data['note']
            debt = form.save()
            if note_content:
                debt_note = DebtNote(content=note_content, debt=debt)
                debt_note.save()
            return redirect('contact_debts', contact_id=contact_id)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'form_errors': get_form_errors(form),
        'form': form,
        'menu_page': 'contacts'
    }
    template_path = 'contact/add_debts.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_debt(request, contact_id, debt_id):
    contact = Contact.objects.get(contact_id=contact_id)
    instance = Debt.objects.get(debt_id=debt_id)
    form = DebtForm(contact, request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            response_data = 'Ok'
            response = {'result': response_data}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'debt_id': debt_id,
        'form': form,
        'menu_page': 'contacts'
    }
    template_path = 'contact/edit_debt.html'
    return _render_response(request, context_info, template_path)


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
        (str(plan.enrollment_plan_id), plan.name) for plan in enrollment_plans
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
    instance = EnrollmentPlan.objects.get(enrollment_plan_id=int(enrollment_plan_id))
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
    plans = [('', '--New Plan--')] + [(str(plan.enrollment_plan_id), plan.name) for plan in enrollment_plans]
    form_fee_2 = FeePlanForm(prefix='2')
    if len(fees) > 1:
        form_fee_2 = FeePlanForm(prefix='2', instance=fees[1])
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
    profiles = [('', '--Add Profile--')] + [(str(profile.fee_profile_id), profile.name) for profile in fee_profiles]
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
    profiles = [('', '--Add Profile--')] + [(str(profile.fee_profile_id), profile.name) for profile in fee_profiles]
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
    contact = Contact.objects.prefetch_related('contact_debts').prefetch_related('incomes').prefetch_related(
        'expenses').prefetch_related('bank_account').get(contact_id=contact_id)
    bank_account = contact.get_bank_account()
    if not bank_account:
        return redirect('contact_dashboard', contact_id=contact_id)
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
            post_data['first_date'] = (now() + timedelta(days=1)).strftime(SHORT_DATE_FORMAT)
        form = EnrollmentForm(contact, post_data)
        form_fee_1 = FeeForm(get_data('1', post_data), prefix='1')
        form_fee_2 = None
        form_2_data = get_data('2', post_data)
        if form_2_data:
            form_fee_2 = FeeForm(form_2_data, prefix='2')
        if bank_account and bank_account.info_complete() and form.is_valid() and form_fee_1.is_valid() and (
           not form_fee_2 or (form_fee_2 and form_fee_2.is_valid())):
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
                    payment = Payment(date=date, amount=amount, status='open', type='ACH Client Debit',
                                      enrollment=enrollment, charge_type='payment', address=contact.address_1,
                                      account_number=bank_account.account_number,
                                      routing_number=bank_account.routing_number,
                                      account_type=bank_account.account_type,
                                      gateway=enrollment.custodial_account)
                    payment.save()
            response_data = 'Ok'
            response = {'result': response_data,
                        'redirect_url': reverse('contact_enrollment_details', kwargs={'contact_id': contact_id})}
        else:
            form_errors = get_form_errors(form) + get_form_errors(form_fee_1)
            if form_fee_2:
                form_errors += get_form_errors(form_fee_2)
            if not bank_account:
                form_errors.append('Contact must have a bank account.')
            response = {'errors': form_errors}
        return JsonResponse(response)
    debts = list(contact.contact_debts.all())
    form = EnrollmentForm(contact)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'bank_account': bank_account,
        'debts': debts,
        'form': form,
        'fixed_values': FIXED_VALUES,
        'form_errors': form_errors,
        'menu_page': 'contacts',
    }
    template_path = 'contact/add_contact_enrollment.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_contact_enrollment(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').prefetch_related('incomes') \
        .prefetch_related('expenses').prefetch_related('bank_account').get(contact_id=contact_id)
    bank_account = contact.get_bank_account()
    try:
        instance = Enrollment.objects.get(contact=contact)
    except Enrollment.DoesNotExist:
        instance = None
    if not instance:
        return redirect('add_contact_enrollment', contact_id=contact_id)
    form_errors = []
    if request.method == 'POST' and request.POST:
        post_data = request.POST.copy()
        if 'first_date' not in post_data:
            post_data['first_date'] = instance.first_date.strftime(SHORT_DATE_FORMAT)
        form = EnrollmentForm(contact, post_data, instance=instance)
        fee_instances = list(instance.fees.all())
        fee_forms, _ = get_forms(post_data, FeeForm, prefix=1, until=2, instances=None)
        if form.is_valid() and all([form.is_valid() for form in fee_forms]):
            with transaction.atomic():
                enrollment = form.save()
                for fee in fee_instances:
                    fee.delete()
                for fee_form in fee_forms:
                    new_fee = fee_form.save(commit=False)
                    new_fee.enrollment = enrollment
                    new_fee.save()
                if form.changed_data != ['compensation_template']:
                    payments_to_delete = enrollment.payments.filter(status='open')
                    for payment in payments_to_delete:
                        payment.delete()
                    payments_data = get_payments_data(post_data)
                    for payment_data in payments_data:
                        date = payment_data.pop('date')
                        amount = payment_data.pop('amount')
                        payment = Payment(date=date, amount=amount, status='open', type='ACH Client Debit',
                                          enrollment=enrollment, charge_type='payment', address=contact.address_1,
                                          account_number=bank_account.account_number,
                                          routing_number=bank_account.routing_number,
                                          account_type=bank_account.account_type,
                                          gateway=enrollment.custodial_account)
                        payment.save()
            response_data = 'Ok'
            response = {'result': response_data,
                        'redirect_url': reverse('contact_enrollment_details', kwargs={'contact_id': contact_id})}
        else:
            list_of_error_lists = list((get_form_errors(form) for form in fee_forms))
            form_errors = get_form_errors(form) + list(error for sub_list in list_of_error_lists for error in sub_list)
            response = {'errors': form_errors}
        return JsonResponse(response)
    else:
        form = EnrollmentForm(contact, instance=instance)
    debts = list(contact.contact_debts.all())
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'bank_account': bank_account,
        'debts': debts,
        'form': form,
        'fixed_values': FIXED_VALUES,
        'form_errors': form_errors,
        'menu_page': 'contacts',
    }
    template_path = 'contact/edit_contact_enrollment.html'
    return _render_response(request, context_info, template_path)


@login_required
def contact_enrollment_details(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').prefetch_related('incomes').prefetch_related(
        'expenses').get(contact_id=contact_id)
    try:
        enrollment = Enrollment.objects.prefetch_related('payments').get(contact=contact)
    except Enrollment.DoesNotExist:
        enrollment = None
    if not enrollment:
        return redirect('add_contact_enrollment', contact_id=contact_id)
    form_add_payment = PaymentForm(enrollment=enrollment, initial={'enrollment': enrollment})
    form_edit_payment = PaymentForm(enrollment=enrollment, initial={'enrollment': enrollment})
    payments = list(enrollment.payments.prefetch_related('enrollment').all())
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
def contact_schedule_performance_fees(request, contact_id):
    contact = Contact.objects.prefetch_related('contact_debts').prefetch_related('enrollments').prefetch_related(
        'expenses').get(contact_id=contact_id)
    settlement_id = request.GET.get('settlement_id', request.POST.get('settlement_id'))

    if settlement_id:
        settlement = Settlement.objects.prefetch_related('settlement_offer') \
            .prefetch_related('settlement_offer__enrollment').prefetch_related('settlement_offer__debt') \
            .prefetch_related('settlement_offer__enrollment__compensation_template') \
            .prefetch_related('settlement_offer__enrollment__compensation_template__payees') \
            .get(settlement_id=settlement_id)
    else:
        settlement = None
    debt = None
    enrollment = Enrollment.objects.prefetch_related('compensation_template').get(contact__contact_id=contact_id)
    comp_template = enrollment.compensation_template
    if request.method == 'POST' and request.POST:
        payments_data = get_payments_data(request.POST, starting_index=1)
        now_date = now()
        if all((payment_data['date'] > now_date for payment_data in payments_data)):
            with transaction.atomic():
                for payment_data in payments_data:
                    payment = Payment(date=payment_data['date'], amount=payment_data['amount'], status='open',
                                      charge_type='fee', type='Earned Performance Fee', enrollment=enrollment,
                                      settlement=settlement, gateway=enrollment.custodial_account)
                    payment.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': "Dates must be in the future."}
        return JsonResponse(response)
    settlement_offer = None
    fee_percentage = None
    settlement_payments_count = 0
    total_fee_amount = Decimal('0.00')
    start_date = (now() + timedelta(days=1)).strftime(SHORT_DATE_FORMAT)
    payees = []
    if settlement:
        settlement_offer = settlement.settlement_offer
        debt = settlement_offer.debt
        settlement_payments_count = len(list(settlement.settlement_payments.all()))
        fees = list(enrollment.fees.all())
        for fee in fees:
            if fee.type == 'percent':
                fee_percentage = fee.amount
                break
        total_fee_amount = roundup_places(settlement_offer.debt_amount * (fee_percentage / 100))
        payees = list(comp_template.payees.all())
        payee_index = 0
        fee_accumulator = Decimal('0.00')
        total_payments = settlement_payments_count + 3
        payments_number = request.GET.getlist('p_number')
        if payments_number:
            payments_number = [int(x) for x in payments_number]
        else:
            payments_number = [settlement_payments_count - 1 for _ in range(0, len(payees))]
        if not payments_number:
            start_index = len(payees) - len(payments_number)
            for i in range(start_index, len(payments_number)):
                payments_number[i] = settlement_payments_count - 1
        payments_dates = request.GET.getlist('p_dates', [start_date for _ in range(0, len(payees))])
        if len(payments_dates) < len(payees):
            start_index = len(payees) - len(payments_dates)
            for i in range(start_index, len(payments_dates)):
                payments_dates[i] = start_date
        index = 0
        payment_form_index = 1
        for payee in payees:
            payee.total_fee = roundup_places(total_fee_amount * (payee.fee_amount / 100))
            fee_accumulator += payee.total_fee
            if payee_index == len(payees) - 1:
                payee.total_fee += fee_accumulator - total_fee_amount
            payee.options = []
            for payment_index in range(1, total_payments + 1):
                amount = roundup_places(payee.total_fee / payment_index)
                option_str = str(payment_index) + ' Payment' + ('s' if payment_index > 1 else '') + ' - ' \
                                                                                                  + currency(amount)
                payee.options.append((payment_index, option_str))
            payee_index += 1
            payee.payments_forms = []
            payee.total_payments = Decimal('0.00')
            payment_number = int(payments_number[index])
            number_of_fees = payee.options[payment_number][0]
            first_date = get_next_work_date(datetime.strptime(payments_dates[index], SHORT_DATE_FORMAT))
            date = first_date
            for fee_index in range(0, number_of_fees):
                amount = payee.options[payment_number][1].split(' - ')[-1].replace(',', '').replace('$', '')
                form = PaymentForm(initial={'date': date.strftime(SHORT_DATE_FORMAT), 'amount': amount},
                                   prefix=payment_form_index, attr_class='col-xs-12 no-padding-sides')
                date = get_next_work_date(add_months(first_date, fee_index + 1))
                payee.payments_forms.append(form)
                payee.total_payments += Decimal(amount)
                payment_form_index += 1
            index += 1
    settled_debts = Settlement.objects.prefetch_related('settlement_offer').prefetch_related('settlement_offer__debt') \
        .prefetch_related('settlement_offer__debt__original_creditor') \
        .filter(settlement_offer__enrollment__contact__contact_id=contact_id)
    settled_debts_options = [('', '--Select--')] + \
        [(str(settlement.settlement_id), settlement.settlement_offer.debt.debt_text()) for settlement in settled_debts]
    comp_template_fee_count = len(list(comp_template.payees.all())) if comp_template else 0
    if request.is_ajax():
        response_forms = {}
        for payee in payees:
            response_forms[payee.compensation_template_payee_id] = []
            for form in payee.payments_forms:
                response_forms[payee.compensation_template_payee_id].append(
                    {'date': str(form.fields['date'].get_bound_field(form, 'date')),
                     'amount': str(form.fields['amount'].get_bound_field(form, 'amount'))}
                )
        return JsonResponse({'forms': response_forms})
    else:
        context_info = {
            'request': request,
            'user': request.user,
            'contact': contact,
            'settlement_id': str(settlement.settlement_id) if settlement else None,
            'settlement_payments_count': str(settlement_payments_count),
            'fee_percentage': fee_percentage,
            'settlement_offer': settlement_offer,
            'start_date': start_date,
            'debt': debt,
            'payees': payees,
            'total_fee_amount': total_fee_amount,
            'comp_template': comp_template,
            'comp_template_fee_count': comp_template_fee_count,
            'settled_debts_options': settled_debts_options,
            'menu_page': 'contacts',
        }
        template_path = 'contact/schedule_performance_fees.html'
        return _render_response(request, context_info, template_path)


def adjust_payments(request, contact_id):
    contact = Contact.objects.get(contact_id=contact_id)
    if request.method == 'POST' and request.POST:
        found = True
        payment_index = 1
        payments_data = []
        while found:
            prefix = str(payment_index)
            found = False
            payment_data = get_data(prefix, request.POST)
            if payment_data:
                found = True
                data = {}
                active_str = payment_data.get(prefix + '-active')
                if active_str:
                    data['active'] = active_str == 'True'
                date_str = payment_data.get(prefix + '-date')
                if date_str:
                    data['date'] = get_date_from_str(date_str)
                amount_str = payment_data.get(prefix + '-amount')
                if amount_str:
                    data['amount'] = Decimal(amount_str)
                memo = payment_data.get(prefix + '-memo')
                if memo:
                    data['memo'] = memo
                ids_str = payment_data.get(prefix + '-ids')
                if ids_str:
                    data['ids'] = ids_str.split(',')
                else:
                    data['ids'] = []
                canceled_str = payment_data.get(prefix + '-cancel_checkbox')
                canceled = canceled_str.title() == 'True' if canceled_str else None
                if canceled is not None and canceled:
                    data['status'] = 'canceled'
                payments_data.append(data)
                payment_index += 1
        with transaction.atomic():
            for payment_data in payments_data:
                ids = payment_data.pop('ids')
                payment_index = 0
                if ids:
                    payments = Payment.objects.filter(payment_id__in=ids)
                    initial_date = payment_data.get('date')
                    for payment in payments:
                        if 'active' in payment_data and payment_data['active'] is not None:
                            payment.active = payment_data['active']
                        if initial_date:
                            payment.date = get_next_work_date(add_months(initial_date, payment_index))
                        if 'amount' in payment_data and payment_data['amount']:
                            payment.amount = payment_data['amount']
                        if 'memo' in payment_data and payment_data['memo']:
                            payment.memo = payment_data['memo']
                        payment.save()
                        payment_index += 1
        response = {'result': 'Ok'}
        return JsonResponse(response)

    debits = Payment.objects.filter(transaction_type='debit', enrollment__contact=contact)
    fees = Payment.objects.filter(charge_type='fee', enrollment__contact=contact)
    settlements = Payment.objects.filter(charge_type='settlement', enrollment__contact=contact)
    form_debit = AdjustPaymentForm(prefix=1)
    form_settlement = AdjustPaymentForm(prefix=2)
    form_fees = AdjustPaymentForm(prefix=3)
    context_info = {
        'request': request,
        'user': request.user,
        'form_debit': form_debit,
        'form_settlement': form_settlement,
        'form_fees': form_fees,
        'contact': contact,
        'debits': debits,
        'fees': fees,
        'settlements': settlements,
        'menu_page': 'contacts',
    }
    template_path = 'contact/adjust_payments.html'
    return _render_response(request, context_info, template_path)


@login_required
def get_enrollment_plan_info(request, contact_id, enrollment_plan_id):
    if not request.is_ajax():
        return redirect('home')
    response = {'result': None}
    if request.method == 'GET' and request.GET:
        contact = Contact.objects.prefetch_related('contact_debts').get(contact_id=contact_id)
        date_now = now()
        first_date_str = request.GET.get('first_date')
        first_date = datetime.strptime(
            (first_date_str if first_date_str else (date_now + timedelta(days=1)).strftime(SHORT_DATE_FORMAT)),
            SHORT_DATE_FORMAT)
        start_date_str = request.GET.get('start_date')
        start_date = datetime.strptime(
            (start_date_str if start_date_str else (first_date + timedelta(days=32)).strftime(SHORT_DATE_FORMAT)),
            SHORT_DATE_FORMAT)
        second_date_str = request.GET.get('second_date')
        second_date = datetime.strptime(second_date_str, SHORT_DATE_FORMAT) if second_date_str else None
        debt_ids = get_debts_ids(request.GET)
        fee_values = get_fees_values(request.GET)
        total_debt = contact.total_enrolled_current_debts(ids=debt_ids)
        payments = []
        plan = EnrollmentPlan.objects.prefetch_related('fee_profile').prefetch_related('fee_profile__rules').get(
            enrollment_plan_id=enrollment_plan_id)
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
        program_lengths = [(str(x), ('{} Months' if x > 1 else '{} Month').format(x)) for x in
                           range(min_length, max_length + 1, plan.program_length_increment)]
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
                    options = [(str(op), percent(op)) for op in
                               arange(rule_for_fee.sett_fee_low, rule_for_fee.sett_fee_high + 1,
                                      rule_for_fee.sett_fee_inc)]
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
        contact = Contact.objects.get(contact_id=contact_id)
        bank_account = contact.get_bank_account()
        try:
            enrollment = Enrollment.objects.get(contact__contact_id=contact_id)
        except Enrollment.DoesNotExist:
            enrollment = None
        if enrollment:
            form = PaymentForm(request.POST)
            if form.is_valid():
                payment = form.save(commit=False)
                payment.status = 'open'
                payment.enrollment = enrollment
                if not payment.address:
                    payment.address = contact.address_1
                if bank_account:
                    if not payment.account_number:
                        payment.account_number = bank_account.account_number
                    if not payment.routing_number:
                        payment.routing_number = bank_account.routing_number
                    if not payment.account_type:
                        payment.account_type = bank_account.account_type
                payment.added_manually = True
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
                form = PaymentForm(request.POST, instance=instance)
                if form.is_valid():
                    payment = form.save(commit=False)
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
                        'enrollment': payment.enrollment.enrollment_id,
                        'account_number': payment.account_number,
                        'routing_number': payment.routing_number,
                        'account_type': payment.account_type,
                        'associated_settlement_payment': payment.associated_settlement_payment,
                        'associated_payment': payment.associated_payment,
                        'address': payment.address,
                        'paid_to': payment.paid_to.payee_id if payment.paid_to else '',
                        'payee': payment.payee.payee_id if payment.payee else '',
                    }
                else:
                    form_errors = get_form_errors(form)
                    response = {'errors': form_errors, 'result': 'No Enrollment'}
    return JsonResponse(response)


def add_compensation_template(request, company_id):
    compensation_templates = CompensationTemplate.objects.filter(company__company_id=company_id)
    form = CompensationTemplateForm(request.POST or None)
    forms = [CompensationTemplatePayeeForm(prefix=1)]
    form_errors = []
    if request.method == 'POST' and request.POST:
        forms, _ = get_forms(request.POST, CompensationTemplatePayeeForm)
        forms_validation = sum(Decimal(form.data[str(form.prefix) + '-fee_amount']) for form in forms) == Decimal(
            '100.00')
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
    template_path = 'admin/add_compensation_template.html'
    return _render_response(request, context_info, template_path)


def edit_compensation_template(request, company_id, compensation_template_id):
    compensation_templates = CompensationTemplate.objects.filter(company__company_id=company_id)
    instance = CompensationTemplate.objects.get(compensation_template_id=compensation_template_id)
    form = CompensationTemplateForm(request.POST or None, instance=instance)
    instances = list(instance.payees.all())
    if request.method == 'POST' and request.POST:
        forms, instances = get_forms(request.POST, CompensationTemplatePayeeForm, instances=instances)
        forms_validation = sum(Decimal(form.data[str(form.prefix) + '-fee_amount']) for form in forms) == Decimal(
            '100.00')
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
    template_path = 'admin/edit_compensation_template.html'
    return _render_response(request, context_info, template_path)


@login_required
def contact_settlement_offer(request, contact_id):
    contact = Contact.objects.prefetch_related('enrollments').get(contact_id=contact_id)
    try:
        enrollment = Enrollment.objects.get(contact=contact)
    except Enrollment.DoesNotExist:
        enrollment = None
    if not enrollment:
        return redirect('add_contact_enrollment', contact_id=contact_id)
    settlement_offer_id = request.POST.get('settlement_offer_id')
    if settlement_offer_id:
        instance = SettlementOffer.objects.get(settlement_offer_id=settlement_offer_id)
    else:
        instance = None
    form = SettlementOfferForm(request.user, request.POST or None, instance=instance)
    form_errors = []
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            if not settlement_offer_id:
                current_completed_offer = enrollment.settlement_offers.prefetch_related('settlements') \
                    .prefetch_related('settlements__settlement_payments').first()
                if current_completed_offer:
                    settlement = current_completed_offer.settlements.first()
                    payments = settlement.settlement_payments.filter(status='open').all()
                    for payment in payments:
                        payment.delete()
                    settlement.delete()
                    current_completed_offer.delete()
            settlement_offer = form.save(commit=False)
            if not settlement_offer_id:
                settlement_offer.enrollment = enrollment
                settlement_offer.created_by = request.user
            settlement_offer.save()
            request.session['debt_id'] = settlement_offer.debt.debt_id
            response = {'result': 'Ok'}
        else:
            form_errors = get_form_errors(form)
            response = {'errors': form_errors}
        return JsonResponse(response)
    debts = list(contact.contact_debts.prefetch_related('offers').filter(enrolled=True))
    offers = list(enrollment.settlement_offers.filter(status__in=['accepted', 'completed']))
    offer_saved = False
    debt_id = request.session.get('debt_id', 0)
    if debt_id:
        offer_saved = True
        request.session.pop('debt_id')
    if not debt_id:
        debt_id = request.GET.get('debt_id', 0)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'enrollment': enrollment,
        'form_errors': form_errors,
        'offer_saved': offer_saved,
        'debt_id': debt_id,
        'form': form,
        'debts': debts,
        'offers': offers,
        'menu_page': 'contacts',
    }
    template_path = 'contact/contact_settlement_offer.html'
    return _render_response(request, context_info, template_path)


@login_required
def get_debt_offer(request, debt_id):
    if request.is_ajax() and request.method == 'GET':
        debt = Debt.objects.prefetch_related('offers').get(debt_id=debt_id)
        offer = debt.offers.first()
        response = {}
        if offer and offer.status != 'completed':
            response['settlement_offer_id'] = str(offer.settlement_offer_id)
            response['made_by'] = offer.made_by
            response['negotiator'] = str(offer.negotiator.pk)
            response['status'] = offer.status
            response['date'] = offer.date.strftime(SHORT_DATE_FORMAT)
            response['valid_until'] = offer.valid_until.strftime(SHORT_DATE_FORMAT) if offer.valid_until else ''
            response['debt_amount'] = str(offer.debt_amount)
            response['offer_amount'] = str(offer.offer_amount)
            response['notes'] = offer.notes if offer.notes else ''
        return JsonResponse(response)


@login_required
def contact_settlement(request, contact_id, settlement_offer_id):
    contact = Contact.objects.prefetch_related('bank_account').get(contact_id=contact_id)
    bank_account = contact.get_bank_account()
    number_of_payments = int(request.GET.get('payments', '1'))
    start_date_str = request.GET.get('start_date', now().strftime(SHORT_DATE_FORMAT))
    date = get_next_work_date(datetime.strptime(start_date_str, SHORT_DATE_FORMAT))
    contact = Contact.objects.prefetch_related('enrollments').get(contact_id=contact_id)
    settlement_offer = SettlementOffer.objects.prefetch_related('debt').prefetch_related('debt__original_creditor') \
        .prefetch_related('debt__debt_buyer').prefetch_related('enrollment') \
        .prefetch_related('enrollment__compensation_template').prefetch_related('enrollment__fees') \
        .get(settlement_offer_id=settlement_offer_id)
    first_amount = settlement_offer.offer_amount
    next_amount = 0
    if number_of_payments > 1:
        first_amount = roundup_places(settlement_offer.offer_amount / 2)
        second_amount = first_amount + settlement_offer.offer_amount - (first_amount * 2)
        next_amount = roundup_places(second_amount / (number_of_payments - 1))
        excess = second_amount - (next_amount * (number_of_payments - 1))
    payment_forms = []
    for i in range(1, number_of_payments + 1):
        if i == 1:
            amount = first_amount
        else:
            amount = next_amount
            if excess != 0 and i == number_of_payments:
                amount += excess
        payment_forms.append(
            PaymentForm(get_data(str(i), request.POST) or None, prefix=i, enrollment=settlement_offer.enrollment,
                        initial={'date': date, 'amount': amount, 'enrollment': settlement_offer.enrollment,
                                 'gateway': settlement_offer.enrollment.custodial_account},
                        attr_class='col-xs-12 no-padding-sides', sub_type_choices=SETTLEMENT_SUB_TYPE_CHOICES)
        )
        date = get_next_work_date(add_months(date, 1))
    form = SettlementForm(request.POST or None)
    if request.method == 'POST' and request.POST:
        fee_percentage = None
        for fee in list(settlement_offer.enrollment.fees.all()):
            if fee.type == 'percent':
                fee_percentage = fee.amount
                break
        if form.is_valid() and all([form.is_valid() for form in payment_forms]) and fee_percentage:
            compensation_template = settlement_offer.enrollment.compensation_template
            if compensation_template:
                fee_payees = list(compensation_template.payees.all())
            else:
                fee_payees = []
            with transaction.atomic():
                settlement_offer.status = 'completed'
                settlement_offer.save()
                settlement = form.save(commit=False)
                settlement.settlement_offer = settlement_offer
                settlement.save()
                payments = []
                for payment_form in payment_forms:
                    payment = payment_form.save(commit=False)
                    payment.settlement = settlement
                    payment.charge_type = 'settlement'
                    payment.type = 'Settlement Payment'
                    payment.active = True
                    payment.status = 'open'
                    payment.address = contact.address_1
                    payment.enrollment = settlement_offer.enrollment
                    if bank_account:
                        payment.account_number = bank_account.account_number
                        payment.account_type = bank_account.account_type
                        payment.routing_number = bank_account.routing_number
                    payment.save()
                    payments.append(payment)
                total_fee_amount = roundup_places(settlement_offer.debt_amount * (fee_percentage / 100))
                for fee_payee in fee_payees:
                    fee_accumulator = Decimal('0.00')
                    payment_index = 0
                    payment_count = len(payments)
                    fee_payments = []
                    total_payee_fee_amount = roundup_places(total_fee_amount * (fee_payee.fee_amount / 100))
                    for payment in payments:
                        settlement_ratio_of_total_debt = roundup_places(payment.amount / settlement_offer.offer_amount,
                                                                        FOUR_PLACES)
                        amount = roundup_places(total_payee_fee_amount * settlement_ratio_of_total_debt)
                        fee_accumulator += amount
                        if payment_index == payment_count - 1:
                            amount += total_payee_fee_amount - fee_accumulator
                        payee_payment = Payment(date=payment.date, amount=amount, status='open', charge_type='fee',
                                                type='Earned Performance Fee', gateway=payment.gateway,
                                                enrollment=settlement_offer.enrollment)
                        payee_payment.save()
                        fee_payments.append(payee_payment)
                        payment_index += 1

                response = {'result': 'Ok'}
        else:
            list_of_error_lists = list((get_form_errors(form) for form in payment_forms))
            form_errors = get_form_errors(form) + list(error for sub_list in list_of_error_lists for error in sub_list)
            if not fee_percentage:
                form_errors.append('You must have a Percent Fee on the enrollment of this contact.')
            response = {'errors': form_errors}
        return JsonResponse(response)
    context_info = {
        'request': request,
        'user': request.user,
        'contact': contact,
        'form': form,
        'payment_forms': payment_forms,
        'payment_amounts': range(1, 101),
        'settlement_offer': settlement_offer,
        'payments_start_date': start_date_str,
        'payments_count': number_of_payments,
        'menu_page': 'contacts',
    }
    template_path = 'contact/contact_settlement.html'
    return _render_response(request, context_info, template_path)


def _generate_permission_sections(checked_permissions=[]):
    permission_sections = []
    data = [
        ('Contacts', CONTACT_BASE_CODENAME), ('Creditors', CREDITOR_BASE_CODENAME),
        ('Enrollments', ENROLLMENT_BASE_CODENAME), ('Settlements', SETTLEMENT_BASE_CODENAME),
        ('Docs', DOCS_BASE_CODENAME), ('Files', FILES_BASE_CODENAME),
        ('E-Marketing', E_MARKETING_BASE_CODENAME), ('Admin', ADMIN_BASE_CODENAME),
    ]
    for data_element in data:
        permissions = list(Permission.objects.filter(codename__startswith=data_element[1] + '.'))
        permissions.sort(key=lambda x: x.name != 'Access Tab')
        permission_data = {'name': data_element[0], 'permissions': permissions}
        if checked_permissions:
            for permission in permissions:
                if permission.id in checked_permissions:
                    permission.checked = True
        permission_sections.append(permission_data)
    return permission_sections


@login_required
def add_company(request):
    form = CompanyForm(request.POST or None)
    errors = []
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            company = form.save()
            return redirect('edit_company', company_id=company.company_id)
        else:
            errors = get_form_errors(form)
    context_info = {
        'request': request,
        'user': request.user,
        'errors': errors,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/add_company.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_company(request, company_id):
    instance = Company.objects.prefetch_related('users').prefetch_related('users__userprofile') \
        .prefetch_related('users__groups').prefetch_related('children').get(company_id=company_id)
    form = CompanyForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)

    context_info = {
        'request': request,
        'user': request.user,
        'company': instance,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/edit_company.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_user_role(request):
    form = GroupForm(request.POST or None)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            assignable = form.cleaned_data['assignable']
            parent = form.cleaned_data['parent']
            ids = request.POST['ids'].split(',') if 'ids' in request.POST and request.POST['ids'] else []
            permissions = list(Permission.objects.filter(id__in=ids))
            role = form.save()
            role.permissions.set(permissions)
            role.save()
            role.extension.assignable = assignable
            role.extension.parent = parent
            role.extension.save()
            response = {'result': 'Ok', 'id': str(role.id), 'name': role.name}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    permission_sections = _generate_permission_sections()
    roles = [('', '--Select--')] + [(str(role.id), role.name) for role in list(Group.objects.all())]
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'roles': roles,
        'permission_sections': permission_sections,
        'menu_page': 'admin',
    }
    template_path = 'admin/add_user_role.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_user_role(request, role_id):
    instance = Group.objects.prefetch_related('permissions').get(pk=role_id)
    form = GroupForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            assignable = form.cleaned_data['assignable']
            parent = form.cleaned_data['parent']
            ids = request.POST['ids'].split(',') if 'ids' in request.POST else []
            permissions = list(Permission.objects.filter(id__in=ids))
            role = form.save()
            role.permissions.set(permissions)
            role.save()
            role.extension.assignable = assignable
            role.extension.parent = parent
            role.extension.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    permission_sections = _generate_permission_sections(
        [permission.id for permission in list(instance.permissions.all())]
    )
    roles = [('', '--Select--')] + [(str(role.id), role.name) for role in list(Group.objects.all())]
    context_info = {
        'request': request,
        'user': request.user,
        'form': form,
        'roles': roles,
        'role_id': str(instance.id),
        'permission_sections': permission_sections,
        'menu_page': 'admin',
    }
    template_path = 'admin/edit_user_role.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_team(request):
    form = TeamForm(request.POST or None)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            team = form.save()
            response = {'result': 'Ok', 'id': str(team.team_id), 'name': team.name}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    teams = [('', '--Select--')] + [(str(team.team_id), team.name) for team in list(Team.objects.all())]
    context_info = {
        'request': request,
        'teams': teams,
        'user': request.user,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/add_team.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_team(request, team_id):
    instance = Team.objects.get(team_id=team_id)
    form = TeamForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            form.save()
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    teams = [('', '--Select--')] + [(str(team.team_id), team.name) for team in list(Team.objects.all())]
    context_info = {
        'request': request,
        'teams': teams,
        'team_id': str(instance.team_id),
        'user': request.user,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/edit_team.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_payee(request, company_id):
    company = Company.objects.prefetch_related('payees').get(company_id=company_id)
    form = PayeeForm(request.POST or None)
    errors = []
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            payee = form.save(commit=False)
            payee.company_id = company_id
            payee.save()
            return redirect('add_payee', company_id=company_id)
        else:
            errors = get_form_errors(form)
    payees = list(company.payees.all())
    context_info = {
        'request': request,
        'user': request.user,
        'company_id': str(company_id),
        'payees': payees,
        'form': form,
        'errors': errors,
        'menu_page': 'admin',
    }
    template_path = 'admin/add_payee.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_payee(request, company_id, payee_id):
    company = Company.objects.prefetch_related('payees').get(company_id=company_id)
    instance = Payee.objects.get(payee_id=payee_id)
    form = PayeeForm(request.POST or None, instance=instance)
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            payee = form.save()
            response = {'result': 'Ok', 'default_for_company': payee.default_for_company, 'name': payee.name,
                        'bank_name': payee.bank_name, 'routing_number': payee.routing_number,
                        'account_number': payee.account_number, 'account_type': payee.account_type,
                        'name_on_account': payee.name_on_account, 'payee_id': payee.payee_id}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    payees = list(company.payees.all())
    context_info = {
        'request': request,
        'payees': payees,
        'payee_id': str(payee_id),
        'company_id': str(company_id),
        'user': request.user,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/edit_payee.html'
    return _render_response(request, context_info, template_path)


@login_required
def add_user(request):
    form = CreateUserForm(request.POST or None)
    errors = []
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            user = form.save()
            return redirect('edit_user', user_id=user.id)
        else:
            errors = get_form_errors(form)
    context_info = {
        'request': request,
        'user': request.user,
        'errors': errors,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/add_user.html'
    return _render_response(request, context_info, template_path)


@login_required
def edit_user(request, user_id):
    instance = User.objects.prefetch_related('groups').get(id=user_id)
    post_data = request.POST.copy()
    if post_data and 'groups' in post_data and post_data['groups']:
        post_data['groups'] = [post_data['groups']]
    form = EditUserForm(post_data or None, instance=instance)
    if request.method == 'POST' and post_data:
        if form.is_valid():
            form.save()
            form.save_m2m()
            #  TODO: Implement send email login details.
            response = {'result': 'Ok'}
        else:
            response = {'errors': get_form_errors(form)}
        return JsonResponse(response)
    role_id = instance.groups.all().first().id if instance.groups.all().first() else ''
    context_info = {
        'request': request,
        'user': request.user,
        'edited_user': instance,
        'role_id': role_id,
        'form': form,
        'menu_page': 'admin',
    }
    template_path = 'admin/edit_user.html'
    return _render_response(request, context_info, template_path)


@login_required
def suspend_user(request, user_id):
    if request.is_ajax() and request.method == 'POST':
        User.objects.filter(id=user_id).update(is_active=False)
        return JsonResponse({'result': 'Ok'})


@login_required
def activate_user(request, user_id):
    if request.is_ajax() and request.method == 'POST':
        User.objects.filter(id=user_id).update(is_active=True)
        return JsonResponse({'result': 'Ok'})


#######################################################################


def render404(request):
    return render(request, '404.html', status=404)


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
            data = request.POST.copy()
            data['created_by'] = request.user
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
