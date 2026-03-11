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

"""Unit tests for ovos_utils.geolocation module."""

import unittest
from unittest.mock import MagicMock, patch


def _make_response(status_code: int, json_data: object) -> MagicMock:
    """Build a mock requests.Response object."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


class TestGetTimezone(unittest.TestCase):
    """Tests for get_timezone function."""

    def test_valid_coordinates(self) -> None:
        """get_timezone should return name and code for valid coords."""
        mock_finder = MagicMock()
        mock_finder.timezone_at.return_value = "America/New_York"

        with patch("ovos_utils.geolocation._tz_finder", mock_finder):
            from ovos_utils.geolocation import get_timezone
            result = get_timezone(40.7128, -74.0060)

        self.assertEqual(result["code"], "America/New_York")
        self.assertIn("America", result["name"])

    def test_invalid_latitude_raises(self) -> None:
        """get_timezone should raise ValueError for out-of-range latitude."""
        mock_finder = MagicMock()
        with patch("ovos_utils.geolocation._tz_finder", mock_finder):
            from ovos_utils.geolocation import get_timezone
            with self.assertRaises(ValueError):
                get_timezone(999, 0)

    def test_invalid_longitude_raises(self) -> None:
        """get_timezone should raise ValueError for out-of-range longitude."""
        mock_finder = MagicMock()
        with patch("ovos_utils.geolocation._tz_finder", mock_finder):
            from ovos_utils.geolocation import get_timezone
            with self.assertRaises(ValueError):
                get_timezone(0, 999)

    def test_timezone_not_found_raises_runtime_error(self) -> None:
        """get_timezone should raise RuntimeError when timezone_at returns None."""
        mock_finder = MagicMock()
        mock_finder.timezone_at.return_value = None
        with patch("ovos_utils.geolocation._tz_finder", mock_finder):
            from ovos_utils.geolocation import get_timezone
            with self.assertRaises(RuntimeError):
                get_timezone(0, 0)


class TestGetReverseGeolocation(unittest.TestCase):
    """Tests for get_reverse_geolocation function."""

    def _make_reverse_response(self) -> dict:
        """Create a sample nominatim reverse geocoding response."""
        return {
            "display_name": "New York, US",
            "lat": "40.7128",
            "lon": "-74.006",
            "address": {
                "city": "New York",
                "state": "New York",
                "state_code": "NY",
                "country": "United States",
                "country_code": "us",
                "postcode": "10001",
            }
        }

    @patch("ovos_utils.geolocation.get_timezone")
    @patch("ovos_utils.geolocation.requests.get")
    def test_successful_reverse_geolocation(
        self, mock_get: MagicMock, mock_tz: MagicMock
    ) -> None:
        """get_reverse_geolocation should parse a valid response and return location dict."""
        mock_get.return_value = _make_response(200, self._make_reverse_response())
        mock_tz.return_value = {"code": "America/New_York", "name": "America New_York"}

        # Clear LRU cache before calling
        from ovos_utils.geolocation import get_reverse_geolocation
        get_reverse_geolocation.cache_clear()
        result = get_reverse_geolocation(40.7128, -74.006)

        self.assertIn("city", result)
        self.assertIn("coordinate", result)
        self.assertEqual(result["city"]["name"], "New York")

    @patch("ovos_utils.geolocation.requests.get")
    def test_http_error_raises_connection_error(self, mock_get: MagicMock) -> None:
        """get_reverse_geolocation should raise ConnectionError on non-200 status."""
        mock_get.return_value = _make_response(500, {})
        from ovos_utils.geolocation import get_reverse_geolocation
        get_reverse_geolocation.cache_clear()
        with self.assertRaises(ConnectionError):
            get_reverse_geolocation(0.0, 0.0)

    @patch("ovos_utils.geolocation.requests.get")
    def test_empty_address_raises_value_error(self, mock_get: MagicMock) -> None:
        """get_reverse_geolocation should raise ValueError when address is empty."""
        mock_get.return_value = _make_response(200, {
            "display_name": "Somewhere",
            "lat": "0",
            "lon": "0",
            "address": {}
        })
        from ovos_utils.geolocation import get_reverse_geolocation
        get_reverse_geolocation.cache_clear()
        # Empty address dict is falsy
        # The function checks `if not address`
        # Empty dict is falsy, so this should raise ValueError
        # But address is `{}` which is falsy, triggering the ValueError
        with self.assertRaises(ValueError):
            get_reverse_geolocation(1.0, 1.0)

    @patch("ovos_utils.geolocation.requests.get")
    def test_request_exception_raises_connection_error(self, mock_get: MagicMock) -> None:
        """get_reverse_geolocation should raise ConnectionError on RequestException."""
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("timeout")
        from ovos_utils.geolocation import get_reverse_geolocation
        get_reverse_geolocation.cache_clear()
        with self.assertRaises(ConnectionError):
            get_reverse_geolocation(2.0, 2.0)


class TestGetGeolocation(unittest.TestCase):
    """Tests for get_geolocation function."""

    @patch("ovos_utils.geolocation.get_reverse_geolocation")
    @patch("ovos_utils.geolocation.requests.get")
    def test_successful_geolocation(
        self, mock_get: MagicMock, mock_rev: MagicMock
    ) -> None:
        """get_geolocation should call reverse geolocation when lat/lon present."""
        nominatim_result = [{"lat": "40.7", "lon": "-74.0", "display_name": "New York"}]
        mock_get.return_value = _make_response(200, nominatim_result)
        mock_rev.return_value = {"city": {"name": "New York"}}

        from ovos_utils.geolocation import get_geolocation
        get_geolocation.cache_clear()
        result = get_geolocation("New York")
        mock_rev.assert_called_once()
        self.assertEqual(result["city"]["name"], "New York")

    @patch("ovos_utils.geolocation.requests.get")
    def test_empty_result_raises_value_error(self, mock_get: MagicMock) -> None:
        """get_geolocation should raise ValueError when result list is empty."""
        mock_get.return_value = _make_response(200, [])
        from ovos_utils.geolocation import get_geolocation
        get_geolocation.cache_clear()
        with self.assertRaises(ValueError):
            get_geolocation("NonExistentPlaceXYZ")

    @patch("ovos_utils.geolocation.requests.get")
    def test_http_error_raises_connection_error(self, mock_get: MagicMock) -> None:
        """get_geolocation should raise ConnectionError on non-200 status."""
        mock_get.return_value = _make_response(503, [])
        from ovos_utils.geolocation import get_geolocation
        get_geolocation.cache_clear()
        with self.assertRaises(ConnectionError):
            get_geolocation("AnyCity")

    @patch("ovos_utils.geolocation.requests.get")
    def test_request_exception_raises_connection_error(self, mock_get: MagicMock) -> None:
        """get_geolocation should raise ConnectionError on network failure."""
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("network error")
        from ovos_utils.geolocation import get_geolocation
        get_geolocation.cache_clear()
        with self.assertRaises(ConnectionError):
            get_geolocation("SomeCity")


class TestGetIpGeolocation(unittest.TestCase):
    """Tests for get_ip_geolocation function."""

    def _make_ip_response(self) -> dict:
        """Build a sample ip-api.com success response."""
        return {
            "status": "success",
            "country": "United States",
            "countryCode": "US",
            "region": "NY",
            "regionName": "New York",
            "city": "New York City",
            "lat": 40.7128,
            "lon": -74.006,
            "timezone": "America/New_York",
            "query": "8.8.8.8",
        }

    @patch("ovos_utils.geolocation.requests.get")
    def test_successful_ip_geolocation(self, mock_get: MagicMock) -> None:
        """get_ip_geolocation should parse a valid ip-api.com response."""
        mock_get.return_value = _make_response(200, self._make_ip_response())
        from ovos_utils.geolocation import get_ip_geolocation
        get_ip_geolocation.cache_clear()
        result = get_ip_geolocation(ip="8.8.8.8")
        self.assertIn("city", result)
        self.assertIn("coordinate", result)
        self.assertIn("timezone", result)
        self.assertEqual(result["city"]["name"], "New York City")

    @patch("ovos_utils.geolocation.requests.get")
    def test_invalid_ip_raises_value_error(self, mock_get: MagicMock) -> None:
        """get_ip_geolocation should raise ValueError for an invalid IP address."""
        from ovos_utils.geolocation import get_ip_geolocation
        get_ip_geolocation.cache_clear()
        with self.assertRaises(ValueError):
            get_ip_geolocation(ip="not_an_ip")

    @patch("ovos_utils.geolocation.requests.get")
    def test_http_error_raises_connection_error(self, mock_get: MagicMock) -> None:
        """get_ip_geolocation should raise ConnectionError on non-200 response."""
        mock_get.return_value = _make_response(503, {})
        from ovos_utils.geolocation import get_ip_geolocation
        get_ip_geolocation.cache_clear()
        with self.assertRaises(ConnectionError):
            get_ip_geolocation(ip="8.8.8.8")

    @patch("ovos_utils.geolocation.requests.get")
    def test_api_fail_status_raises_value_error(self, mock_get: MagicMock) -> None:
        """get_ip_geolocation should raise ValueError when api returns fail status."""
        mock_get.return_value = _make_response(200, {"status": "fail", "message": "reserved range"})
        from ovos_utils.geolocation import get_ip_geolocation
        get_ip_geolocation.cache_clear()
        with self.assertRaises(ValueError):
            get_ip_geolocation(ip="8.8.8.8")

    @patch("ovos_utils.geolocation.requests.get")
    def test_unsupported_lang_defaults_to_english(self, mock_get: MagicMock) -> None:
        """get_ip_geolocation should fall back to 'en' for unsupported languages."""
        mock_get.return_value = _make_response(200, self._make_ip_response())
        from ovos_utils.geolocation import get_ip_geolocation
        get_ip_geolocation.cache_clear()
        # 'fi' (Finnish) is unsupported by ip-api.com
        result = get_ip_geolocation(ip="8.8.8.8", lang="fi")
        self.assertIsNotNone(result)
        # Verify that the request used lang=en
        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs["params"]["lang"], "en")

    @patch("ovos_utils.geolocation.get_external_ip")
    @patch("ovos_utils.geolocation.requests.get")
    def test_localhost_ip_fetches_external(
        self, mock_get: MagicMock, mock_ext_ip: MagicMock
    ) -> None:
        """get_ip_geolocation should resolve external IP when given localhost."""
        mock_ext_ip.return_value = "8.8.8.8"
        mock_get.return_value = _make_response(200, self._make_ip_response())
        from ovos_utils.geolocation import get_ip_geolocation
        get_ip_geolocation.cache_clear()
        result = get_ip_geolocation(ip="127.0.0.1")
        mock_ext_ip.assert_called_once()
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
