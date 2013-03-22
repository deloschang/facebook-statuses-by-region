from django.utils.translation import ugettext

from social_auth.models import UserSocialAuth, SOCIAL_AUTH_MODELS_MODULE
from social_auth.exceptions import AuthAlreadyAssociated


def social_auth_user(backend, uid, user=None, *args, **kwargs):
    """Return UserSocialAuth account for backend/uid pair or None if it
    doesn't exists.

    Raise AuthAlreadyAssociated if UserSocialAuth entry belongs to another
    user.
    """
    social_user = UserSocialAuth.get_social_auth(backend.name, uid)
    if social_user:
        if user and social_user.user != user:

            # if facebook2, this is the 2nd step, which is OK
            if social_user.provider == 'facebook2':
                user = social_user.user


            else:
                msg = ugettext('This %(provider)s account is already in use.')
                raise AuthAlreadyAssociated(backend, msg % {
                    'provider': backend.name
                })
        elif not user:
            user = social_user.user
    return {'social_user': social_user, 'user': user}


def associate_user(backend, user, uid, social_user=None, *args, **kwargs):
    """Associate user social account with user instance."""
    if social_user:
        return None

    if not user:
        return {}

    try:
        social = UserSocialAuth.create_social_auth(user, uid, backend.name)
    except Exception, e:
        if not SOCIAL_AUTH_MODELS_MODULE.is_integrity_error(e):
            raise
        # Protect for possible race condition, those bastard with FTL
        # clicking capabilities, check issue #131:
        #   https://github.com/omab/django-social-auth/issues/131
        return social_auth_user(backend, uid, user, social_user=social_user,
                                *args, **kwargs)
    else:
        return {'social_user': social, 'user': social.user}


def load_extra_data(backend, details, response, uid, user, social_user=None,
                    *args, **kwargs):
    """Load extra data from provider and store it on current UserSocialAuth
    extra_data field.
    """
    
    # check if school has been filled out yet
    if user.get_profile().school == '':
        # check by email first
        if 'berkeley.edu' in response['email']:
            user.get_profile().school = 'Berkeley'
        elif 'dartmouth.edu' in response['email']:
            user.get_profile().school = 'Dartmouth'
        else:
            for index in range(0, len(response['education'])):
                # better to be too general than to filter by ID
                if 'Berkeley' in response['education'][index]['school']['name']: 
                    user.get_profile().school = 'Berkeley'
                    user.get_profile().save()
                    break
                elif 'Dartmouth' in response['education'][index]['school']['name']: 
                    user.get_profile().school = 'Dartmouth'
                    user.get_profile().save()
                    break

        user.get_profile().save()
        

    social_user = social_user or \
                  UserSocialAuth.get_social_auth(backend.name, uid)
    if social_user:
        extra_data = backend.extra_data(user, uid, response, details)
        if extra_data and social_user.extra_data != extra_data:
            if social_user.extra_data:
                social_user.extra_data.update(extra_data)
            else:
                social_user.extra_data = extra_data
            social_user.save()
        return {'social_user': social_user}
