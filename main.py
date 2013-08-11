# -*- coding: utf-8 -*-

import logging
import os

import pymongo
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
from tornado.options import define, options

import base
import auth

define('host')
define('port', default=80, type=int)
define('domain')
define('weibo_api_key')
define('weibo_api_secret')

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            ('/', ThingsHandler),
            ('/users/auth/weibo', AuthWeiboHandler),
            ('/things', ThingsHandler),
            ('/things/new', ThingsNewHandler),
            ('/users/messages', UsersMessagesHandler),
            ('/users/logout', UsersLogoutHandler),
            ('/test', TestHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.getcwd(), 'templates'),
            static_path=os.path.join(os.getcwd(), 'static'),
            xsrf_cookies=False,
            cookie_secret='__WhatColorIsThat?!__',
            login_url='/',
            debug=False,
            static_handler_class=base.SmartStaticFileHandler,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = pymongo.MongoClient().kuke

class ThingsHandler(base.BaseHandler):
    def get_sort_type(self):
        sort_type = self.get_argument('sort', 'None')
        sort_types = ['time', 'hot', 'favor']
        if sort_type not in sort_types:
            sort_type = 'time'
        return sort_type

    def get(self):
        user = self.get_current_user()
        self.render('things.html',
                    sort_type=self.get_sort_type(),
                    user=user)

class ThingsNewHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('things_new.html',
                    user=self.current_user)

class AuthWeiboHandler(base.BaseHandler, auth.WeiboMixin):
    @tornado.web.asynchronous
    def get(self):
        return_code = self.get_argument('code', None)
        redirect_uri = '%s/users/auth/weibo' % options.domain
        if return_code:
            logging.info('weibo auth code: %s', return_code)
            self.get_authenticated_user(redirect_uri=redirect_uri,
                                        client_id=options.weibo_api_key,
                                        client_secret=options.weibo_api_secret,
                                        code=return_code,
                                        callback=self._on_login)
        else:
            self.authorize_redirect(redirect_uri=redirect_uri,
                                    client_id=options.weibo_api_key)

    def _on_login(self, login_info):
        if login_info:
            logging.info('login success: %s', login_info)
            uid = 'weibo$%d' % login_info['id']
            self.db.users.update({'uid':uid},
                                 {'uid':uid, 'name':login_info['screen_name'], 'img_url':login_info['profile_image_url']},
                                 True)
            self.set_secure_cookie('uid', uid)
        else:
            logging.warning('login failed')
        self.redirect('/')

class UsersMessagesHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        # TODO
        self.redirect('/')

class UsersLogoutHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie('uid')
        self.redirect('/')

class TestHandler(base.BaseHandler):
    def get(self):
        self.render('test.html')

def main():
    tornado.options.parse_config_file('./kuke.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info('============ [ KuKe server START! ] ============')
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
