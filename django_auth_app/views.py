from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth import login, logout
from django.utils.timezone import now, pytz
from django_auth_app.forms import LoginForm
from django.utils.html import strip_tags
from django.core.urlresolvers import reverse
import logging

logger = logging.getLogger(__name__)


def login_user(request):
    form = LoginForm(request.POST or None)
    form_errors = None
    user_tz = str(pytz.utc)
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
    return render(request, 'login.html', {'form': form, 'form_errors': form_errors})


def logout_user(request):
    logout(request)
    return HttpResponseRedirect("/")
