# libraries
from django.shortcuts import render_to_response
from facepy import GraphAPI

def home(request):
    # Check if publish_stream permissions are set
    #social_user = request.user.social_auth.all().get(user=request.user, provider = 'facebook')
    #access_token = social_user.extra_data['access_token']

    # test for successful login
    try:
        if 'access_token' in request.user.social_auth.all().get(user=request.user, provider='facebook').extra_data:
            return render_to_response('loggedin.html')

    # not logged in yet
    except:
        return render_to_response('main.html')

