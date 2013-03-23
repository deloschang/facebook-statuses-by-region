# libraries
from django.shortcuts import render_to_response
from facepy import GraphAPI
#import json
from django.utils import simplejson

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
    DESIGNATED = "Billy Peters"

    graph = GraphAPI(access_token)
    full_data =  graph.get('billy.peters.10?fields=id,name,statuses.fields(from,message,comments.fields(from,message))')

    data = full_data['statuses']['data']

    #import pdb;
    #pdb.set_trace()


    # PARSE
    counter = 0 
    for status_update in data:
        # parse the status updates
        #print data['statuses']['data'][counter]['message']


        # parse the comment messages
        comment_counter = 0 
        if 'comments' in data[counter]:
            for each_comment in data[counter]['comments']['data']:

                # integrity check for chosen user
                if data[counter]['comments']['data'][comment_counter]['from']['name'] == DESIGNATED:
                    print data[counter]['comments']['data'][comment_counter]['message']

                comment_counter += 1


        counter += 1

        # parse comment material too

    # add into a corpus


    #return data

