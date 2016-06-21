from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from mimetypes import MimeTypes
import urllib
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_auth_app import enums
from sundog.cache.user.info import store_cache_user

"""
    UserProfile is the principal profile model for our users
"""


class UserProfile(models.Model):
    related_user = models.OneToOneField(User, related_name='related_user')
    birthday = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=enums.GENDER_CHOICES, blank=True, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=60, blank=True, null=True)
    state = models.CharField(max_length=4, choices=enums.US_STATES, blank=True, null=True)
    city = models.CharField(max_length=60, blank=True, null=True)
    zip_code = models.CharField(max_length=12, blank=True, null=True)
    address = models.CharField(max_length=300, blank=True, null=True)
    website = models.CharField(max_length=300, blank=True, null=True)
    twitter = models.CharField(max_length=300, blank=True, null=True)
    facebook = models.CharField(max_length=200, blank=True, null=True)
    linkedin = models.CharField(max_length=200, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    profile_photo_thumb = models.ImageField(upload_to='profiles/', max_length=500, blank=True, null=True)
    profile_photo_original = models.ImageField(upload_to='profiles/', max_length=500, blank=True, null=True)
    profile_photo = models.ImageField(upload_to='profiles/', max_length=500, blank=True, null=True)
    activation_key = models.CharField(max_length=50, blank=True, null=True)
    key_expires = models.DateTimeField(blank=True, null=True)
    recover_key = models.CharField(max_length=50, blank=True, null=True)
    recover_key_expires = models.DateTimeField(blank=True, null=True)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    timezone = models.CharField(max_length=100, null=True, blank=True, choices=enums.FORMATTED_TIMEZONES)

    def __unicode__(self):
        return '%s' % self.related_user.username

    def create_thumbnail(self):
        if not self.profile_photo_original:
            return
        # Set our max thumbnail size in a tuple (max width, max height)
        thumbnail_size = (100, 100)
        mime = MimeTypes()
        # TODO: this function does not exist? change this to work.
        url = urllib.pathname2url(self.profile_photo_original.file.name)
        mime_type = mime.guess_type(url)
        django_type = mime_type[0]
        if django_type == 'image/jpeg':
            pil_type = 'jpeg'
            file_extension = 'jpg'
        elif django_type == 'image/png':
            pil_type = 'png'
            file_extension = 'png'

        image = Image.open(self.profile_photo_original.file)

        image.thumbnail(thumbnail_size, Image.ANTIALIAS)

        # Save the thumbnail
        temp_handle = StringIO()
        image.save(temp_handle, pil_type)
        temp_handle.seek(0)

        # Save image to a SimpleUploadedFile which can be saved into
        # ImageField
        suf = SimpleUploadedFile(
            os.path.split(self.profile_photo_original.name)[-1], temp_handle.read(), content_type=django_type)
        self.profile_photo_thumb.save(
            '%s_thumbnail.%s' % (os.path.splitext(suf.name)[0], file_extension), suf, save=False)
 
    def resize_original(self):
        if not self.profile_photo_original:
            return
            # Set our max thumbnail size in a tuple (max width, max height)

        image_size = (400, 400)
        mime = MimeTypes()
        url = urllib.pathname2url(self.profile_photo_original.file.name)
        mime_type = mime.guess_type(url)
        django_type = mime_type[0]
        if django_type == 'image/jpeg':
            pil_type = 'jpeg'
            file_extension = 'jpg'
        elif django_type == 'image/png':
            pil_type = 'png'
            file_extension = 'png'

        image = Image.open(self.profile_photo_original.file)

        image.thumbnail(image_size, Image.ANTIALIAS)

        # Save the thumbnail
        temp_handle = StringIO()
        image.save(temp_handle, pil_type)
        temp_handle.seek(0)

        # Save image to a SimpleUploadedFile which can be saved into
        # ImageField
        suf = SimpleUploadedFile(
            os.path.split(self.profile_photo_original.name)[-1], temp_handle.read(), content_type=django_type)
        self.profile_photo.save('%s_normal.%s' % (os.path.splitext(suf.name)[0], file_extension), suf, save=False)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.create_thumbnail()
        self.resize_original()
        super(UserProfile, self).save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class UserPreferences(models.Model):
    related_user = models.ForeignKey(User)
    accounts_collapsed = models.BooleanField(default=False)
    auth_collapsed = models.BooleanField(default=False)
    avatar_collapsed = models.BooleanField(default=False)
    social_accounts_collapsed = models.BooleanField(default=False)
    sundog_collapsed = models.BooleanField(default=False)
    app_log_collapsed = models.BooleanField(default=False)

    def __str__(self):
        return '%s' % self.related_user.username

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(UserPreferences, self).save(
            force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


User.preferences = property(lambda u: UserPreferences.objects.get_or_create(user=u)[0])


@receiver(post_save, sender=User)
def update_stock(sender, instance, **kwargs):
    store_cache_user(instance)
