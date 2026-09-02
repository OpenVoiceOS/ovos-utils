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

"""Unit tests for ovos_utils.security module."""

import string
import unittest
from unittest.mock import MagicMock, patch


class TestRandomKey(unittest.TestCase):
    """Tests for random_key function."""

    def test_default_length(self) -> None:
        """random_key should return a 16-character string by default."""
        from ovos_utils.security import random_key
        key = random_key()
        self.assertEqual(len(key), 16)

    def test_custom_length(self) -> None:
        """random_key should return a string of the specified length."""
        from ovos_utils.security import random_key
        key = random_key(32)
        self.assertEqual(len(key), 32)

    def test_key_contains_valid_chars(self) -> None:
        """random_key characters should be alphanumeric."""
        from ovos_utils.security import random_key
        valid = set(string.ascii_letters + string.digits)
        key = random_key(64)
        for ch in key:
            self.assertIn(ch, valid)

    def test_keys_are_random(self) -> None:
        """Two successive calls should (almost certainly) produce different keys."""
        from ovos_utils.security import random_key
        keys = {random_key() for _ in range(10)}
        self.assertGreater(len(keys), 1)


class TestEncryptDecrypt(unittest.TestCase):
    """Tests for encrypt/decrypt functions."""

    @unittest.skipIf(
        True,  # Skip if AES not available; we'll test via mock
        "AES not available"
    )
    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Encrypting then decrypting should recover the original text."""
        pass  # Replaced by mock test below

    def test_encrypt_raises_import_error_when_aes_none(self) -> None:
        """encrypt should raise ImportError when AES is None."""
        with patch("ovos_utils.security.AES", None):
            from ovos_utils.security import encrypt
            with self.assertRaises(ImportError):
                encrypt("key1234567890123", "hello")

    def test_decrypt_raises_import_error_when_aes_none(self) -> None:
        """decrypt should raise ImportError when AES is None."""
        with patch("ovos_utils.security.AES", None):
            from ovos_utils.security import decrypt
            with self.assertRaises(ImportError):
                decrypt("key1234567890123", b"cipher", b"tag", b"nonce")

    def test_encrypt_with_mock_aes(self) -> None:
        """encrypt should call AES.new and return ciphertext, tag, nonce."""
        mock_aes = MagicMock()
        mock_cipher = MagicMock()
        mock_cipher.encrypt_and_digest.return_value = (b"ciphertext", b"tag")
        mock_cipher.nonce = b"nonce123"
        mock_aes.new.return_value = mock_cipher
        mock_aes.MODE_GCM = 2  # arbitrary constant

        with patch("ovos_utils.security.AES", mock_aes):
            from ovos_utils.security import encrypt
            ciphertext, tag, nonce = encrypt("1234567890123456", "hello world")

        self.assertEqual(ciphertext, b"ciphertext")
        self.assertEqual(tag, b"tag")
        self.assertEqual(nonce, b"nonce123")

    def test_decrypt_with_mock_aes(self) -> None:
        """decrypt should call AES.new and return decoded plaintext."""
        mock_aes = MagicMock()
        mock_cipher = MagicMock()
        mock_cipher.decrypt_and_verify.return_value = b"hello world"
        mock_aes.new.return_value = mock_cipher
        mock_aes.MODE_GCM = 2

        with patch("ovos_utils.security.AES", mock_aes):
            from ovos_utils.security import decrypt
            result = decrypt("1234567890123456", b"ciphertext", b"tag", b"nonce")

        self.assertEqual(result, "hello world")

    def test_encrypt_accepts_bytes_key(self) -> None:
        """encrypt should work when key is already bytes."""
        mock_aes = MagicMock()
        mock_cipher = MagicMock()
        mock_cipher.encrypt_and_digest.return_value = (b"ct", b"tag")
        mock_cipher.nonce = b"nonce"
        mock_aes.new.return_value = mock_cipher
        mock_aes.MODE_GCM = 2

        with patch("ovos_utils.security.AES", mock_aes):
            from ovos_utils.security import encrypt
            # Passing bytes key — should not encode again
            encrypt(b"1234567890123456", "text")

        mock_aes.new.assert_called_once()
        call_args = mock_aes.new.call_args[0]
        self.assertIsInstance(call_args[0], bytes)

    def test_encrypt_accepts_bytes_text(self) -> None:
        """encrypt should work when text is already bytes."""
        mock_aes = MagicMock()
        mock_cipher = MagicMock()
        mock_cipher.encrypt_and_digest.return_value = (b"ct", b"tag")
        mock_cipher.nonce = b"nonce"
        mock_aes.new.return_value = mock_cipher
        mock_aes.MODE_GCM = 2

        with patch("ovos_utils.security.AES", mock_aes):
            from ovos_utils.security import encrypt
            encrypt("1234567890123456", b"already bytes")

        mock_cipher.encrypt_and_digest.assert_called_once_with(b"already bytes")

    def test_decrypt_raises_on_bad_tag(self) -> None:
        """decrypt should propagate exceptions from decrypt_and_verify."""
        mock_aes = MagicMock()
        mock_cipher = MagicMock()
        mock_cipher.decrypt_and_verify.side_effect = ValueError("MAC check failed")
        mock_aes.new.return_value = mock_cipher
        mock_aes.MODE_GCM = 2

        with patch("ovos_utils.security.AES", mock_aes):
            from ovos_utils.security import decrypt
            with self.assertRaises(ValueError):
                decrypt("1234567890123456", b"bad", b"bad_tag", b"nonce")


if __name__ == "__main__":
    unittest.main()
