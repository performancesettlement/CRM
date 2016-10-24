from django.contrib.auth.decorators import login_required
from django.http.response import JsonResponse
from django_auth_app.models import UserPreferences


@login_required
def update_preferences_for_section_collapsed_state(request):
    if request.method == 'POST':
        user_preferences = (
            UserPreferences
            .objects
            .get_or_create(
                related_user_id=request.user.id,
            )
        )[0]
        section = request.POST.get('id')
        if section == "Accounts":
            user_preferences.accounts_collapsed = \
                not user_preferences.accounts_collapsed
        elif section == "Authentication_and_Authorization":
            user_preferences.auth_collapsed = \
                not user_preferences.auth_collapsed
        elif section == "Avatar":
            user_preferences.avatar_collapsed = \
                not user_preferences.avatar_collapsed
        elif section == "SunDog":
            user_preferences.sundog_collapsed = \
                not user_preferences.sundog_collapsed
        elif section == "App_Log":
            user_preferences.app_log_collapsed = \
                not user_preferences.app_log_collapsed
        user_preferences.save()
        response_data = {'result': 'Success!'}
    else:
        response_data = {'result': 'Fail!'}
    return JsonResponse(response_data)


@login_required
def get_preferences_for_sections_collapsed_state(request):
    if request.method == 'GET':
        user_preferences = (
            UserPreferences
            .objects
            .get_or_create(
                related_user_id=request.user.id,
            )
        )[0]

        return JsonResponse({
            'accounts_collapsed_id': "Accounts",
            'accounts_collapsed': user_preferences.accounts_collapsed,
            'auth_collapsed_id': "Authentication_and_Authorization",
            'auth_collapsed': user_preferences.auth_collapsed,
            'avatar_collapsed_id': "Avatar",
            'avatar_collapsed': user_preferences.avatar_collapsed,
            'sundog_collapsed_id': "SunDog",
            'sundog_collapsed': user_preferences.sundog_collapsed,
            'app_log_collapsed_id': "App_Log",
            'app_log_collapsed': user_preferences.app_log_collapsed,
        })
