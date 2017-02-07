from django.conf.urls import include, url
from django.conf.urls.static import static

from sundog import views
from sundog.routing import module_urls, package_urls

import settings
import sundog.components

urlpatterns = module_urls(views) + package_urls(sundog.components) + [
    url(r'^auth/login/$', views.login_user, name='login'),
    url(r'^auth/logout/$', views.logout_user, name='logout'),

    url(r'^tinymce/', include('tinymce.urls')),

    url(r'^$', views.index, name='index'),
    url(r'^terms/$', views.terms, name="terms"),

    url(r'^contact/add/$', views.add_contact, name='add_contact'),
    url(r'^contact/(?P<contact_id>\d+)/edit/$', views.edit_contact, name='edit_contact'),
    url(r'^contact/(?P<contact_id>\d+)/delete/$', views.delete_contact, name='delete_contact'),
    url(r'^contact/(?P<contact_id>\d+)/edit/bankAccount/$', views.edit_bank_account, name='edit_bank_account'),
    url(r'^contact/(?P<contact_id>\d+)/edit/status/$', views.edit_contact_status, name='edit_contact_status'),
    url(r'^contact/(?P<contact_id>\d+)/dashboard/$', views.contact_dashboard, name='contact_dashboard'),
    url(r'^contact/(?P<contact_id>\d+)/budgetAnalysis/$', views.budget_analysis, name='budget_analysis'),
    url(r'^contact/(?P<contact_id>\d+)/budgetAnalysis/save/$', views.budget_analysis_save, name='budget_analysis_save'),
    url(r'^contact/(?P<contact_id>\d+)/budgetAnalysis/delete/$', views.delete_budget_analysis, name='delete_budget_analysis'),
    url(r'^contact/(?P<contact_id>\d+)/note/add/$', views.add_note, name='add_note'),
    url(r'^contact/(?P<contact_id>\d+)/call/add/$', views.add_call, name='add_call'),
    url(r'^contact/(?P<contact_id>\d+)/email/add/$', views.add_email, name='add_email'),
    url(r'^contact/(?P<contact_id>\d+)/uploadFile/$', views.upload_file, name='upload_file'),
    url(r'^contact/(?P<contact_id>\d+)/uploadedFile/(?P<uploaded_id>\d+)/view/$', views.uploaded_file_view, name='uploaded_file_view'),
    url(r'^contact/(?P<contact_id>\d+)/uploadedFile/(?P<uploaded_id>\d+)/delete/$', views.uploaded_file_delete, name='uploaded_file_delete'),
    url(r'^contact/(?P<contact_id>\d+)/creditors/debt/add/$', views.add_debt, name='add_debt'),
    url(r'^contact/(?P<contact_id>\d+)/creditors/debt/(?P<debt_id>\d+)/edit/$', views.edit_debt, name='edit_debt'),
    url(r'^contact/(?P<contact_id>\d+)/creditors/debt/edit/enrolled/$', views.edit_debt_enrolled, name='edit_debt_enrolled'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/plan/add/$', views.add_contact_enrollment, name='add_contact_enrollment'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/plan/edit/$', views.edit_contact_enrollment, name='edit_contact_enrollment'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/$', views.contact_enrollment_details, name='contact_enrollment_details'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/payment/add/$', views.add_payment, name='add_payment'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/payment/edit/$', views.edit_payment, name='edit_payment'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/performanceFees/?$', views.contact_schedule_performance_fees, name='contact_schedule_performance_fees'),
    url(r'^contact/(?P<contact_id>\d+)/enrollment/payments/edit/$', views.adjust_payments, name='adjust_payments'),
    url(r'^contact/(?P<contact_id>\d+)/enrollmentPlan/(?P<enrollment_plan_id>\d+)/getInfo/$', views.get_enrollment_plan_info, name='get_enrollment_plan_info'),
    url(r'^contact/(?P<contact_id>\d+)/debts/getInfo/$', views.get_debts_info, name='get_debts_info'),
    url(r'^debt/(?P<debt_id>\d+)/offer/$', views.get_debt_offer, name='get_debt_offer'),
    url(r'^contact/(?P<contact_id>\d+)/settlement/offers$', views.contact_settlement_offer, name='contact_settlement_offer'),
    url(r'^contact/(?P<contact_id>\d+)/settlement/(?P<settlement_offer_id>\d+)/complete/$', views.contact_settlement, name='contact_settlement'),
    url(r'^enrollment/plan/add/$', views.add_enrollment_plan, name='add_enrollment_plan'),
    url(r'^enrollment/plan/(?P<enrollment_plan_id>\d+)/edit/$', views.edit_enrollment_plan, name='edit_enrollment_plan'),
    url(r'^enrollment/plan/(?P<enrollment_plan_id>\d+)/delete/$', views.delete_enrollment_plan, name='delete_enrollment_plan'),
    url(r'^enrollment/feeProfiles/add/$', views.add_fee_profile, name='add_fee_profile'),
    url(r'^enrollment/feeProfile/(?P<fee_profile_id>\d+)/edit/$', views.edit_fee_profile, name='edit_fee_profile'),
    url(r'^enrollment/feeProfile/(?P<fee_profile_id>\d+)/delete/$', views.delete_fee_profile, name='delete_fee_profile'),
    url(r'^enrollment/settings/$', views.workflow_settings, name='workflow_settings'),
    url(r'^enrollment/settings/save/$', views.workflow_settings_save, name='workflow_settings_save'),
    url(r'^enrollments/$', views.enrollments_list, name='enrollments_list'),
    url(r'^debtNote/add/$', views.debt_add_note, name='debt_add_note'),
    url(r'^stage/statuses/$', views.get_stage_statuses, name='get_stage_statuses'),
    url(r'^campaigns/$', views.campaigns, name='campaigns'),
    url(r'^campaigns/addCampaign/$', views.add_campaign, name='add_campaign'),
    url(r'^campaigns/editCampaign/$', views.edit_campaign, name='edit_campaign'),
    url(r'^campaigns/addSource/$', views.add_source, name='add_source'),
    url(r'^workflow/?$', views.workflows, name='workflows'),
    url(r'^workflow/addStage/$', views.add_stage, name='add_stage'),
    url(r'^workflow/editStage/$', views.edit_stage, name='edit_stage'),
    url(r'^workflow/deleteStage/(?P<stage_id>\d+)/$', views.delete_stage, name='delete_stage'),
    url(r'^workflow/addStatus/$', views.add_status, name='add_status'),
    url(r'^workflow/editStatus/$', views.edit_status, name='edit_status'),
    url(r'^workflow/deleteStatus/(?P<status_id>\d+)/$', views.delete_status, name='delete_status'),
    url(r'^workflow/updateStageOrder/$', views.update_stage_order, name='update_stage_order'),
    url(r'^workflow/updateStatusOrder/$', views.update_status_order, name='update_status_order'),
    url(r'^creditors/$', views.creditors_list, name='creditors_list'),
    url(r'^creditor/add/$', views.add_creditor, name='add_creditor'),

    url(r'^client/add/$', views.add_client_ajax, name='ajax_client_add'),

    url(r'^company/add/$', views.add_company, name='add_company'),
    url(r'^company/(?P<company_id>\d+)/edit/$', views.edit_company, name='edit_company'),
    url(r'^company/(?P<company_id>\d+)/compensationTemplate/add/$', views.add_compensation_template, name='add_compensation_template'),
    url(r'^company/(?P<company_id>\d+)/compensationTemplate/(?P<compensation_template_id>\d+)/edit/$', views.edit_compensation_template, name='edit_compensation_template'),
    url(r'^company/(?P<company_id>\d+)/payee/add/$', views.add_payee, name='add_payee'),
    url(r'^company/(?P<company_id>\d+)/payee/(?P<payee_id>\d+)/edit/$', views.edit_payee, name='edit_payee'),
    url(r'^user/add/$', views.add_user, name='add_user'),
    url(r'^user/(?P<user_id>\d+)/edit/$', views.edit_user, name='edit_user'),
    url(r'^user/(?P<user_id>\d+)/suspend/$', views.suspend_user, name='suspend_user'),
    url(r'^user/(?P<user_id>\d+)/activate/$', views.activate_user, name='activate_user'),
    url(r'^user/role/add/$', views.add_user_role, name='add_user_role'),
    url(r'^user/role/(?P<role_id>\d+)/edit/$', views.edit_user_role, name='edit_user_role'),
    url(r'^team/add/$', views.add_team, name='add_team'),
    url(r'^team/(?P<team_id>\d+)/edit/$', views.edit_team, name='edit_team'),
]

handler404 = 'sundog.views.render404'

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
        show_indexes=True
    )

    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
