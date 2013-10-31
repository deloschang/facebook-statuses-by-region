# libraries
from django.shortcuts import render_to_response
from facepy import GraphAPI
#import json
from django.utils import simplejson

import random

SKIP_CREATION = True
FB_DESIGNATED = 'billy.peters.10'
DESIGNATED = 'Billy Peters'  

def markov_chain():
    #file_paths = "/Users/deloschang/Documents/self_projects/markovbilly/output/"+FB_DESIGNATED+".txt"

    markov_chain = {}
    word1 = "\n"
    word2 = "\n"

    file = open(file_paths)

    print "Reading lines..."

    for line in file:
        for current_word in line.split():
            if current_word != "":
                markov_chain.setdefault((word1, word2), []).append(current_word)
                word1 = word2
                word2 = current_word
    return markov_chain
 
def construct_markov(markov_chain, word_count):

    print "Constructing..."

    generated_sentence = ""
    word_tuple = random.choice(markov_chain.keys())
    w1 = word_tuple[0]
    w2 = word_tuple[1]
    
    for i in xrange(word_count):
        newword = random.choice(markov_chain[(w1, w2)])
        generated_sentence = generated_sentence + " " + newword
        w1 = w2
        w2 = newword
        
    return generated_sentence

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
        markov = markov_chain()

        # construct result
        result = "..."+construct_markov(markov_chain = markov, word_count=250)+"..."

        return render_to_response('loggedin.html', {'data_amount' : data_amount, 'result' : result, 'name' : DESIGNATED })

    except AttributeError:
        # not logged in yet
        return render_to_response('main.html')

def pull_facebook(access_token):

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

        # PARSE
        counter = 0 
        for status_update in data:
            # parse the status updates

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


    # return trivia
    return 'Extracted '+str(total_counter)+' statuses and '+str(total_comment_counter)+' comments.'


 
