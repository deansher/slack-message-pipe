# MIT License
#
# Copyright (c) 2019 Erik Kalkoken

import urllib.request

from tests.helpers import NoSocketsTestCase, SocketAccessError


class TestNoSocketsTestCase(NoSocketsTestCase):
    def test_raises_exception_on_attempted_network_access(self):
        with self.assertRaises(SocketAccessError):
            urllib.request.urlopen("https://www.google.com")
