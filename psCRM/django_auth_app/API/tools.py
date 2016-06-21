# from oauthlib.common import generate_token
# from django.http import JsonResponse
# from oauth2_provider.models import AccessToken, Application, RefreshToken
# from django.utils.timezone import now, timedelta
# import settings
#
#
# def get_token_json(access_token, user):
#     """
#     Takes an AccessToken instance as an argument
#     and returns a JsonResponse instance from that
#     AccessToken
#     """
#     token = {
#         'full_name': user.profile.full_name,
#         "username": user.username,
#         "email": user.email,
#         "profile_photo":  settings.SITE_DOMAIN + user.profile.profile_photo.url if user.profile.profile_photo else "",
#         "profile_photo_thumb": settings.SITE_DOMAIN + user.profile.profile_photo_thumb.url if user.profile.profile_photo_thumb else "",
#         "profile_photo_original": settings.SITE_DOMAIN + user.profile.profile_photo_original.url if user.profile.profile_photo_original else "",
#         "phone_number": user.profile.phone_number,
#         "gender": user.profile.gender,
#         "birthday": user.profile.birthday,
#         "country": user.profile.country,
#         "address": user.profile.address,
#         "website": user.profile.website,
#         "twitter": user.profile.twitter,
#         "facebook": user.profile.facebook,
#         "linkedin": user.profile.linkedin,
#         "about": user.profile.about,
#         'access_token': access_token.token,
#     }
#     return JsonResponse(token)
#
#
# def get_access_token(user):
#     """
#     Takes a user instance and return an access_token as a JsonResponse
#     instance.
#     """
#
#     # our oauth2 app
#     app = Application.objects.get(name="Web App")
#
#     # We delete the old access_token and refresh_token
#     try:
#         old_access_token = AccessToken.objects.get(
#             user=user, application=app)
#         old_refresh_token = RefreshToken.objects.get(
#             user=user, access_token=old_access_token
#         )
#     except:
#         pass
#     else:
#         old_access_token.delete()
#         old_refresh_token.delete()
#
#     # we generate an access token
#     token = generate_token()
#     # we generate a refresh token
#     refresh_token = generate_token()
#
#     expires = now() + timedelta(seconds=settings.
#                                 ACCESS_TOKEN_EXPIRE_SECONDS)
#     scope = "read write"
#
#     # we create the access token
#     access_token = AccessToken.objects.\
#         create(user=user,
#                application=app,
#                expires=expires,
#                token=token,
#                scope=scope)
#
#     # we create the refresh token
#     RefreshToken.objects.\
#         create(user=user,
#                application=app,
#                token=refresh_token,
#                access_token=access_token)
#
#     # we call get_token_json and returns the access token as json
#     return get_token_json(access_token, user)