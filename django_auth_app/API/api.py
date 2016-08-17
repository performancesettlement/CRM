from django_auth_app.forms import RegistrationForm
from django.contrib.auth.models import User
from rest_framework import permissions
from django.contrib.auth import login, logout
from rest_framework.views import APIView
from django_auth_app.API import serializers, authenticators
from django_auth_app import models
from django.http.response import HttpResponse, HttpResponseRedirect
import json
from django.core.validators import validate_email
import settings
import datetime
import hashlib, random
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django_auth_app.models import UserProfile


"""
####################### END POINTS #######################
"""

"""
    Endpoint /api/upload
        Handles the file uploads to the server for the current user
        in case of request.POST['action_type'] == 'profile_photo' we upload
        the user photo to the User object in DB

"""
class UploadFileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        user = request.user
        if user:
            user_profile = user.profile
            if ('file' in request.FILES and request.FILES['file'] and request.FILES['file'] is not None
                and 'action_type' in request.POST and request.POST['action_type'] == 'profile_photo'):                    
                try:
                    image_name = 'avatar_original_%s.jpg' % user.id
                    user_profile.profile_photo_original.save(save=True)
                    response_data = get_response_body(True,settings.SITE_DOMAIN + user_profile.profile_photo.url)
                    return HttpResponse(json.dumps(response_data), content_type='application/json')
        
                except Exception as exception:
                    errors_list = []
                    errors_list.append({'id':'profile_photo','error':exception})
                    response_data = get_response_body(False,errors_list)
                    return HttpResponse(json.dumps(response_data), content_type='application/json')
            else:
                return HttpResponse(json.dumps(get_response_body(False,'Invalid file content')), content_type='application/json')    
        else:
            return HttpResponse(json.dumps(get_response_body(False,'401 unauthorized')), content_type='application/json')    
        
"""
    Endpoint /api/profile
        Handles all the requests for User profile.

        POST: Update the user profile, only the full_name and email are mandatory.

        GET: Returns a object with all the fields descripted in serializers.py UserProfileSerializer
"""

class UserProfileView(APIView):
    serializer_class = serializers.UserProfileSerializer
    model = models.UserProfile
    permission_classes = (permissions.IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        user = request.user
        if user:
            user_profile = user.profile
            valid_data = True
            errors_list = []
            if 'full_name' in request.POST and request.POST['full_name'] and request.POST['full_name'] is not None:
                user_profile.full_name = request.POST['full_name']
            else:
                valid_data = False
                errors_list.append({'id':'full_name','error':'This field is required.'})


            if 'email' in request.POST  and request.POST['email'] and request.POST['email'] is not None:
                try:
                    validate_email(request.POST['email'])
                except:
                    valid_data = False
                    errors_list.append({'id':'email','error':'The email format is invalid.'})
                else:
                    user.email = request.POST['email']
            else:
                valid_data = False
                errors_list.append({'id':'email','error':'This field is required.'})
            
            
            
            #optional
            if 'phone_number' in request.POST and request.POST['phone_number'] and request.POST['phone_number'] is not None and request.POST['phone_number'] != 'null':
                user_profile.phone_number = request.POST['phone_number']

            if 'gender' in request.POST and request.POST['gender'] and request.POST['gender'] is not None and request.POST['gender'] != 'null':
                user_profile.gender = request.POST['gender']

            if 'birthday' in request.POST and request.POST['birthday'] and request.POST['birthday'] is not None and request.POST['birthday'] != 'null':
                try:
                    user_profile.birthday = request.POST['birthday'];
                except Exception:
                    valid_data = False
                    errors_list.append({'id':'birthday','error':'The date format is incorrect.'})

            if 'country' in request.POST and request.POST['country'] and request.POST['country'] is not None and request.POST['country'] != 'null':
                user_profile.country = request.POST['country']

            if 'address' in request.POST and request.POST['address'] and request.POST['address'] is not None and request.POST['address'] != 'null':
                user_profile.address = request.POST['address']
            
            if 'website' in request.POST and request.POST['website'] and request.POST['website'] is not None and request.POST['website'] != 'null':
                user_profile.website = request.POST['website']

            if 'twitter' in request.POST and request.POST['twitter'] and request.POST['twitter'] is not None and request.POST['twitter'] != 'null':
                user_profile.twitter = request.POST['twitter']

            if 'facebook' in request.POST and request.POST['facebook'] and request.POST['facebook'] is not None and request.POST['facebook'] != 'null':
                user_profile.facebook = request.POST['facebook']

            if 'linkedin' in request.POST and request.POST['linkedin'] and request.POST['linkedin'] is not None and request.POST['linkedin'] != 'null':
                user_profile.linkedin = request.POST['linkedin']

            if 'about' in request.POST and request.POST['about'] and request.POST['about'] is not None and request.POST['about'] != 'null':
                user_profile.about = request.POST['about']

            
            if valid_data:
                user.save()
                user_profile.save()                
                return HttpResponse(json.dumps(get_response_body(True,serializers.UserProfileSerializer(user_profile).data)), content_type='application/json')            
            else:
                response_data = get_response_body(False,errors_list)
                return HttpResponse(json.dumps(response_data), content_type='application/json')
        else:
            return HttpResponse(json.dumps(get_response_body(False,'401 unauthorized')), content_type='application/json')    
        
    def get(self, request, *args, **kwargs):
        if request.user and hasattr(request.user, 'profile'):
            response_data = get_response_body(True,serializers.UserProfileSerializer(request.user.profile).data)
            return HttpResponse(json.dumps(response_data), content_type='application/json')
        else:
            return HttpResponse(json.dumps(get_response_body(False,'401 unauthorized'), content_type='application/json'))

"""
    Endpoint /api/users
        Handles the signup for a user, uses RegistrationForm to validate the fields for signup
"""
class UserView(APIView):
    serializer_class = serializers.UserSerializer
    model = User
    
    def post(self, request, *args, **kwargs):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()


            #Get user by username
            username = request.POST['username']
            email = request.POST['email']
            user=User.objects.get(username=username)
            
            #initialize the new user with active state false
            #user.is_active = False
            #user.save()
            
            #activation key 
            salt = hashlib.sha1(str(random.random())).hexdigest()[:5]            
            activation_key = hashlib.sha1(salt+user.email).hexdigest()            
            key_expires = datetime.datetime.today() + datetime.timedelta(2)

            profile = user.profile

            profile.activation_key = activation_key
            profile.key_expires = key_expires
            profile.save()

            # Send email with activation key
            #mailer.send_activation_email(email,username,activation_key)

            return HttpResponse(json.dumps(get_response_body(True,None)), content_type='application/json')

        errors_list = []
        for s in form.errors.items():
            error = {'id':'%s' % (s[0]), 'error':'%s' % (s[1][0].replace(".", ":"))}
            errors_list.append(error)

        response_data = get_response_body(False,errors_list)
        return HttpResponse(json.dumps(response_data), content_type='application/json')


"""
    Endpoint /api/auth

    Handles the login/logout for the current user.

        POST: Uses the standart login of django.

        DELETE: Kill the session for the current user
"""
class AuthView(APIView):
    authentication_classes = (authenticators.QuietBasicAuthentication,)

    def post(self, request, *args, **kwargs):
        login(request, request.user)
        #return get_access_token(request.user)
        return HttpResponse(json.dumps(get_response_body(True,None)), content_type='application/json')
    
    def delete(self, request, *args, **kwargs):
        logout(request)
        return HttpResponse(json.dumps(get_response_body(True,None)), content_type='application/json')

def get_response_body(success,message):
    if message is not None:
        return {"success": success, "response": message}
    else:
        return {"success": success}

"""
    Endpoint for account confirmation
"""

class ConfirmView(APIView):

    def get(self, request, *args, **kwargs):
        #check if user is already logged in and if he is redirect him to some other url, e.g. home
        #if request.user.is_authenticated():
        #    return HttpResponse(json.dumps(get_response_body(False,"User already logged in")), content_type='application/json')

        # check if there is UserProfile which matches the activation key (if not then display 404)
        activation_key = kwargs['activation_key']
        user_profile = get_object_or_404(UserProfile, activation_key=activation_key)

        user = user_profile.user

        #check if urser is already active
        if user.is_active:
            return HttpResponse(json.dumps(get_response_body(False,"This user has already activated his account")), content_type='application/json')

        #check if the activation key has expired, if it hase then render confirm_expired.html
        if user_profile.key_expires < timezone.now():
            return HttpResponse(json.dumps(get_response_body(False,"The provided token has expired")), content_type='application/json')
        
        #if the key hasn't expired save user and set him as active and render some template to confirm activation
        user.is_active = True
        user.save()

        return HttpResponseRedirect('/#/activate-account-success')

#
# class ApiEndpoint(ProtectedResourceView):
#     def get(self, request, *args, **kwargs):
#         return HttpResponse('Hello, OAuth2!')