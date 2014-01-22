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
