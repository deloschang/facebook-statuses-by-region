# libraries
from django.shortcuts import render_to_response
from facepy import GraphAPI

def home(request):

    # test for successful login
    try: 
        access_token = request.user.social_auth.all().get(user=request.user, provider='facebook').extra_data['access_token']
        results = pull_facebook(access_token)

        #import pdb;
        #pdb.set_trace()

        return render_to_response('loggedin.html', {'results' : results})

    except AttributeError:
        # not logged in yet
        return render_to_response('main.html')

def pull_facebook(access_token):
    graph = GraphAPI(access_token)
    return graph.get('billy.peters.10?fields=id,name,statuses.fields(from,message,comments.fields(from,message))')


