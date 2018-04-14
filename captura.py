import sys
import tweepy
import requests
import codecs
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json

cred = credentials.Certificate("./firekey.json")

#llaves del API Twitter
consumer_key = '59cgFGdx36FjvhTwkTVf7GNeX'
consumer_secret = 'Dyd2oRd0MRulImiMOPfNQ4rdAi1XZRarZPd3WXnkARk2fTwmsM'
access_token = '741729530478354432-nJXxuhF66sa0TGIODDT5vHtwAC0RD8p'
access_secret = '4duZZ2wM4ThBYpnqwlkbhJBCwommpxAilCSDuLa2aYtNW'

# Add a new document
# Use the application default credentials
# Use a service account
firebase_admin.initialize_app(cred)
db = firestore.client()

#Read user preferences
dbpreferences = db.collection(u'userpreferences').get()
userpreferences = {}
for dbpreference in dbpreferences:
    print dbpreference.to_dict()
    userpreferences[dbpreference.to_dict()['key']] = dbpreference.to_dict()['value']

#Default preferences - User
min_followers_count = 10
min_friends_count = 10
#Default preferences - Tweet
min_retweet_count = 2000
min_reply_count = 200
min_quote_count = 100
min_favorite_count = 1000
#keyword
keyword = "" 

if(userpreferences.has_key('min_retweet_count')):
    min_retweet_count = userpreferences['min_retweet_count']
if(userpreferences.has_key('min_reply_count')):
    min_reply_count = userpreferences['min_reply_count']
if(userpreferences.has_key('min_quote_count')):
    min_quote_count = userpreferences['min_quote_count']
if(userpreferences.has_key('min_favorite_count')):
    min_favorite_count = userpreferences['min_favorite_count']
if(userpreferences.has_key('keyword')):
    keyword = userpreferences['keyword']


class MyStreamListener(tweepy.StreamListener): #Extender la clase streamListener
    
    def on_connect(self):
        # Called initially to connect to the Streaming API
        print("You are now connected to the streaming API.")
 
    def on_status(self, status):#Procesar nuevos tweets
        tweet = {"type": u"tweet", "polarity": u""}
        tweet['description'] = status.text[3::]
        if hasattr(status, 'retweeted_status'):
            tweet['tweet_id'] = unicode(status.retweeted_status.id)
            tweet['tweet_screen_name'] = status.retweeted_status.user.screen_name
            tweet['publishedAt'] = status.retweeted_status.created_at
            tweet['location'] = status.retweeted_status.user.location
            tweet['keyword'] = keyword
            if(hasattr(status, 'quote_count')):
                tweet['quote_count'] = status.retweeted_status.quote_count
            if(hasattr(status, 'reply_count')):
                tweet['reply_count'] = status.retweeted_status.reply_count 
            if(hasattr(status, 'favorite_count')):
                tweet['favorite_count'] = status.retweeted_status.favorite_count
            if(hasattr(status, 'retweet_count')):
                tweet['retweet_count'] = status.retweeted_status.retweet_count 

            #Filter tweets
            if( tweet['retweet_count'] >= min_retweet_count and tweet['favorite_count'] >= min_favorite_count and tweet['reply_count'] >= min_reply_count and tweet['quote_count'] >= min_quote_count):    
                try:                
                    results = db.collection(u'posts').where(u'tweet_id', u'==', tweet['tweet_id']).get()                
                    #resultsit = itertools.tee(results)
                    if (sum(1 for x in results) == 0):
                        print "new"
                        doc_ref = db.collection(u'posts').document()
                        doc_ref.set(tweet)
                    else:
                        print "update"
                        results = db.collection(u'posts').where(u'tweet_id', u'==', status.retweeted_status.id).get()
                        for result in results:   
                            result.reference.update({
                                u"quote_count":status.retweeted_status.quote_count,
                                u"reply_count":status.retweeted_status.reply_count,
                                u"favorite_count":status.retweeted_status.favorite_count,
                                u"retweet_count":status.retweeted_status.retweet_count
                            })
                except Exception:
                    print "err"
                #print tweet
                
        """
        doc_ref = db.collection(u'post').document()
        doc_ref.set({
            'text': status.text,
            'id': status.
        })
        """
        #print status
        #if not hasattr(status, 'retweeted_status'):#Ignorar retweets
        #    print status.text.encode('utf-8')#Codificar en UTF-8 el mensaje antes de imprimirlo
            
    def on_error(self, status_code): 
        if status_code == 420:
            print "Numero de intentos excesivos de conectarse al streaming API, esperar y ejecutar de nuevo..."
        elif status_code == 401:#
            print "Credenciales de API incorrectas."
        else:
            print "Ocurrio un error "+str(status_code)
        return False #Seguir la ejecucion. True cancelaria la ejecucion del programa

    def on_timeout(self):
        print "Timeout..."
        return False #Seguir la ejecucion. True cancelaria la ejecucion del programa

if(len(keyword) == 0 and userpreferences.has_key('keyword')):
    keyword = userpreferences['keyword']

tauth = tweepy.OAuthHandler(consumer_key, consumer_secret)#Autenticar
tauth.set_access_token(access_token, access_secret)#Autenticar

streamListen = MyStreamListener()#Instanciar clase "MyStreamListener"
twStream = tweepy.Stream(auth = tauth, listener = streamListen )#Crear stream

twStream.filter(track=[keyword], async=False)#Especificar filtro & Iniciar Stream

