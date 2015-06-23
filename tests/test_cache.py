from tornado.testing import AsyncTestCase, gen_test, AsyncHTTPClient
import tornado_client_cache


class TestCache(AsyncTestCase):
    # def setUp(self):
    #     super(TestCache, self).setUp()

    # def tearDown(self):
    #     super(TestCache, self).tearDown()
        # tornado_client_cache.unpatch()

    @gen_test
    def test_that_result_is_cached(self):
        client = AsyncHTTPClient(self.io_loop)
        tornado_client_cache.patch()
        resp = yield client.fetch('http://httpbin.org/get')
        self.assertFalse(hasattr(resp, 'cached'))
        resp = yield client.fetch('http://httpbin.org/get')
        self.assertTrue(resp.cached)

    # @gen_test
    # def test_that_unpatch_works(self):
    #     client = AsyncHTTPClient(self.io_loop)
    #     resp = yield client.fetch('http://httpbin.org/get')
    #     self.assertFalse(hasattr(resp, 'cached'))
    #     resp = yield client.fetch('http://httpbin.org/get')
    #     self.assertTrue(resp.cached)
    #
    #     tornado_client_cache.unpatch()
    #     resp = yield client.fetch('http://httpbin.org/get')
    #     self.assertFalse(hasattr(resp, 'cached'))

