from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django_auth_app.models import UserPreferences
from sundog import services
from django.http.response import JsonResponse
from sundog.decorators import bypass_impersonation_login_required


# def areas_by_state(request):
#     areas_array = []
#     if request.is_ajax() and request.GET['state_id']:
#         areas = services.get_areas_by_state(request.GET['state_id'])
#         if areas is not None:
#             areas_array = [{'id': a.area_id, 'name': a.name}
#                            for a in areas]
#
#     return JsonResponse({'results': areas_array})
#
#
# def communities_by_area(request):
#     communities_array = []
#     if request.is_ajax() and request.GET['area_id']:
#         communities = services.get_communities_by_area(request.GET['area_id'])
#         if communities is not None:
#             communities_array = [{'id': a.community_id, 'name': a.name}
#                                  for a in communities]
#
#     return JsonResponse({'results': communities_array})


def get_completed_by_file_status(request):
    completed = 0
    if request.is_ajax() and request.GET['status_id']:
        completed = services.get_completed_by_file_status(request.GET['status_id'])

    return JsonResponse({'result': completed})


@login_required
def update_preferences_for_section_collapsed_state(request):
    response_data = {}
    if request.method == 'POST':
        user_preferences = UserPreferences.objects.get_or_create(related_user_id=request.user.id)[0]
        section = request.POST.get('id')
        if section == "Accounts":
            user_preferences.accounts_collapsed = not user_preferences.accounts_collapsed
        elif section == "Authentication_and_Authorization":
            user_preferences.auth_collapsed = not user_preferences.auth_collapsed
        elif section == "Avatar":
            user_preferences.avatar_collapsed = not user_preferences.avatar_collapsed
        elif section == "SunDog":
            user_preferences.sundog_collapsed = not user_preferences.sundog_collapsed
        elif section == "App_Log":
            user_preferences.app_log_collapsed = not user_preferences.app_log_collapsed
        user_preferences.save()
        response_data['result'] = 'Success!'
    else:
        response_data['result'] = 'Fail!'
    return JsonResponse(response_data)


@login_required
def get_preferences_for_sections_collapsed_state(request):
    response_data = {}
    if request.method == 'GET':
        user_preferences = UserPreferences.objects.get_or_create(related_user_id=request.user.id)[0]
        response_data['accounts_collapsed_id'] = "Accounts"
        response_data['accounts_collapsed'] = user_preferences.accounts_collapsed
        response_data['auth_collapsed_id'] = "Authentication_and_Authorization"
        response_data['auth_collapsed'] = user_preferences.auth_collapsed
        response_data['avatar_collapsed_id'] = "Avatar"
        response_data['avatar_collapsed'] = user_preferences.avatar_collapsed
        response_data['sundog_collapsed_id'] = "SunDog"
        response_data['sundog_collapsed'] = user_preferences.sundog_collapsed
        response_data['app_log_collapsed_id'] = "App_Log"
        response_data['app_log_collapsed'] = user_preferences.app_log_collapsed
        return JsonResponse(response_data)
