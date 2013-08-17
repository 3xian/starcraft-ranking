# -*- coding: utf-8 -*-

import bson
import datetime
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
define('items_per_page', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', ThingsHandler),
            (r'/users/auth/weibo', AuthWeiboHandler),
            (r'/things', ThingsHandler),
            (r'/things/new', ThingsNewHandler),
            (r'/things/image-upload', ThingsImageUploadHandler),
            (r'/things/detail/(.*)', ThingsDetailHandler),
            (r'/users/messages', UsersMessagesHandler),
            (r'/users/logout', UsersLogoutHandler),
            (r'/test', TestHandler),
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

    def gen_things_image_url(self, things):
        for thing in things:
            if thing['image_ids']:
                image_id = thing['image_ids'][0]
                urls = self.image_urls([image_id])
                thing['image_url'] = urls[0]
            else:
                thing['image_url'] = 'http://www.baidu.com/img/bdlogo.gif'
        return things

    def get_things(self, sort_type, page):
        # offset = page * options.items_per_page
        things = list(self.db.things.find().sort('date', pymongo.DESCENDING))
        logging.info(things)
        things = self.gen_things_image_url(things)
        return things

    def get(self):
        user = self.get_current_user()
        sort_type = self.get_sort_type()
        page = self.get_argument('page', 0)
        things = self.get_things(sort_type, page)
        self.render('things.html',
                    sort_type=sort_type,
                    user=user,
                    things=things)

class ThingsNewHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render_extend('things_new.html')

    @tornado.web.authenticated
    def post(self):
        response = {
            'error': ''
        }

        try:
            title = self.get_argument('title')
            subtitle = self.get_argument('subtitle')
            buylink = self.get_argument('buylink')
            tags = self.get_list_argument('tags')
            price = self.get_argument('price')
            image_ids = self.get_list_argument('image_ids', bson.objectid.ObjectId)
            desc = self.get_argument('desc')

            thing_id = self.db.things.insert({
                'title': title,
                'subtitle': subtitle,
                'buylink': buylink,
                'tags': tags,
                'price': price,
                'image_ids': image_ids,
                'desc': desc,
                'visit': 0,
                'favor': 0,
                'date': datetime.datetime.utcnow(),
                'user': self.current_user['uid'],
                'auth': 0 
            })
            response['thing_id'] = str(thing_id)
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)

        response_json = tornado.escape.json_encode(response)
        self.write(response_json)

class ThingsImageUploadHandler(base.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        image = self.request.files['file'][0]
        ext = os.path.splitext(image['filename'])[1]
        image_id = self.db.images.insert({
            'user': self.current_user['uid'],
            'ext': ext,
            'date': datetime.datetime.utcnow()
        })
        if image_id:
            image_path = os.path.join(self.static_path('data'), str(image_id)+ext)
            with open(image_path, 'w') as fout:
                fout.write(image['body'])
            self.write(str(image_id))
        else:
            pass # TODO

class ThingsDetailHandler(base.BaseHandler):
    def get(self, thing_id):
        self.write(thing_id)

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
            self.db.users.update({
                'uid': uid
            }, {
                'uid': uid,
                'name': login_info['screen_name'],
                'img_url': login_info['profile_image_url']
            }, upsert=True)
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
