from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop
import tornado_client_cache

ioloop = IOLoop.current()


@gen.coroutine
def get_nu():
    c = AsyncHTTPClient()
    resp = yield c.fetch("http://www.nu.nl/")
    raise gen.Return(resp)

def done(f):
    ioloop.stop()
    print f.result()
    print "From cache: ", hasattr(f.result(), 'cached')

tornado_client_cache.patch()
f = get_nu()
f.add_done_callback(done)
ioloop.start()
