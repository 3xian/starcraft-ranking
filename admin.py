import tornado.web

import kuke_util

class AdminHandler(kuke_base.BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('admin.html',
                user_name=self.current_user['name'],
                time=datetime.datetime.now())

