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
    FB_DESIGNATED = 'billy.peters.10'

    graph = GraphAPI(access_token)

    # offset for pagination
    offset = 0

    full_data =  graph.get(FB_DESIGNATED+'/statuses?limit=100&offset='+str(offset))


    # initialize a unique corpus text file
    corpus = open("output/"+FB_DESIGNATED+".txt", 'w')

    # keep scraping until no more material
    total_counter = 0 
    total_comment_counter = 0
    while not not full_data['data']:

        data = full_data['data']

        #import pdb;
        #pdb.set_trace()



        # PARSE
        counter = 0 
        for status_update in data:
            # parse the status updates
            #import pdb;
            #pdb.set_trace()

            if 'message' in data[counter]:
                message = data[counter]['message']
                corpus.write(message.encode('utf-8') + "\n")


            # parse the comment messages
            comment_counter = 0 
            if 'comments' in data[counter]:
                for each_comment in data[counter]['comments']['data']:

                    # integrity check for chosen user
                    if data[counter]['comments']['data'][comment_counter]['from']['name'] == DESIGNATED:
                        corpus.write(data[counter]['comments']['data'][comment_counter]['message'].encode('utf-8') + "\n")

                    comment_counter += 1


            counter += 1


        print 'finished one loop. starting another..'

        # refresh
        offset += 100
        total_counter += counter
        total_comment_counter += comment_counter

        full_data = graph.get(FB_DESIGNATED+'/statuses?limit=100&offset='+str(offset))
    

    corpus.close()


    return 'Extracted '+str(total_counter)+' messages and '+str(total_comment_counter)+' comments.'

    #return data

