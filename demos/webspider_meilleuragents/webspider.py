#!/usr/bin/env python

import time
from datetime import timedelta

try:
    from HTMLParser import HTMLParser
    from urlparse import urljoin, urldefrag
except ImportError:
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urldefrag

import geojson
from tornado import httpclient, gen, ioloop, queues, curl_httpclient

start_url = 'https://static0.meilleursagents.com/static/build/images/major-cities.geojson'
base_url = 'http://www.meilleursagents.com/prix-immobilier/'
target_url = 'http://api.meilleursagents.com/indices/v1/indice/'
concurrency = 10

import momoko


async def get_links_from_url(url):
    try:
        if url.startswith(target_url):
            print('target url %s' % url)

        if url == start_url:
            response = await curl_httpclient.AsyncHTTPClient().fetch(url)
            urls = ["http://www.meilleursagents.com" + elem['properties']['href'] for elem in
                    geojson.loads(response.body)['features']]
            print('fetched %s' % urls)
            return urls

        if url.startswith(base_url):
            response = await httpclient.AsyncHTTPClient().fetch(url)
            print('fetched %s' % url)
            html = response.body if isinstance(response.body, str) \
                else response.body.decode()
            urls = [urljoin(url, remove_fragment(new_url))
                    for new_url in get_links(html)]
            return urls

        return []
    except Exception as e:
        print('Exception: %s %s' % (e, url))
        return []


def remove_fragment(url):
    pure_url, frag = urldefrag(url)
    return pure_url


def get_links(html):
    class URLSeeker(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.urls = []

        def handle_starttag(self, tag, attrs):
            href = dict(attrs).get('href')
            # if href and tag == 'a':
            #     if href.count("/") < 6:
            #         self.urls.append(href)
            src = dict(attrs).get('src')
            if src and tag == 'img':
                if src.endswith("/chart"):
                    self.urls.append(src[:-len("/chart")])

    url_seeker = URLSeeker()
    url_seeker.feed(html)
    return url_seeker.urls


async def main():
    q = queues.Queue()
    start = time.time()
    fetching, fetched = set(), set()

    async def fetch_url():
        current_url = await q.get()
        try:
            if current_url in fetching:
                return

            print('fetching %s' % current_url)
            fetching.add(current_url)
            urls = await get_links_from_url(current_url)
            fetched.add(current_url)

            for new_url in urls:
                # Only follow links beneath the base URL
                if "meilleursagents" in new_url:
                    await q.put(new_url)

        finally:
            q.task_done()


    q.put(start_url)

    # Start workers, then wait for the work queue to be empty.
    for _ in range(concurrency):
        ioloop.IOLoop.current().spawn_callback(fetch_url)

    await q.join(timeout=timedelta(seconds=300))
    assert fetching == fetched
    print('Done in %d seconds, fetched %s URLs.' % (
        time.time() - start, len(fetched)))


if __name__ == '__main__':
    import logging

    logging.basicConfig()
    io_loop = ioloop.IOLoop.current()

    # db = momoko.Pool(
    #     dsn='dbname=tornado user=francois password=francois '
    #         'host=AKASA port=32768',
    #     size=1,
    #     ioloop=ioloop,
    # )

    io_loop.run_sync(main)
