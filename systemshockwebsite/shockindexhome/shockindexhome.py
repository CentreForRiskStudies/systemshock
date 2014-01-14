__author__ = 'Simon Ruffle'

from weblib.baseclasses.pagebase import Pagebase
from django.shortcuts import render
from twitter import *

template_name = "shockindexhome/templates/shockindexhome.html"

consumerKey = 'XbCWGfms9wHAsYejzClBw'
consumerSecret = 'Tgn5RLVxY3XFv7an47o7M0RHxt2l1nBfmChobEVgzUo'
apiKey = '1953499994-YvabSKj3EPi4tCMf7iGoxIesLaVm2REqNBSiHI7'
apiSecret = 'KAD9DeVxapgbtyAvmEOFlg29goBbFMDwctaiHZbcw'

# use OR and AND to make search clause
searchclause = '#cybersecurity'

class BasicPage (Pagebase):

    def dispatch(self, request, *args, **kwargs):
        self.preProcessPage(request, **kwargs)

        self.page_context['page_title'] = 'Cambridge Shock Index: Cyber Threat'
        self.page_context['page_subtitle'] = 'Twitter Feed ' + searchclause

        if request.method == 'GET':

            # initialise twitter connection
            twitter = Twitter(consumerKey, consumerSecret, apiKey, apiSecret)

            #tweets = twitter.GetTweetsFromUnblockedUsers('#testingriskcentre', 20)   # search for hashtag - limited to past 7 days?
            tweets = twitter.GetTweetsFromUnblockedUsers(searchclause, 20)   # search for keywords - limited to past 7 days?
            #tweets = twitter.GetUserTweets('Risk_Cambridge', 20)                      # from specific user - goes way back

            self.page_context['tweet_table'] = '<table class="tweettable">'

            for index, post in enumerate(tweets):
                  self.page_context['tweet_table'] += '<tr><td>' + post.author + '</td><td>' + post.postedOn + '</td><td>' + post.location + '</td><td>' + post.text + '</td></tr>'

            self.page_context['tweet_table'] += '</table>'

            return render(request, template_name, self.page_context)