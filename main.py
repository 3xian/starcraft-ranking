# -*- coding: utf-8 -*-

import bson.objectid
import datetime
import logging
import os
import re
import StringIO
from bson.objectid import ObjectId

import pymongo
import qrcode
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
from tornado.options import define, options
from tornado.escape import json_encode

import base
import auth

define('host')
define('port', default=80, type=int)
define('domain')
define('weibo_api_key')
define('weibo_api_secret')
define('items_per_page', type=int)
define('debug', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', ThingsHandler),
            (r'/users/auth/weibo', AuthWeiboHandler),
            (r'/things', ThingsHandler),
            (r'/things/collection', ThingsCollectionHandler),
            (r'/things/find', ThingsFindHandler),
            (r'/things/new', ThingsNewHandler),
            (r'/things/update', ThingsUpdateHandler),
            (r'/things/update/(.*)', ThingsUpdateHandler),
            (r'/things/collect', ThingsCollectHandler),
            (r'/things/favor', ThingsFavorHandler),
            (r'/things/image-upload', ThingsImageUploadHandler),
            (r'/things/detail/(.*)', ThingsDetailHandler),
            (r'/things/qrcode', ThingsQrcodeHandler),
            (r'/things/remove', ThingsRemoveHandler),
            (r'/things/permit', ThingsPermitHandler),
            (r'/things/comments/new', ThingsCommentsNewHandler),
            (r'/users/messages', UsersMessagesHandler),
            (r'/users/logout', UsersLogoutHandler),
            (r'/users/profile/(.*)', UsersProfileHandler),
            (r'/admin/things', AdminThingsHandler),
            (r'/test', TestHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.getcwd(), 'templates'),
            static_path=os.path.join(os.getcwd(), 'static'),
            xsrf_cookies=False,
            cookie_secret='__WhatColorIsThat?!__',
            login_url='/',
            debug=(options.debug != 0),
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

    def get_things(self, sort_type, offset):
        if sort_type == 'hot':
            sort_key = 'visit'
        elif sort_type == 'favor':
            sort_key = 'favor'
        else:
            sort_key = 'date'

        things = list(self.db.things.find({'auth': 1}).sort(sort_key, pymongo.DESCENDING).\
                      skip(offset).limit(options.items_per_page))
        things = self.gen_things_image_url(things)
        return things

    def get(self):
        sort_type = self.get_sort_type()
        offset = int(self.get_argument('offset', 0))
        things = self.get_things(sort_type, offset)
        self.render_extend('things.html',
                           sort_type=sort_type,
                           things=things,
                           title='酷客')

    def post(self):
        user = self.get_current_user()
        sort_type = self.get_sort_type()
        offset = int(self.get_argument('offset', 0))
        logging.info('%s:%s', sort_type, str(offset))
        things = self.get_things(sort_type, offset)
        for thing in things:
            thing['_id'] = str(thing['_id'])
            del thing['image_ids']
            del thing['date']

        result = { 'error': '', 'things': things }
        response_json = json_encode(result)
        self.write(response_json)

class ThingsCollectionHandler(base.BaseHandler):
    def get_things(self, page):
        tids = self.db.users.find_one({'_id': self.current_user['_id']})['collect']
        things = list(self.db.things.find({'_id': {'$in': tids}}).sort('date', pymongo.DESCENDING))
        things = self.gen_things_image_url(things)
        return things

    @tornado.web.authenticated
    def get(self):
        user = self.get_current_user()
        page = self.get_argument('page', 0)
        things = self.get_things(page)
        self.render_extend('things.html',
                           things=things,
                           title="收藏 - 酷客")

class ThingsFindHandler(base.BaseHandler):
    def get_things_by_tag(self, tag, page=0):
        things = list(self.db.things.find({'auth': 1, 'tags':tag}).sort('date', pymongo.DESCENDING))
        things = self.gen_things_image_url(things)
        return things

    def get_things_by_search(self, query, offset=0):
        regx = re.compile('.*%s.*'%query, re.IGNORECASE)
        things = list(self.db.things.find({'$or': [
            {'title': regx, 'auth': 1},
            {'tags': regx, 'auth': 1}
        ]}).sort('date', pymongo.DESCENDING))
        things = self.gen_things_image_url(things)
        return things

    def get(self):
        tag = self.get_argument('tag', None)
        if tag:
            things = self.get_things_by_tag(tag)
            title = '【%s】 - 酷客' % tag.encode('utf8')
            subtitle = '标签：%s' % tag.encode('utf8')
        else:
            query = self.get_argument('q')
            things = self.get_things_by_search(query)
            title = '【%s】 - 酷客' % query.encode('utf8')
            subtitle = '搜索：%s' % query.encode('utf8')

        self.render_extend('things.html',
                           things=things,
                           title=title,
                           subtitle=subtitle)

class ThingsNewHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render_extend('things_new.html')

    @tornado.web.authenticated
    def post(self):
        response = {'error': ''}
        try:
            title = self.get_argument('title')
            subtitle = self.get_argument('subtitle')
            buylink = self.get_argument('buylink')
            tags = self.get_list_argument('tags')
            price = self.get_argument('price')
            image_ids = self.get_list_argument('image_ids', ObjectId)
            desc = self.get_argument('desc')
            tid = self.db.things.insert({
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
            response['tid'] = str(tid)
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)

        response_json = json_encode(response)
        self.write(response_json)

class ThingsUpdateHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self, tid):
        thing = self.db.things.find_one({'_id': ObjectId(tid)})
        if not thing:
            raise tornado.web.HTTPError(404) 
        self.render_extend('things_update.html', thing=thing)

    @tornado.web.authenticated
    def post(self):
        response = {'error': ''}
        try:
            tid = self.get_argument('tid')
            title = self.get_argument('title')
            subtitle = self.get_argument('subtitle')
            buylink = self.get_argument('buylink')
            tags = self.get_list_argument('tags')
            price = self.get_argument('price')
            image_ids = self.get_list_argument('image_ids', ObjectId)
            desc = self.get_argument('desc')

            self.db.things.update(
                    {
                        '_id': ObjectId(tid)
                    },
                    {
                        '$set':
                        {
                            'title': title,
                            'subtitle': subtitle,
                            'buylink': buylink,
                            'tags': tags,
                            'price': price,
                            'desc': desc,
                        },
                        '$addToSet':
                        {
                            'image_ids': { '$each': image_ids }
                        }
                    }
            )
            response['tid'] = tid
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)

        response_json = json_encode(response)
        self.write(response_json)

class ThingsCollectHandler(base.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        response = {'error': ''}
        try:
            tid = self.get_argument('tid')
            op = self.get_argument('op')
            if op == '1':
                self.db.users.update({'_id': self.current_user['_id']},
                                     {'$addToSet': {'collect': ObjectId(tid)}})
            else:
                self.db.users.update({'_id': self.current_user['_id']},
                                     {'$pull': {'collect': ObjectId(tid)}})
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)
        response_json = json_encode(response)
        self.write(response_json)

class ThingsFavorHandler(base.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        response = {'error': ''}
        try:
            tid = self.get_argument('tid')
            op = self.get_argument('op')
            if op == '1':
                logging.info('favor')
                self.db.users.update({'_id': self.current_user['_id']},
                                     {'$addToSet': {'favor': ObjectId(tid)}})
                thing = self.db.things.find_and_modify({'_id': ObjectId(tid)},
                                                       {'$inc': {'favor': 1}})
                response['favor'] = thing['favor'] + 1
            else:
                logging.info('disfavor')
                self.db.users.update({'_id': self.current_user['_id']},
                                     {'$pull': {'favor': ObjectId(tid)}})
                thing = self.db.things.find_and_modify({'_id': ObjectId(tid)},
                                                       {'$inc': {'favor': -1}})
                response['favor'] = thing['favor'] - 1
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)
        response_json = json_encode(response)
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
    def gen_thing_image_urls(self, thing):
        if thing['image_ids']:
            image_ids = thing['image_ids']
            urls = self.image_urls(image_ids)
            thing['image_urls'] = urls
        return thing

    def visit_plus(self, thing):
        self.db.things.update({'_id': thing['_id']},
                              {'$inc': {'visit': 1}},
                              w=0)

    def get_comments(self, tid):
        comments = list(self.db.comments.find({'tid': ObjectId(tid)})\
                        .sort('date', pymongo.DESCENDING))
        for cmt in comments:
            user = self.db.users.find_one({'_id': cmt['from']})
            cmt['from_name'] = user['name']
            cmt['from_img'] = user['img_url']
        return comments

    def get(self, tid):
        thing = self.db.things.find_one({'_id': ObjectId(tid)})
        if not thing:
            raise tornado.web.HTTPError(404) 

        thing = self.gen_thing_image_urls(thing)
        thing['user'] = self.db.users.find_one({'uid': thing['user']})
        thing['collected'] = self.current_user and (thing['_id'] in self.current_user['collect'])
        thing['favored'] = self.current_user and (thing['_id'] in self.current_user['favor'])

        comments = self.get_comments(ObjectId(tid))

        self.visit_plus(thing)
        self.render_extend('things_detail.html',
                           thing=thing,
                           comments=comments)

class ThingsQrcodeHandler(base.BaseHandler):
    def get_qrcode(self, data):
        qr = qrcode.QRCode(
            version=2,
            box_size=6,
            border=0,
        )
        qr.add_data(data)
        qr.make()
        return qr.make_image()

    def get(self):
        tid = self.get_argument('tid')
        url = '%s/things/detail/%s' % (options.domain, tid)

        fake_file = StringIO.StringIO()
        img = self.get_qrcode(url)
        img.save(fake_file, 'gif')
        response = fake_file.getvalue()
        fake_file.close()
        self.set_header('Content-Type', 'image/gif')
        self.write(response)

class ThingsRemoveHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        response = {'error': ''}
        try:
            tid = ObjectId(self.get_argument('tid'))
            self.db.users.update({'collect': tid},
                                 {'$pull': {'collect': tid}})
            self.db.users.update({'favor': tid},
                                 {'$pull': {'favor': tid}})
            self.db.things.remove({'_id': tid})
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)
        response_json = json_encode(response)
        self.write(response_json)

class ThingsCommentsNewHandler(base.BaseHandler):
    @tornado.web.authenticated
    def post(self):
        from_uid = self.current_user['_id']
        to_uid = self.get_argument('to')
        tid = self.get_argument('tid')
        content = self.get_argument('content')
        cid = self.db.comments.insert({
            'from': from_uid,
            'to': to_uid,
            'tid': ObjectId(tid),
            'content': content,
            'date': datetime.datetime.utcnow()
        })
        self.redirect('/things/detail/%s' % tid)

class ThingsPermitHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        response = {'error': ''}
        try:
            tid = ObjectId(self.get_argument('tid'))
            self.db.things.update({'_id': tid},
                                  {'$set': {'auth': 1}})
        except Exception, e:
            logging.warning(e)
            response['error'] = str(e)
        response_json = json_encode(response)
        self.write(response_json)

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
            self.db.users.update({'uid': uid},
                                 {
                                     '$set': {
                                         'uid': uid,
                                         'name': login_info['screen_name'],
                                         'img_url': login_info['profile_image_url']
                                     },
                                     '$setOnInsert': {
                                         'favor': [],
                                         'collect': []
                                     }
                                 },
                                 upsert=True)
            self.set_secure_cookie('uid', uid)
        else:
            logging.warning('login failed')
        self.redirect('/')

class UsersMessagesHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        pass # TODO

class UsersLogoutHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie('uid')
        self.redirect('/')

class UsersProfileHandler(base.BaseHandler):
    def get_comments(self, uid):
        comments = list(self.db.comments.find({'from': uid})\
                        .sort('date', pymongo.DESCENDING))
        for cmt in comments:
            cmt['thing_name'] = self.db.things.find_one({'_id': cmt['tid']})['title']

        logging.info('comments count: %d' % len(comments))
        return comments

    def get(self, uid):
        who = self.db.users.find_one({'_id': ObjectId(uid)})
        if not who:
            raise tornado.web.HTTPError(404) 
        favor = who.get('favor', None)
        if favor:
            things = list(self.db.things.find({'_id': {'$in': favor}}))
        else:
            things = []
        comments = self.get_comments(ObjectId(uid))
        self.render_extend('user.html',
                           who=who,
                           things=things,
                           comments=comments)

class AdminThingsHandler(base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        things = list(self.db.things.find({'auth': 0}).sort('date', pymongo.DESCENDING))
        self.render_extend('admin_things.html',
                            things=things)

class TestHandler(base.BaseHandler):
    def get(self):
        self.render_extend('test.html')

def main():
    tornado.options.parse_config_file('./kuke.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info('============ [ KuKe server START! ] ============')
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
