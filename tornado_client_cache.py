import hashlib
import os
import re
from tornado.concurrent import Future
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
# from sqlitedict import SqliteDict
from tornado.httputil import HTTPHeaders
import pickle

class Cache(object):
    def __init__(self, cache_name='cache'):
        self.cache_name = cache_name
        if not os.path.isdir(cache_name):
            os.makedirs(cache_name)

#        self.backend = SqliteDict(cache_name + '.sqlite', 'cache', autocommit=True)

    def create_key(self, request):
        """
        Create cache key for a request

        :param tornado.httpclient.HTTPRequest request: Request to create cache key for
        :return:
        """
        key = hashlib.sha256()
        key.update(request.method.upper().encode('ascii'))
        key.update(request.url.encode('ascii'))
        if request.body:
            key.update(request.body)

        url_filename = re.sub(r'[^\w\d\.\-]', '_', request.url) # .encode('ascii')
        return url_filename + '-' + key.hexdigest()

    def get_response_and_time(self, key):
        try:
            with open(self.cache_name + '/' + key, 'rb') as fh:
                # resp = self.backend[key]
                data = pickle.load(fh)
                return self._decode_headers(data)
        except (OSError, KeyError):
            return None

    def save_response(self, key, response):
        with open(self.cache_name + '/' + key, 'wb') as fh:
            pickle.dump(self._encode_headers(response), fh)
        # self.backend[key] = self._encode_headers(response)

    def _encode_headers(self, response):
        def encode(headers):
            tuples = []
            for pair in headers.get_all():
                tuples.append(pair)
            return tuples
        response.headers = encode(response.headers)
        response.request.headers = encode(response.request.headers)
        return response

    def _decode_headers(self, response):
        def decode(pairs):
            headers = HTTPHeaders()
            for name, value in pairs:
                headers.add(name, value)
            return headers
        response.headers = decode(response.headers)
        response.request.headers = decode(response.request.headers)
        return response


def patch(cache_name='cache'):

    AsyncHTTPClient.cache = Cache(cache_name)
    AsyncHTTPClient.pending_requests = {}

    orig_fetch = AsyncHTTPClient.fetch

    def fetch(self, request, callback=None, raise_error=True, **kwargs):
        if not isinstance(request, HTTPRequest):
            request = HTTPRequest(url=request, **kwargs)

        key = self.cache.create_key(request)

        # Check and return future if there is a pending request
        pending = self.pending_requests.get(key)
        if pending:
            return pending

        response = self.cache.get_response_and_time(key)
        if response:
            response.cached = True
            if callback:
                self.io_loop.add_callback(callback, response)
            future = Future()
            future.set_result(response)
            return future

        future = orig_fetch(self, request, callback, raise_error, **kwargs)

        self.pending_requests[key] = future

        def cache_response(future):
            exc = future.exception()
            if exc is None:
                self.cache.save_response(key, future.result())

        future.add_done_callback(cache_response)
        return future

    AsyncHTTPClient.fetch = fetch
