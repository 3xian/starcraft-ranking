# -*- coding: utf-8 -*-

import bson.objectid
import datetime
import logging
import os
import re
import StringIO
from bson.objectid import ObjectId

import pymongo
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
from tornado.options import define, options
from tornado.escape import json_encode

import base

define('host')
define('port', default=80, type=int)
define('domain')
define('items_per_page', type=int)
define('debug', type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/sc', IndexHandler),
            (r'/sc/contest/add', ContestAddHandler),
            (r'/sc/contest/rollback', ContestRollbackHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.getcwd(), 'templates'),
            static_path=os.path.join(os.getcwd(), 'static'),
            xsrf_cookies=False,
            debug=(options.debug != 0),
            static_handler_class=base.SmartStaticFileHandler,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = pymongo.MongoClient('off1.db', 19345).starcraft

class IndexHandler(base.BaseHandler):
    def get(self):
        players = list(self.db.player.find().sort('rating', pymongo.DESCENDING))
        contests = list(self.db.contest.find().sort('date', pymongo.DESCENDING))
        self.render('index.html', players=players, contests=contests)

class ContestAddHandler(base.BaseHandler):
    def post(self):
        winners = self.get_argument('winners').split()
        losers = self.get_argument('losers').split()
        logging.info('winners: %s' % str(winners))
        logging.info('losers: %s' % str(losers))
        if len(winners) == 0 or len(losers) == 0:
            self.write('输入为空')
            return

        contest = {'win':[], 'lose':[], 'date':datetime.datetime.now()}
        diff_sum = 0.0
        for w in losers:
            player = self.db.player.find_one({"name": w})
            if player is None:
                self.write('玩家[%s]不存在' % w.encode('utf8'))
                return
            d = player['rating'] / 10.0 / len(winners)
            diff_sum += d

        for w in winners:
            player = self.db.player.find_one({"name": w})
            if player is None:
                self.write('玩家[%s]不存在' % w.encode('utf8'))
                return
            contest['win'].append([w, player['rating'], player['rating'] + diff_sum / len(winners)])
        for w in losers:
            player = self.db.player.find_one({"name": w})
            d = player['rating'] / 10.0 / len(winners)
            contest['lose'].append([w, player['rating'], player['rating'] - d])

        logging.info(contest)
        self.db.contest.insert(contest)

        for w in contest['win'] + contest['lose']:
            self.db.player.update({"name": w[0]}, {'$set':{'rating': w[2]}})

        self.write('ok')

class ContestRollbackHandler(base.BaseHandler):
    def post(self):
        contest = list(self.db.contest.find().sort('date', pymongo.DESCENDING).limit(1))[0]

        for w in contest['win'] + contest['lose']:
            self.db.player.update({"name": w[0]}, {'$set':{'rating': w[1]}})

        self.db.contest.remove({'_id':contest['_id']})

def main():
    tornado.options.parse_config_file('./starcraft.conf')
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    logging.info('============ [ StarCraft server START! ] ============')
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()
