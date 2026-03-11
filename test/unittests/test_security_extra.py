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

"""Additional unit tests for ovos_utils.security — create_self_signed_cert."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch


class TestCreateSelfSignedCertMocked(unittest.TestCase):
    """Tests for create_self_signed_cert with a mocked pyOpenSSL crypto module."""

    def _make_mock_crypto(self) -> MagicMock:
        """Build a minimal mock of OpenSSL.crypto for testing."""
        mock_crypto = MagicMock()
        mock_key = MagicMock()
        mock_cert = MagicMock()

        mock_crypto.PKey.return_value = mock_key
        mock_crypto.TYPE_RSA = 6  # arbitrary constant
        mock_crypto.X509.return_value = mock_cert
        mock_crypto.FILETYPE_PEM = 1

        mock_crypto.dump_certificate.return_value = "CERT_DATA"
        mock_crypto.dump_privatekey.return_value = "KEY_DATA"

        return mock_crypto

    def test_creates_cert_and_key_files(self) -> None:
        """create_self_signed_cert should write .crt and .key files."""
        from ovos_utils.security import create_self_signed_cert

        mock_crypto = self._make_mock_crypto()
        with patch("ovos_utils.security.crypto", mock_crypto):
            with tempfile.TemporaryDirectory() as tmpdir:
                cert_path, key_path = create_self_signed_cert(tmpdir, name="test")
        self.assertTrue(cert_path.endswith(".crt"))
        self.assertTrue(key_path.endswith(".key"))

    def test_returns_existing_files_without_regenerating(self) -> None:
        """create_self_signed_cert should not overwrite existing cert/key files."""
        from ovos_utils.security import create_self_signed_cert

        mock_crypto = self._make_mock_crypto()
        with patch("ovos_utils.security.crypto", mock_crypto):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Pre-create the cert and key files
                cert_file = os.path.join(tmpdir, "test.crt")
                key_file = os.path.join(tmpdir, "test.key")
                with open(cert_file, "w") as f:
                    f.write("EXISTING_CERT")
                with open(key_file, "w") as f:
                    f.write("EXISTING_KEY")

                cert_path, key_path = create_self_signed_cert(tmpdir, name="test")

        # PKey should NOT have been called since files exist
        mock_crypto.PKey.assert_not_called()
        self.assertEqual(cert_path, cert_file)
        self.assertEqual(key_path, key_file)


if __name__ == "__main__":
    unittest.main()
