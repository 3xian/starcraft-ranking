# -*- coding: utf-8 -*-

import logging
import os

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
from tornado.options import define, options

import base
import auth

define("local_host")
define("port", default=80, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', HomeHandler),
            (r'/auth', AuthHandler),
            #(r'/admin', AdminHandler),
            #(r'/admin/login', AdminLoginHandler),
            #(r'/login', LoginHandler),
            #(r'/logout', LogoutHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.getcwd(), 'templates'),
            static_path=os.path.join(os.getcwd(), 'static'),
            xsrf_cookies=False,
            cookie_secret="__WhatColorIsThat?!__",
            login_url="/login",
            debug=False,
            static_handler_class=base.SmartStaticFileHandler,
            weibo_api_key='277552994',
            weibo_api_secret='065159860517012fd61c4efd25ff89d6',
        )
        tornado.web.Application.__init__(self, handlers, **settings)

class HomeHandler(base.BaseHandler):
    def get(self):
        self.render('home.html')

class AuthHandler(base.BaseHandler, auth.WeiboMixin):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', None):
            user = yield self.get_authenticated_user(
                redirect_uri='/',
                client_id=self.settings['weibo_api_key'],
                client_secret=self.settings['weibo_api_secret'],
                code=self.get_argument('code'))
            self.redirect('/')

def main():
    tornado.options.parse_config_file('./kuke.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info('============ [ KuKe server START! ] ============')
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
