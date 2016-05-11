from django.contrib.auth.models import User
from rest_framework import serializers
from django_auth_app import models
import settings


"""
    User serializer
"""
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name',
                  'last_name', 'email')
        read_only_fields = ('id',)
        write_only_fields = ('password',)

    def restore_object(self, attrs, instance=None):
        user = super(UserSerializer, self).restore_object(attrs, instance)
        user.set_password(attrs['password'])
        return user

"""
    UserProfile serializer
"""
class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.SerializerMethodField("get_email_field")
    username = serializers.SerializerMethodField("get_username_field")
    birthday = serializers.SerializerMethodField("get_birthday_field")
    profile_photo = serializers.SerializerMethodField("get_profile_photo_field")
    profile_photo_thumb = serializers.SerializerMethodField("get_profile_photo_thumb_field")
    profile_photo_original = serializers.SerializerMethodField("get_profile_photo_original_field")
    class Meta:
        model = models.UserProfile
        fields = ('id', 'full_name', 'username', 'email', 'profile_photo','profile_photo_thumb','profile_photo_original', 'phone_number','gender','birthday','country','address','website','twitter','facebook','linkedin','about')
    
    def restore_object(self, attrs, instance=None):
        user_profile = super(UserProfileSerializer, self).restore_object(attrs, instance)
        return user_profile

    def get_username_field(self, user_profile):
        return (user_profile.user.username)

    def get_email_field(self, user_profile):
        return (user_profile.user.email)

    def get_birthday_field(self, user_profile):
        if user_profile.birthday is not None:
            return str(user_profile.birthday);
        else:
            return ""
    def get_profile_photo_field(self, user_profile):
        return settings.SITE_DOMAIN + (user_profile.profile_photo.url if user_profile.profile_photo else "")
    def get_profile_photo_thumb_field(self, user_profile):
        return settings.SITE_DOMAIN + (user_profile.profile_photo_thumb.url if user_profile.profile_photo_thumb else "") 
    def get_profile_photo_original_field(self, user_profile):
        return settings.SITE_DOMAIN + (user_profile.profile_photo_original.url if user_profile.profile_photo_thumb else "")