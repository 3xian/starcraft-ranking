# -*- coding: utf-8 -*-

import urllib
import logging

import tornado.auth
import tornado.escape
import tornado.httpclient
from tornado.auth import AuthError

class WeiboMixin(tornado.auth.OAuth2Mixin):
    _OAUTH_ACCESS_TOKEN_URL = 'https://api.weibo.com/oauth2/access_token'
    _OAUTH_AUTHORIZE_URL = 'https://api.weibo.com/oauth2/authorize?'

    @tornado.auth._auth_return_future
    def get_authenticated_user(self, redirect_uri, client_id, client_secret, 
                               code, callback, extra_fields=None, grant_type='authorization_code'):

        http = self.get_auth_http_client()
        args = {
            'redirect_uri': redirect_uri,
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': grant_type,
        }

        fields = set(['id', 'screen_name', 'profile_image_url'])
        if extra_fields:
            fields.update(extra_fields)

        http.fetch(self._OAUTH_ACCESS_TOKEN_URL,
                   method='POST',
                   body=urllib.urlencode(args),
                   callback=self.async_callback(self._on_access_token, redirect_uri, client_id, client_secret, callback, fields))

    def _on_access_token(self, redirect_uri, client_id, client_secret, future, fields, response):
        if response.error:
            future.set_exception(AuthError('Weibo auth error %s' % str(response)))
            return

        args = tornado.escape.json_decode(tornado.escape.native_str(response.body))
        session = {
            'access_token': args['access_token'],
            'expires': args['expires_in'],
            'uid': args['uid'],
        }

        self.weibo_request(
            url = 'https://api.weibo.com/2/users/show.json',
            callback=self.async_callback(self._on_get_user_info, future, session, fields),
            access_token=session['access_token'],
            uid=session['uid']
        )

    def _on_get_user_info(self, future, session, fields, user):
        if user is None:
            future.set_result(None)
            return

        fieldmap = {}
        for field in fields:
            fieldmap[field] = user.get(field)
        fieldmap.update({'access_token': session['access_token'], 'session_expires': session['expires']})
        future.set_result(fieldmap)

    @tornado.auth._auth_return_future
    def weibo_request(self, url, callback, access_token=None, uid=None, post_args=None, **args):
        all_args = {}
        if access_token:
            all_args['access_token'] = access_token
            if uid:
                all_args['uid'] = uid
                if args:
                    all_args.update(args)

        if all_args:
            url += '?' + urllib.urlencode(all_args)
            callback = self.async_callback(self._on_weibo_request, callback)
            http = self.get_auth_http_client()
            if post_args:
                http.fetch(url, method="POST", body=urllib.urlencode(post_args), callback=callback)
            else:
                http.fetch(url, callback=callback)

    def _on_weibo_request(self, future, response):
        if response.error:
            future.set_exception(AuthError('Error response %s fetching %s', response.error, response.request.url))
            return
        future.set_result(tornado.escape.json_decode(response.body))

    def get_auth_http_client(self):
        return tornado.httpclient.AsyncHTTPClient()
