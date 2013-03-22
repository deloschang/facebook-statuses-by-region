"""Views

Notes:
    * Some views are marked to avoid csrf tocken check because they rely
      on third party providers that (if using POST) won't be sending csrf
      token back.
"""
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from social_auth.utils import sanitize_redirect, setting, \
                              backend_setting, clean_partial_pipeline
from social_auth.decorators import dsa_view
from invitation.models import InvitationKeyManager, InvitationKey


# for private tracking
from datetime import datetime
import os
from django.conf import settings



DEFAULT_REDIRECT = setting('SOCIAL_AUTH_LOGIN_REDIRECT_URL',
                           setting('LOGIN_REDIRECT_URL'))
LOGIN_ERROR_URL = setting('LOGIN_ERROR_URL', setting('LOGIN_URL'))
PIPELINE_KEY = setting('SOCIAL_AUTH_PARTIAL_PIPELINE_KEY', 'partial_pipeline')


@dsa_view(setting('SOCIAL_AUTH_COMPLETE_URL_NAME', 'socialauth_complete'))
def auth(request, backend):
    """Start authentication process"""
    return auth_process(request, backend)


@csrf_exempt
@dsa_view()
def complete(request, backend, *args, **kwargs):
    """Authentication complete view, override this view if transaction
    management doesn't suit your needs."""


    if request.user.is_authenticated():
        social_user = request.user.social_auth.all().get(user=request.user, provider = 'facebook')

        #### INVITATION TO RETURNING USER ####
        # Everytime, you log in, check if somebody has invited you to their album!
        # Check if the user has been invited. If so, link albums
        try:
            invitations = InvitationKey.objects.filter(key=social_user.uid)
            #invitee_obj = InvitationKey.objects.get(key='641286114')

            for invitee_obj in invitations:
                invitee_obj.from_user_album.creator.add(request.user) # add user to the album then
                invitee_obj.delete() #cleanup
        except:
            pass

        # if session exists, user is inviting FB friends
        # try checking for session 
        # session comes from helloworld_create, views.py
        try: 
            if social_user.provider == 'facebook' and request.session['friend_inv_exist'] == True:
                try:
                    from facepy import GraphAPI

                    #import pdb; pdb.set_trace()
                    access_token = social_user.extra_data['access_token']

                    # change in webapp_from_album_invite as well
                    graph = GraphAPI(access_token)
                    message = 'Hey '+request.session['friend_name']+'. I invited you to our private album: '+\
                            request.session['first_friend_experience'].title+' on Memeja. -'+request.user.username

                    picture = 'http://www.memeja.com/static/images/intro_logo.gif'
                    link = 'http://memeja.com/login/facebook'
                    name = 'See it here'

                    graph.post(path=request.session['friend_id']+"/feed", retry=1, message=message, picture=picture, link=link, name=name)

                    with open(os.path.join(settings.STATIC_ROOT, 'registration_track.txt'), "a") as text_file:
                        text_file.write('   **'+request.user.username+' invited '+request.session['friend_name']+'\n')

                    # Invitation 
                    invite = InvitationKey.objects.create_invitation(request.user, request.session['first_friend_experience'])
                    invite.key = request.session['friend_id'] # replace key with uid of INVITED user
                    invite.save()

                    # first time invite.
                    # add in a message for user to know invitation completed
                    messages.add_message(request, messages.INFO, 'Success!', extra_tags="text-success")

                    del request.session['first_friend_experience']
                    del request.session['friend_id']
                    del request.session['friend_inv_exist']
                    del request.session['friend_name']

                except:
                    return associate_complete(request, backend, *args, **kwargs)
        except:
            return associate_complete(request, backend, *args, **kwargs)



        return associate_complete(request, backend, *args, **kwargs)
    else:
        return complete_process(request, backend, *args, **kwargs)


@login_required
def associate_complete(request, backend, *args, **kwargs):
    """Authentication complete process"""
    # pop redirect value before the session is trashed on login()
    redirect_value = request.session.get(REDIRECT_FIELD_NAME, '')
    user = auth_complete(request, backend, request.user, *args, **kwargs)

    if not user:
        url = backend_setting(backend, 'LOGIN_ERROR_URL', LOGIN_ERROR_URL)
    elif isinstance(user, HttpResponse):
        return user
    else:
        url = redirect_value or \
              backend_setting(backend,
                              'SOCIAL_AUTH_NEW_ASSOCIATION_REDIRECT_URL') or \
              DEFAULT_REDIRECT

    

    return HttpResponseRedirect(url)


@login_required
@dsa_view()
def disconnect(request, backend, association_id=None):
    """Disconnects given backend from current logged in user."""
    backend.disconnect(request.user, association_id)
    url = request.REQUEST.get(REDIRECT_FIELD_NAME, '') or \
          backend_setting(backend, 'SOCIAL_AUTH_DISCONNECT_REDIRECT_URL') or \
          DEFAULT_REDIRECT
    return HttpResponseRedirect(url)


def auth_process(request, backend):
    """Authenticate using social backend"""
    # Save any defined next value into session
    #import pdb; pdb.set_trace()
    data = request.POST if request.method == 'POST' else request.GET
    if REDIRECT_FIELD_NAME in data:
        # Check and sanitize a user-defined GET/POST next field value
        redirect = data[REDIRECT_FIELD_NAME]
        if setting('SOCIAL_AUTH_SANITIZE_REDIRECTS', True):
            redirect = sanitize_redirect(request.get_host(), redirect)
        request.session[REDIRECT_FIELD_NAME] = redirect or DEFAULT_REDIRECT

    # Clean any partial pipeline info before starting the process
    clean_partial_pipeline(request)

    if backend.uses_redirect:
        return HttpResponseRedirect(backend.auth_url())
    else:
        return HttpResponse(backend.auth_html(),
                            content_type='text/html;charset=UTF-8')


def complete_process(request, backend, *args, **kwargs):
    """Authentication complete process"""
    # pop redirect value before the session is trashed on login()
    redirect_value = request.session.get(REDIRECT_FIELD_NAME, '')
    user = auth_complete(request, backend, *args, **kwargs)

    if isinstance(user, HttpResponse):
        return user

    if not user and request.user.is_authenticated():
        return HttpResponseRedirect(redirect_value)

    msg = None
    if user:
        if getattr(user, 'is_active', True):
            # catch is_new flag before login() might reset the instance
            is_new = getattr(user, 'is_new', False)
            login(request, user)
            # user.social_user is the used UserSocialAuth instance defined
            # in authenticate process
            social_user = user.social_user
            if redirect_value:
                request.session[REDIRECT_FIELD_NAME] = redirect_value or \
                                                       DEFAULT_REDIRECT

            if setting('SOCIAL_AUTH_SESSION_EXPIRATION', True):
                # Set session expiration date if present and not disabled by
                # setting. Use last social-auth instance for current provider,
                # users can associate several accounts with a same provider.
                expiration = social_user.expiration_datetime()
                if expiration:
                    try:
                        request.session.set_expiry(expiration)
                    except OverflowError:
                        # Handle django time zone overflow, set default expiry.
                        request.session.set_expiry(None)

            # store last login backend name in session
            key = setting('SOCIAL_AUTH_LAST_LOGIN',
                          'social_auth_last_login_backend')
            request.session[key] = social_user.provider

            # Remove possible redirect URL from session, if this is a new
            # account, send him to the new-users-page if defined.
            new_user_redirect = backend_setting(backend,
                                           'SOCIAL_AUTH_NEW_USER_REDIRECT_URL')
            if new_user_redirect and is_new:
                url = new_user_redirect
            else:
                url = redirect_value or \
                      backend_setting(backend,
                                      'SOCIAL_AUTH_LOGIN_REDIRECT_URL') or \
                      DEFAULT_REDIRECT
        else:
            msg = setting('SOCIAL_AUTH_INACTIVE_USER_MESSAGE', None)
            url = backend_setting(backend, 'SOCIAL_AUTH_INACTIVE_USER_URL',
                                  LOGIN_ERROR_URL)
    else:
        msg = setting('LOGIN_ERROR_MESSAGE', None)
        url = backend_setting(backend, 'LOGIN_ERROR_URL', LOGIN_ERROR_URL) # set to '/'
    if msg:
        messages.error(request, msg)


    #### INVITATION TO NEW USER ####
    # Check if the user has been invited. If so, link albums
    try:
        #pass
        invitations = InvitationKey.objects.filter(key=social_user.uid)
        #invitee_obj = InvitationKey.objects.get(key='641286114')

        for invitee_obj in invitations:
            invitee_obj.from_user_album.creator.add(request.user) # add user to the album then
    except:
        pass

    return HttpResponseRedirect(url)


def auth_complete(request, backend, user=None, *args, **kwargs):
    """Complete auth process. Return authenticated user or None."""
    if user and not user.is_authenticated():
        user = None

    if request.session.get(PIPELINE_KEY):
        data = request.session.pop(PIPELINE_KEY)
        idx, xargs, xkwargs = backend.from_session_dict(data, user=user,
                                                        request=request,
                                                        *args, **kwargs)
        if 'backend' in xkwargs and \
           xkwargs['backend'].name == backend.AUTH_BACKEND.name:
            return backend.continue_pipeline(pipeline_index=idx,
                                             *xargs, **xkwargs)
    return backend.auth_complete(user=user, request=request, *args, **kwargs)
