
import unittest
from time import sleep


class TestNetworkUtils(unittest.TestCase):
    def test_get_network_tests_config(self):
        from ovos_utils.network_utils import get_network_tests_config
        # self.assertEqual(set(get_network_tests_config().keys()),
        #                  {'ip_url', 'dns_primary', 'dns_secondary', 'web_url',
        #                   'web_url_secondary', 'captive_portal_url',
        #                   'captive_portal_text'})
        # TODO: Validate config in helper method

    def test_get_ip(self):
        from ovos_utils.network_utils import get_ip
        ip_addr = get_ip()
        self.assertIsInstance(ip_addr, str)
        self.assertEqual(len(ip_addr.split('.')), 4)

    def test_get_external_ip(self):
        from ovos_utils.network_utils import get_external_ip
        ip_addr = get_external_ip()
        self.assertIsInstance(ip_addr, str)
        self.assertEqual(len(ip_addr.split('.')), 4, ip_addr)

    def test_is_connected_dns(self):
        from ovos_utils.network_utils import is_connected_dns
        self.assertIsInstance(is_connected_dns(), bool)
        # TODO

    def test_is_connected_http(self):
        from ovos_utils.network_utils import is_connected_http
        self.assertIsInstance(is_connected_http(), bool)
        # TODO

    def test_is_connected(self):
        from ovos_utils.network_utils import is_connected
        self.assertIsInstance(is_connected(), bool)
        # TODO

    def test_check_captive_portal(self):
        from ovos_utils.network_utils import check_captive_portal
        # TODO
