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

"""Unit tests for ovos_utils.smtp_utils module."""

import unittest
from unittest.mock import MagicMock, patch


class TestSendSmtp(unittest.TestCase):
    """Tests for the send_smtp function."""

    @patch("ovos_utils.smtp_utils.SMTP_SSL")
    def test_send_smtp_calls_login_and_sendmail(self, mock_smtp_ssl: MagicMock) -> None:
        """send_smtp should login, build the message, and call sendmail."""
        from ovos_utils.smtp_utils import send_smtp

        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_ssl.return_value.__exit__ = MagicMock(return_value=False)

        send_smtp(
            user="user@example.com",
            pswd="secret",
            sender="sender@example.com",
            destinatary="dest@example.com",
            subject="Test Subject",
            contents="Hello World",
            host="smtp.example.com",
            port=465,
        )

        mock_smtp_ssl.assert_called_once_with(host="smtp.example.com", port=465)
        mock_server.login.assert_called_once_with("user@example.com", "secret")
        self.assertTrue(mock_server.sendmail.called)

    @patch("ovos_utils.smtp_utils.SMTP_SSL")
    def test_send_smtp_default_port(self, mock_smtp_ssl: MagicMock) -> None:
        """send_smtp should use port 465 as the default."""
        from ovos_utils.smtp_utils import send_smtp

        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_ssl.return_value.__exit__ = MagicMock(return_value=False)

        send_smtp("u", "p", "s", "d", "subj", "body", "host.example.com")
        mock_smtp_ssl.assert_called_once_with(host="host.example.com", port=465)


class TestSendEmail(unittest.TestCase):
    """Tests for the send_email function."""

    def test_send_email_raises_when_no_config(self) -> None:
        """send_email should raise KeyError when email config is missing."""
        from ovos_utils.smtp_utils import send_email

        with patch("ovos_utils.smtp_utils.LOG"):
            with patch.dict("sys.modules", {"ovos_config": None,
                                             "ovos_config.config": None}):
                # Empty config — no email section
                with patch("builtins.__import__", side_effect=ImportError):
                    with self.assertRaises(KeyError):
                        send_email("subj", "body")

    @patch("ovos_utils.smtp_utils.send_smtp")
    def test_send_email_uses_config(self, mock_send_smtp: MagicMock) -> None:
        """send_email should read from config when parameters are missing."""
        from ovos_utils.smtp_utils import send_email
        fake_config = {
            "email": {
                "smtp": {
                    "username": "user@test.com",
                    "password": "pass123",
                    "host": "mail.test.com",
                    "port": 587,
                },
                "recipient": "recv@test.com",
            }
        }

        config_mock = MagicMock()
        config_mock.read_mycroft_config.return_value = fake_config

        with patch("ovos_utils.smtp_utils.LOG"), \
             patch.dict("sys.modules", {"ovos_config": MagicMock(), "ovos_config.config": config_mock}):
            send_email("Hello", "Body", recipient="recv@test.com")

        # verify the args
        mock_send_smtp.assert_called_once_with(
            "user@test.com",
            "pass123",
            "user@test.com",
            "recv@test.com",
            "Hello",
            "Body",
            "mail.test.com",
            587,
        )



if __name__ == "__main__":
    unittest.main()
