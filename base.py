import logging
import os

import pymongo
import tornado.web

class SmartStaticFileHandler(tornado.web.StaticFileHandler):
    @classmethod
    def kick_version_cache(cls, abs_path):
        with cls._lock:
            hashes = cls._static_hashes
            if abs_path in hashes:
                del hashes[abs_path]

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def static_path(self, sub=''):
        return os.path.join(self.settings['static_path'], sub)

    def get_current_user(self):
        uid = self.get_secure_cookie('uid')
        if not uid:
            return None
        return self.db.users.find_one({'uid':uid})

    def render_extend(self, template_name, user=None, sort_type=None, **args):
        if not user:
            user = self.current_user
        self.render(template_name, user=user, sort_type=sort_type, **args)

    def str_to_list(self, s, element_class=str):
        return [element_class(x.strip().encode('utf8')) for x in s.split(',') if x.strip()]

    def get_list_argument(self, key, element_class=str):
        buf = self.get_argument(key, '')
        return self.str_to_list(buf, element_class)

    def image_urls(self, image_ids):
        images = list(self.db.images.find({'_id': {'$in': image_ids}}).sort('date', pymongo.DESCENDING))
        return [os.path.join('data', str(img['_id'])+img['ext']) for img in images]

    def gen_things_image_url(self, things):
        for thing in things:
            if thing.get('image_ids', None):
                image_id = thing['image_ids'][0]
                urls = self.image_urls([image_id])
                thing['image_url'] = urls[0]
            else:
                thing['image_url'] = 'http://www.baidu.com/img/bdlogo.gif'
        return things
