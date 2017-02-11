#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import parse_command_line

try:
    from HTMLParser import HTMLParser
    from urlparse import urljoin, urldefrag
except ImportError:
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urldefrag

from tornado import httpclient, gen, ioloop, queues, curl_httpclient

from tornado.options import define, options


class BaseHandler(tornado.web.RequestHandler):
    @property
    def base_url(self):
        return self.application.base_url


class MainHandler(BaseHandler):



    # def get(self):
    #     self.write("Hello, world")
    @gen.coroutine
    def get(self):
        """Download the page at `url` and parse it for links.

        Returned links have had the fragment after `#` removed, and have been made
        absolute so, e.g. the URL 'gen.html#tornado.gen.coroutine' becomes
        'http://www.tornadoweb.org/en/stable/gen.html'.
        """
        try:
            response = yield curl_httpclient.AsyncHTTPClient().fetch(self.base_url)
            print('fetched %s' % self.base_url)
            html = response.body if isinstance(response.body, str) \
                else response.body.decode()
        except Exception as e:
            print('Exception: %s %s' % (e, self.base_url))
            self.write("Hello, world")
            self.finish()


        self.write(html)
        self.finish()



if __name__ == '__main__':
    parse_command_line()
    application = tornado.web.Application([
        (r'/', MainHandler)
    ], debug=True)

    ioloop = IOLoop.instance()

    application.base_url = 'https://www.duckduckgo.com'


    http_server = HTTPServer(application)
    http_server.listen(8888, 'localhost')
    ioloop.start()
