from django.shortcuts import render_to_response, render
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django_auth_app.forms import RegistrationForm, LoginForm, RecoverForm, ConfirmRecoverForm, ProfileForm
from django_auth_app.models import UserProfile
from django.utils.html import strip_tags
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
#from sundog.services import get_areas_by_state, get_communities_by_area
import settings
import mailer
import hashlib, random
import datetime
import logging
import messages
import services

"""
    View for the index page of the website, request.user is the logged in user, if no user is logged
    returns the anonymous user.
"""
# initialize logger
logger = logging.getLogger(__name__)


@login_required()
def profile_edit_view(request):
    form_errors = None
    user_profile = services.get_user_profile(request.user.id)
    form = ProfileForm(request.POST or None, initial={'username': request.user.username,'email': request.user.email, 'first_name': request.user.first_name, 'last_name': request.user.last_name}, instance=user_profile)
    ADDRESS_API_KEY = settings.ADDRESS_API_KEY
    # if user_profile.state_of_interest:
    #     form.fields['area_of_interest'].queryset = get_areas_by_state(user_profile.state_of_interest)
    # if user_profile.area_of_interest:
    #     form.fields['communities_of_interest'].queryset = get_communities_by_area(user_profile.area_of_interest)
    if request.POST:
        #update querysets
        # selected_state = request.POST["state_of_interest"]
        # selected_area = request.POST["area_of_interest"]
        # form.fields['area_of_interest'].queryset = get_areas_by_state(selected_state)
        # form.fields['communities_of_interest'].queryset = get_communities_by_area(selected_area)

        if form.is_valid():
            # save user data
            user = services.get_user(request.user.id)
            user.first_name = request.POST["first_name"]
            user.last_name = request.POST["last_name"]
            if request.POST["timezone"]:
                request.session['django_timezone'] = request.POST["timezone"]
            user.save()

            #save user profile data
            user_profile = form.save(commit=False)
            #user_profile.communities_of_interest = request.POST.getlist('communities_of_interest')
            user_profile.save()
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        form_errors.append(strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    return render(request, 'profile_form.html',{'form': form, 'form_errors': form_errors, 'ADDRESS_API_KEY': ADDRESS_API_KEY})


@login_required()
def my_profile_view(request):
    user_profile = services.get_user_profile(request.user.id)
    return render(request, 'my_profile.html', {'user_profile': user_profile})


@login_required()
def profile_upload_picture(request):
    context = RequestContext(request, {'request': request, 'user': request.user})
    return render_to_response('upload_picture.html', context_instance=context)


def login_user(request):
    form = LoginForm(request.POST or None)
    form_errors = None
    if request.method == 'POST' and request.POST:
        if form.is_valid():
            user = form.login(request)
            if user:
                login(request, user)
                user_tz = services.get_user_timezone(user.id)
                if user_tz:
                    request.session['django_timezone'] = user_tz
                else:
                    try:
                        user_tz = request.POST["timezone"]
                        request.session['django_timezone'] = user_tz
                        services.set_user_timezone(user_tz, user.id)
                    except:
                        pass
                return HttpResponseRedirect(reverse("home"))
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


def register_user(request):
    form = RegistrationForm(request.POST or None)
    profile_form = ProfileForm(request.POST or None)
    form_errors = None
    if request.POST:
        try:
            #update querysets
            # selected_state = request.POST["state_of_interest"]
            # selected_area = request.POST["area_of_interest"]
            # form.fields['area_of_interest'].queryset = get_areas_by_state(selected_state)
            # form.fields['communities_of_interest'].queryset = get_communities_by_area(selected_area)

            if form.is_valid() and profile_form.is_valid():

                # save user from auth
                form.save()

                # Get user by username
                username = request.POST['username']
                email = request.POST['email']
                user = User.objects.get(username=username)

                # initialize the new user with active state false
                user.is_active = False
                user.save()

                # activation key
                salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
                activation_key = hashlib.sha1(salt+user.email).hexdigest()
                key_expires = datetime.datetime.today() + datetime.timedelta(2)

                # save user profile
                profile = profile_form.save(commit=False)
                profile.related_user = user
                profile.activation_key = activation_key
                profile.key_expires = key_expires
                profile.save()

                # add to customer group
                services.set_customer_group_to_user(user)

                # profile.communities_of_interest = request.POST.getlist('communities_of_interest')
                # profile.save()

                # Send email with activation key
                activation_link = "%saccount/confirm/%s/" % (settings.SITE_DOMAIN, activation_key)
                mailer.send_template_email('Account confirmation','activation_mail.html',{'SITE_DOMAIN':settings.SITE_DOMAIN,'username':username, 'activation_link':activation_link},[email])

                return render_to_response('register_success.html', context_instance=RequestContext(request))
            else:
                form_errors = []
                for field in form:
                    if field.errors:
                        for field_error in field.errors:
                            field_error_text = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                            form_errors.append(field_error_text)
                for non_field_error in form.non_field_errors():
                    form_errors.append(non_field_error)
                for field in profile_form:
                    if field.errors:
                        for field_error in field.errors:
                            field_error_text = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                            if field_error_text not in form_errors:
                                form_errors.append(field_error_text)
                for non_field_error in profile_form.non_field_errors():
                    form_errors.append(non_field_error)
            return render(request, 'register.html', {'form': form, 'form_errors': form_errors, 'profile_form': profile_form})

        except Exception, e:
            logger.error(messages.ERROR_REGISTERING % request.POST['username'] if request.POST['username'] else "anonymous")
            logger.error(e)
            form.add_error(None, "Error creating the user")
            return render(request, 'register.html', {'form':form, 'profile_form':profile_form})
    return render(request, 'register.html', {'form':form, 'profile_form':profile_form})


def confirm_account(request, activation_key):
    # check if user is already logged in and if he is redirect him to some other url, e.g. home
    if request.user.is_authenticated():
        # TODO: inform the user he needs to logout from current account to activate another
        return HttpResponseRedirect("/")

    # check if there is UserProfile which matches the activation key (if not then display 404)
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)

    user = user_profile.related_user

    # check if user is already active
    if user.is_active:
        return render(request, 'already_active.html')

    # check if the activation key has expired, if it hase then render confirm_expired.html
    if user_profile.key_expires is None or user_profile.key_expires < timezone.now():
        return render(request, 'token_expired.html')

    # if the key hasn't expired save user and set him as active and render some template to confirm activation
    user.is_active = True
    user.save()

    return render(request, 'success_activation.html')


def recover_password(request):
    form = RecoverForm(request.POST or None)
    form_errors = None

    if request.POST:
        if form.is_valid():
            email = request.POST['email']
            # get the user by email and set recover key
            user = User.objects.get(email=email)
            recover_key = services.set_user_recover_key(user)
            username = user.username

            # Send email with recover key
            activation_link = "%saccount/new_password/%s/" % (settings.SITE_DOMAIN, recover_key)

            mailer.send_template_email('Recover password','recover_mail.html',{'SITE_DOMAIN':settings.SITE_DOMAIN,'username':username, 'recover_link':activation_link},[email])
            return render(request, 'recover_password_success.html')
        else:
            form_errors = []
            for field in form:
                if field.errors:
                    for field_error in field.errors:
                        field_error_text = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                        form_errors.append(field_error_text)
            for non_field_error in form.non_field_errors():
                form_errors.append(non_field_error)
    return render(request, 'recover_password.html', {'form': form, 'form_errors': form_errors })


@login_required()
def update_password(request):
    user = services.get_user(request.user.id)
    # generate a recover token
    recover_key = services.set_user_recover_key(user)
    form = ConfirmRecoverForm(initial={'recover_key': recover_key})
    return render(request, 'set_new_password.html', {'form':form})


def confirm_recover_account(request, recover_key):
    form = ConfirmRecoverForm(request.POST or None, initial={'recover_key': recover_key})
    form_errors = None
    #check if user is already logged in and if he is redirect him to some other url, e.g. home
    if request.method == 'GET' and request.user.is_authenticated():
        return HttpResponseRedirect("/")

    # check if there is UserProfile which matches the activation key (if not then display 404)
    user_profile = get_object_or_404(UserProfile, recover_key=recover_key)

    #check if user account is active
    #user = user_profile.related_user
    #if not user.is_active:
    #	return render(request, 'activation_pending.html')

    #check if the activation key has expired, if it hase then render confirm_expired.html
    if not user_profile or not user_profile.recover_key_expires or user_profile.recover_key_expires < timezone.now():
        return render(request, 'recover_token_expired.html')

    if request.POST and form.is_valid():
        # update password
        password = request.POST['password1']
        services.update_user_password(user_profile, password)

        return render(request, 'success_reset_password.html')
    else:
        form_errors = []
        for field in form:
            if field.errors:
                for field_error in field.errors:
                    field_error_text = strip_tags(field.html_name.replace("_", " ").title()) + ": " + field_error
                    form_errors.append(field_error_text)
        for non_field_error in form.non_field_errors():
            form_errors.append(non_field_error)
    return render(request, 'set_new_password.html', {'form':form, 'form_errors':form_errors})