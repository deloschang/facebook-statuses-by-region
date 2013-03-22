from uuid import uuid4

from social_auth.utils import setting
from social_auth.models import UserSocialAuth
from social_auth.backends import USERNAME
from social_auth.signals import socialauth_registered, \
                                pre_update

# check dupe users
from webapp.models import UserProfile

# for private tracking
from datetime import datetime
import os
from django.conf import settings

def get_username(details, user=None,
                 user_exists=UserSocialAuth.simple_user_exists,
                 *args, **kwargs):
    """Return an username for new user. Return current user username
    if user was given.
    """
    if user:
        
        # login private tracking code 
        date = []
        date.append(str(datetime.now()))

        with open(os.path.join(settings.STATIC_ROOT, 'login_track.txt'), "a") as text_file:
            text_file.write(date[0]+'  FB      '+user.username+' logged in with '+user.email+'\n')

        return {'username': user.username}

    # uses FB username
    #if details.get(USERNAME):
        #username = unicode(details[USERNAME])
    #else:
        #username = uuid4().get_hex()

    # uses hyphenated first and last name
    final_username = details['first_name']+' '+details['last_name']

    #uuid_length = 16
    #max_length = UserSocialAuth.username_max_length()
    #short_username = username[:max_length - uuid_length]
    #final_username = UserSocialAuth.clean_username(username[:max_length])

    # Generate a unique username for current user using username
    # as base but adding a unique hash at the end. Original
    # username is cut to avoid any field max_length.

    #count_existing = UserProfile.objects.filter(url_username__iexact=short_username).count() # count existing url_username duplicates
    #if user_exists(username=final_username) or count_existing != 0:
        # original is 0. next is 1 (count is not 0-indexed) 
        #username = short_username + ' ' + str(count_existing) 
        #final_username = UserSocialAuth.clean_username(username[:max_length])


    return {'username': final_username}


def create_user(backend, details, response, uid, username, user=None, *args,
                **kwargs):
    """Create user. Depends on get_username pipeline."""
    if user:
        return {'user': user}
    if not username:
        return None

    return {
        'user': UserSocialAuth.create_user(username=username,
                                           email=details.get('email')),
        'is_new': True
    }


def update_user_details(backend, details, response, user=None, is_new=False,
                        *args, **kwargs):
    """Update user details using data from provider."""
    if user is None:
        return

    changed = False  # flag to track changes

    for name, value in details.iteritems():
        # do not update username, it was already generated
        # do not update configured fields if user already existed
        if name in (USERNAME, 'id', 'pk') or (not is_new and
            name in setting('SOCIAL_AUTH_PROTECTED_USER_FIELDS', [])):
            continue
        if value and value != getattr(user, name, None):
            setattr(user, name, value)
            changed = True

    # Fire a pre-update signal sending current backend instance,
    # user instance (created or retrieved from database), service
    # response and processed details.
    #
    # Also fire socialauth_registered signal for newly registered
    # users.
    #
    # Signal handlers must return True or False to signal instance
    # changes. Send method returns a list of tuples with receiver
    # and it's response.
    signal_response = lambda (receiver, response): response
    signal_kwargs = {'sender': backend.__class__, 'user': user,
                     'response': response, 'details': details}

    changed |= any(filter(signal_response, pre_update.send(**signal_kwargs)))

    # Fire socialauth_registered signal on new user registration
    if is_new:
        changed |= any(filter(signal_response,
                              socialauth_registered.send(**signal_kwargs)))

    if changed:
        user.save()
