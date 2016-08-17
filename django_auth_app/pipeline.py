from django.core.files.base import ContentFile
import urllib


"""
    Saves the profile picture of a user in case that he's logged in with twitter auth
"""
def save_profile_picture(strategy, user, response, details,
                         is_new=False,*args,**kwargs):
    if "twitter" in kwargs['backend'].redirect_uri:
        if response.get('profile_image_url'):
            image_name = 'avatar_original_%s.jpg' % user.id
            image_url = response.get('profile_image_url').replace("_normal","_400x400")
            content = urllib.urlopen(image_url)
            profile = user.profile
            profile.full_name = user.first_name
            profile.profile_photo_original.save(save=True)
                
