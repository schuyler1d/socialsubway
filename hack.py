import settings

import tweepy
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream

import json
import os
import requests
import shutil


auth = tweepy.OAuthHandler(settings.consumer_key, settings.consumer_secret)
auth.secure = True
auth.set_access_token(settings.access_token, settings.access_token_secret)

api = tweepy.API(auth)

#print(api.me().name) #needs access_tokens
print(api.rate_limit_status())


class CsvFile:
    def __init__(self, imgdir, csvfile):
        self.imgdir = imgdir
        self.csvfile = csvfile

        
    def save_data(self, img_url, tweet_id, user_id, text=None):
        ext = img_url.rsplit('.', 1)[1]
        if ext not in ('jpg', 'png', 'jpeg'):
            return
        path = os.path.join(self.imgdir, '%s.%s' % (user_id, ext))
        with open(self.csvfile, 'a') as ff:
            ff.write(
                "%s,%s,%s,%s\n" % (tweet_id, user_id, img_url, str(text))
            )
            
        r = requests.get(img_url, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)

#a = api.search(q='#DoYourJob filter:safe', rpp=100)

def get_past_tweets():
    least_tweet = None
    all_queries = []
    bunch = []
    all_ids = set()
    for x in range(100):
        a = list(api.search(q='#DoYourJob filter:safe', rpp=100, max_id=least_tweet))
        all_queries.append(a)
        ids = [int(x.id_str) for x in a]
        bunch.append(ids)
        all_ids.update(ids)
        mintw = min(all_ids)
        if least_tweet == mintw:
            print('same tweet!', mintw)
            break
        least_tweet = mintw
    return all_ids
#import pdb; pdb.set_trace()
#page=1..15 (1500 results max)
#since_id, max_id, 
#include_entities=False

ccc = CsvFile('images2/', 'downloads.csv')

#for x in range(100):

class StdOutListener(StreamListener):
    def on_data(self, data):
        dd = json.loads(data)
        #print(dd.keys())
        print(dd.get('user',{}).keys())
        print(dd.get('user',{}).get('profile_image_url'))
        print(dd.get('text'))
        ccc.save_data(
            dd.get('user',{}).get('profile_image_url'),
            dd.get('id_str',''),
            dd.get('user',{}).get('id'),
            dd.get('text',''))
        return True

    def on_error(self, status):
        print(status)

stdout = StdOutListener()

stream = Stream(auth, stdout)
#stream.filter(track=['#BernieOrBust'])
stream.filter(track=['#FeelTheBern'])

#os.listdir('./')
