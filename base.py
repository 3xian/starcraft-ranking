import tornado.web

class SmartStaticFileHandler(tornado.web.StaticFileHandler):
    @classmethod
    def kick_version_cache(cls, abs_path):
        with cls._lock:
            hashes = cls._static_hashes
            if abs_path in hashes:
                del hashes[abs_path]

class BaseHandler(tornado.web.RequestHandler):
    def static_path(self, subdir=''):
        return os.path.join(self.settings['static_path'], subdir)
