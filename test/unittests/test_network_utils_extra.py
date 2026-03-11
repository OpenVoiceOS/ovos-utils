# Copyright 2024, OpenVoiceOS
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Additional unit tests for ovos_utils.network_utils module."""

import unittest
from unittest.mock import MagicMock, patch


class TestIsValidIp(unittest.TestCase):
    """Tests for is_valid_ip."""

    def test_valid_ipv4(self) -> None:
        """is_valid_ip should return True for a valid IPv4 address."""
        from ovos_utils.network_utils import is_valid_ip
        self.assertTrue(is_valid_ip("8.8.8.8"))

    def test_valid_ipv6(self) -> None:
        """is_valid_ip should return True for a valid IPv6 address."""
        from ovos_utils.network_utils import is_valid_ip
        self.assertTrue(is_valid_ip("2001:db8::1"))

    def test_invalid_ip(self) -> None:
        """is_valid_ip should return False for an invalid address string."""
        from ovos_utils.network_utils import is_valid_ip
        self.assertFalse(is_valid_ip("not_an_ip"))
        self.assertFalse(is_valid_ip("999.999.999.999"))


class TestGetExternalIp(unittest.TestCase):
    """Tests for get_external_ip with mocked HTTP."""

    @patch("ovos_utils.network_utils.requests.get")
    def test_returns_ip_from_service(self, mock_get: MagicMock) -> None:
        """get_external_ip should return IP text from ipify.org."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.text = "1.2.3.4"
        mock_get.return_value = mock_resp
        from ovos_utils.network_utils import get_external_ip
        result = get_external_ip()
        self.assertEqual(result, "1.2.3.4")

    @patch("ovos_utils.network_utils.requests.get")
    def test_returns_fallback_on_failure(self, mock_get: MagicMock) -> None:
        """get_external_ip should return '0.0.0.0' on request failure."""
        mock_get.side_effect = Exception("network error")
        from ovos_utils.network_utils import get_external_ip
        result = get_external_ip()
        self.assertEqual(result, "0.0.0.0")

    @patch("ovos_utils.network_utils.requests.get")
    def test_returns_fallback_on_bad_status(self, mock_get: MagicMock) -> None:
        """get_external_ip should return '0.0.0.0' when response is not OK."""
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 503
        mock_resp.text = ""
        mock_get.return_value = mock_resp
        from ovos_utils.network_utils import get_external_ip
        result = get_external_ip()
        self.assertEqual(result, "0.0.0.0")


class TestIsConnectedDns(unittest.TestCase):
    """Tests for is_connected_dns with mocked socket."""

    @patch("ovos_utils.network_utils.socket.socket")
    def test_returns_true_when_connection_succeeds(
        self, mock_socket_cls: MagicMock
    ) -> None:
        """is_connected_dns should return True when socket connect succeeds."""
        mock_sock = MagicMock()
        mock_socket_cls.return_value = mock_sock
        from ovos_utils.network_utils import is_connected_dns
        result = is_connected_dns("1.1.1.1")
        self.assertTrue(result)

    @patch("ovos_utils.network_utils.socket.socket")
    def test_returns_false_when_connection_fails(
        self, mock_socket_cls: MagicMock
    ) -> None:
        """is_connected_dns should return False when socket connect raises OSError."""
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("refused")
        mock_socket_cls.return_value = mock_sock
        from ovos_utils.network_utils import is_connected_dns
        result = is_connected_dns("1.1.1.1")
        self.assertFalse(result)


class TestIsConnectedHttp(unittest.TestCase):
    """Tests for is_connected_http."""

    @patch("ovos_utils.network_utils.requests.head")
    def test_returns_true_on_success(self, mock_head: MagicMock) -> None:
        """is_connected_http should return True when HTTP head succeeds."""
        mock_head.return_value = MagicMock(status_code=200)
        from ovos_utils.network_utils import is_connected_http
        result = is_connected_http("http://example.com")
        self.assertTrue(result)

    @patch("ovos_utils.network_utils.requests.head")
    def test_returns_false_on_exception(self, mock_head: MagicMock) -> None:
        """is_connected_http should return False when request raises."""
        mock_head.side_effect = Exception("unreachable")
        from ovos_utils.network_utils import is_connected_http
        result = is_connected_http("http://example.com")
        self.assertFalse(result)


class TestCheckCaptivePortal(unittest.TestCase):
    """Tests for check_captive_portal."""

    @patch("ovos_utils.network_utils.requests.get")
    def test_no_captive_portal(self, mock_get: MagicMock) -> None:
        """check_captive_portal should return False when expected text is found."""
        mock_resp = MagicMock()
        mock_resp.text = "NetworkManager is online"
        mock_get.return_value = mock_resp
        from ovos_utils.network_utils import check_captive_portal
        result = check_captive_portal(
            host="http://nmcheck.gnome.org/check_network_status.txt",
            expected_text="NetworkManager is online",
        )
        self.assertFalse(result)

    @patch("ovos_utils.network_utils.requests.get")
    def test_captive_portal_detected(self, mock_get: MagicMock) -> None:
        """check_captive_portal should return True when text differs (redirect)."""
        mock_resp = MagicMock()
        mock_resp.text = "<html>Login to network</html>"
        mock_get.return_value = mock_resp
        from ovos_utils.network_utils import check_captive_portal
        result = check_captive_portal(
            host="http://nmcheck.gnome.org/check_network_status.txt",
            expected_text="NetworkManager is online",
        )
        self.assertTrue(result)

    @patch("ovos_utils.network_utils.requests.get")
    def test_returns_false_on_exception(self, mock_get: MagicMock) -> None:
        """check_captive_portal should return False when request raises."""
        mock_get.side_effect = Exception("timeout")
        from ovos_utils.network_utils import check_captive_portal
        result = check_captive_portal(
            host="http://nmcheck.gnome.org/check_network_status.txt",
            expected_text="NetworkManager is online",
        )
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
