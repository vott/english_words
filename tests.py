import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web
from unittest.mock import patch

from main import init
from utils import fetch_words

class DuckDuckGoTestCase(AioHTTPTestCase):

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """
        return init()


    @unittest_run_loop
    async def test_spam(self):
        resp = await self.client.request("GET", "/search/duckduckgo/sfsdf")
        assert resp.status == 200
        text = await resp.text()
        assert "sfsdf" in text


class TestFetchWords(unittest.TestCase):
    """Tests util function
    """
    def setUp(self):
        self.func = fetch_words

    def test_functions_filter(self):
        """Tests word filtering 
        """
        with patch('requests.get') as request:
            with open('./test_info.txt') as mock_text:
                _test_text = mock_text.read()
                request.return_value.text = _test_text
                filtered_words = self.func()
        self.assertListEqual(filtered_words, ['hello', 'eeW'])
