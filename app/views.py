# libraries
from django.shortcuts import render_to_response
from facepy import GraphAPI
#import json
from django.utils import simplejson

from app.models import Statuses

import random

SKIP_CREATION = False

def home(request):

    # test for successful login
    try: 
        access_token = request.user.social_auth.all().get(user=request.user, provider='facebook').extra_data['access_token']

        # pull the data from facebook
        if SKIP_CREATION == True:
            data_amount = '' #dummy
        else: 
            data_amount = pull_facebook(access_token)

        # generate the markov chain
        #markov = markov_chain()

        # construct result
        #result = "..."+construct_markov(markov_chain = markov, word_count=250)+"..."

        return render_to_response('loggedin.html', {'data_amount' : data_amount})

    except AttributeError:
        # not logged in yet
        return render_to_response('main.html')


def pull_facebook(access_token):

    graph = GraphAPI(access_token)

##### GET LIST OF FRIENDS####
    # Haven't implemented checks for after 5000 friends...
    friend_data = graph.get('me/friends?fields=name,hometown')

# ONLY SCRAPE IF HOMETOWN AND STATUSES ARE AVAILABLE#
    for person in friend_data['data']:
        test_id = person['id']

        if 'hometown' in person:
            hometown_obj = person['hometown']
            hometown_id = hometown_obj['id']
            hometown_name = hometown_obj['name']

            offset = 0
            # offset for pagination
            full_data =  graph.get(test_id+'/statuses?limit=100&offset='+str(offset))

            # Found statuses
            if full_data['data']:
                ## keep scraping until no more material
                total_counter = 0 
                #total_comment_counter = 0
                while full_data['data']:
                    data = full_data['data']

                    # PARSE
                    counter = 0 
                    for status_update in data:
                        # parse the status updates

                        if 'message' in data[counter]:
                            message = data[counter]['message']
                            #print message

                            # save hometown and message
                            # Save into database 
                            unit = Statuses(message=message, hometown_name=hometown_name,
                                    hometown_id=hometown_id)
                            unit.save()

                        # parse the comment messages
                        #comment_counter = 0 
                        #if 'comments' in data[counter]:
                            #for each_comment in data[counter]['comments']['data']:

                                ## integrity check for chosen user
                                #if data[counter]['comments']['data'][comment_counter]['from']['name'] == DESIGNATED:
                                    ##
                                    #corpus.write(data[counter]['comments']['data'][comment_counter]['message'].encode('utf-8') + "\n")

                                #comment_counter += 1


                        counter += 1


                    print('finished one loop. starting another..')

                    # refresh
                    offset += 100
                    total_counter += counter
                    #total_comment_counter += comment_counter

                    full_data = graph.get(test_id+'/statuses?limit=100&offset='+str(offset))

    return 'Extracted '+str(total_counter)+' statuses'


     
