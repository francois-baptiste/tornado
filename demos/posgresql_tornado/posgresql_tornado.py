#!/usr/bin/env python

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import parse_command_line
from tornado import web

import momoko


class BaseHandler(web.RequestHandler):
    @property
    def db(self):
        return self.application.db


class TutorialHandler(BaseHandler):
    @gen.coroutine
    def get(self):
        cursor = yield self.db.execute("SELECT 1;")
        self.write("Results: %s" % cursor.fetchone())
        self.finish()


if __name__ == '__main__':
    parse_command_line()
    application = web.Application([
        (r'/', TutorialHandler)
    ], debug=True)

    ioloop = IOLoop.instance()

    application.db = momoko.Pool(
        dsn='dbname=tornado user=francois password=francois '
            'host=localhost port=32768',
        size=1,
        ioloop=ioloop,
    )

    # this is a one way to run ioloop in sync
    future = application.db.connect()
    ioloop.add_future(future, lambda f: ioloop.stop())
    ioloop.start()
    future.result()  # raises exception on connection error

    http_server = HTTPServer(application)
    http_server.listen(8888, 'localhost')
    ioloop.start()
