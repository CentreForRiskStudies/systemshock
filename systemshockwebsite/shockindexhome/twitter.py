__author__ = 'Simon Ruffle'

# code from http://www.informaticscentre.co.uk/news/view/26

from oauth import *
from post import *
import json
import urllib

class Twitter():
    def __init__(self, consumerKey, consumerSecret, apiKey, apiSecret):
        self.consumerKey = consumerKey
        self.consumerSecret = consumerSecret
        self.apiKey = apiKey
        self.apiSecret = apiSecret

        self.InitialiseOAuth(self.consumerKey, self.consumerSecret)

    def InitialiseOAuth(self, consumerKey, consumerSecret):
        self.oauth = OAuth(consumerKey, consumerSecret)

    def GetTweetsFromUnblockedUsers(self, query, count):
        blockedUsers = self.GetBlockedUsers()
        tweets = self.GetTweets(query, count)

        unblockedTweets = list()

        for tweet in tweets:
            if tweet.author not in blockedUsers:
                unblockedTweets.append(tweet)

        return unblockedTweets

    def GetBlockedUsers(self):
        users = list()

        request, response = self.oauth.Request(
            'https://api.twitter.com/1.1/blocks/list.json?skip_status=true&cursor=-1',
            self.apiKey,
            self.apiSecret)

        data = json.loads(response)

        if 'users' in data:
            for user in data['users']:
                users.append(unicode.lower(user['screen_name']));

        return users

    def GetTweets(self, query, count):
        posts = list()
        encodedQuery = urllib.quote_plus(query)

        # documentation for this request is at https://dev.twitter.com/docs/api/1.1/get/search/tweets

        request, response = self.oauth.Request(
            'https://api.twitter.com/1.1/search/tweets.json?q=' + encodedQuery + '&since_id=319302347434127360&result_type=mixed&count=' + str(count),
            self.apiKey,
            self.apiSecret)

        data = json.loads(response)

        for post in data['statuses']:
            posts.append(Post(post['text'], post['created_at'], unicode.lower(post['user']['screen_name']), unicode(post['user']['location'])))

        return posts


    def GetUserTweets(self, screenname, count):
        posts = list()

        # documentation for this request is at https://dev.twitter.com/docs/api/1.1/get/statuses/user_timeline

        request, response = self.oauth.Request(
            'https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=' + screenname + '&count=' + str(count),
            self.apiKey,
            self.apiSecret)

        data = json.loads(response)

        for post in data:
            posts.append(Post(post['text'], post['created_at'], unicode.lower(post['user']['screen_name']), unicode(post['user']['location'])))

        return posts