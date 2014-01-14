__author__ = 'Simon Ruffle'

# code from http://www.informaticscentre.co.uk/news/view/26

import oauth2 as oauth

class OAuth():
    def __init__(self, consumerKey, consumerSecret):
        self.consumerKey = consumerKey
        self.consumerSecret = consumerSecret

    def Request(self, url, key, secret, http_method = "GET", post_body = '', http_headers = ''):
        consumer = oauth.Consumer(key = self.consumerKey, secret = self.consumerSecret)
        token = oauth.Token(key = key, secret = secret)
        client = oauth.Client(consumer, token)

        request = client.request(
            url,
            method = http_method,
            body = post_body,
            headers = http_headers)

        return request

