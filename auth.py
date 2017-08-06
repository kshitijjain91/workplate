from flask import url_for, redirect, request
from flask import current_app as app
from rauth import OAuth2Service

import json, bs4, requests
from bs4 import BeautifulSoup

def new_decoder(payload):
    return json.loads(payload.decode('utf-8'))

class OAuthSignIn():
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = app.config['OAUTH_CREDENTIALS'][provider_name]
        self.consumer_id = credentials['id']
        self.consumer_secret = credentials['secret']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('oauth_callback', provider=self.provider_name,
                        _external=True)

    @classmethod
    def get_provider(self, provider_name):
        if self.providers is None:
            self.providers = {}
            for provider_class in self.__subclasses__():
                provider = provider_class()
                self.providers[provider.provider_name] = provider
        return self.providers[provider_name]

class GoogleSignIn(OAuthSignIn):
    def __init__(self):
        super(GoogleSignIn, self).__init__('google')
        # googleinfo = urllib2.urlopen('https://accounts.google.com/.well-known/openid-configuration')
        # google_params = json.load(googleinfo)
        res=requests.get('https://accounts.google.com/.well-known/openid-configuration')
        google_params = BeautifulSoup(res.text, "html.parser")
        google_params = json.loads(google_params.text)
        self.service = OAuth2Service(
                name='google',
                client_id=self.consumer_id,
                client_secret=self.consumer_secret,
                authorize_url=google_params.get('authorization_endpoint'),
                base_url=google_params.get('userinfo_endpoint'),
                access_token_url=google_params.get('token_endpoint')
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope='email',
            response_type='code',
            redirect_uri=self.get_callback_url())
            )

    def callback(self):
        if 'code' not in request.args:
            return None, None, None
        oauth_session = self.service.get_auth_session(
                data={'code': request.args['code'],
                      'grant_type': 'authorization_code',
                      'redirect_uri': self.get_callback_url()
                     },
                decoder = new_decoder
        )
        me = oauth_session.get('').json()
        return (me['name'],
                me['email'])