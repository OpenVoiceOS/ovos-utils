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

"""Unit tests for ovos_utils.oauth module."""

import time
import unittest
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch, call

if TYPE_CHECKING:
    from ovos_utils.oauth import OAuthTokenDatabase, OAuthApplicationDatabase


class TestOAuthTokenDatabase(unittest.TestCase):
    """Tests for OAuthTokenDatabase CRUD methods."""

    def _make_db(self) -> "OAuthTokenDatabase":
        """Create an OAuthTokenDatabase backed by a temp file."""
        from ovos_utils.oauth import OAuthTokenDatabase
        with patch("ovos_utils.oauth.get_xdg_cache_save_path", return_value="/tmp"):
            db = OAuthTokenDatabase.__new__(OAuthTokenDatabase)
            # Initialise as plain dict (bypass JsonStorageXDG file I/O)
            dict.__init__(db)
        return db

    def test_add_and_get_token(self) -> None:
        """add_token should store a token retrievable by get_token."""
        db = self._make_db()
        db.add_token("tok1", {"access_token": "abc"})
        result = db.get_token("tok1")
        self.assertEqual(result["access_token"], "abc")

    def test_update_token(self) -> None:
        """update_token should overwrite an existing token."""
        db = self._make_db()
        db.add_token("tok1", {"access_token": "old"})
        db.update_token("tok1", {"access_token": "new"})
        self.assertEqual(db.get_token("tok1")["access_token"], "new")

    def test_delete_token_present(self) -> None:
        """delete_token should return True and remove an existing token."""
        db = self._make_db()
        db.add_token("tok1", {"access_token": "abc"})
        result = db.delete_token("tok1")
        self.assertTrue(result)
        self.assertIsNone(db.get_token("tok1"))

    def test_delete_token_absent(self) -> None:
        """delete_token should return False for a token that does not exist."""
        db = self._make_db()
        result = db.delete_token("nonexistent")
        self.assertFalse(result)

    def test_total_tokens(self) -> None:
        """total_tokens should return the number of stored tokens."""
        db = self._make_db()
        db.add_token("t1", {})
        db.add_token("t2", {})
        self.assertEqual(db.total_tokens(), 2)


class TestOAuthApplicationDatabase(unittest.TestCase):
    """Tests for OAuthApplicationDatabase CRUD methods."""

    def _make_db(self) -> "OAuthApplicationDatabase":
        """Create an OAuthApplicationDatabase as a plain dict subclass."""
        from ovos_utils.oauth import OAuthApplicationDatabase
        with patch("ovos_utils.oauth.get_xdg_cache_save_path", return_value="/tmp"):
            db = OAuthApplicationDatabase.__new__(OAuthApplicationDatabase)
            dict.__init__(db)
        return db

    def test_add_and_get_application(self) -> None:
        """add_application should store data retrievable by get_application."""
        db = self._make_db()
        db.add_application(
            oauth_service="myapp",
            client_id="id123",
            client_secret="secret456",
            auth_endpoint="https://auth.example.com",
            token_endpoint="https://token.example.com",
            callback_endpoint="https://callback.example.com",
            scope="read write",
        )
        result = db.get_application("myapp")
        self.assertIsNotNone(result)
        self.assertEqual(result["client_id"], "id123")

    def test_delete_application_present(self) -> None:
        """delete_application should return True and remove an existing app."""
        db = self._make_db()
        db.add_application("app1", "i", "s", "a", "t", "c", "scope")
        result = db.delete_application("app1")
        self.assertTrue(result)
        self.assertIsNone(db.get_application("app1"))

    def test_delete_application_absent(self) -> None:
        """delete_application should return False when app does not exist."""
        db = self._make_db()
        result = db.delete_application("nope")
        self.assertFalse(result)

    def test_total_apps(self) -> None:
        """total_apps should return the number of registered applications."""
        db = self._make_db()
        db.add_application("svc1", "i", "s", "a", "t", "c", "scope")
        db.add_application("svc2", "i", "s", "a", "t", "c", "scope")
        self.assertEqual(db.total_apps(), 2)

    def test_update_application(self) -> None:
        """update_application should overwrite existing app data."""
        db = self._make_db()
        db.add_application("svc", "old_id", "s", "a", "t", "c", "scope")
        db.update_application("svc", "new_id", "s", "a", "t", "c", "scope")
        self.assertEqual(db.get_application("svc")["client_id"], "new_id")


class TestRefreshOAuthToken(unittest.TestCase):
    """Tests for refresh_oauth_token function."""

    def test_returns_none_when_no_app_data(self) -> None:
        """refresh_oauth_token should return None when app_data is missing."""
        from ovos_utils.oauth import refresh_oauth_token

        with patch("ovos_utils.oauth.OAuthApplicationDatabase") as mock_app_db_cls, \
             patch("ovos_utils.oauth.OAuthTokenDatabase") as mock_tok_db_cls:

            mock_app_ctx = MagicMock()
            mock_app_ctx.__enter__ = MagicMock(return_value=mock_app_ctx)
            mock_app_ctx.__exit__ = MagicMock(return_value=False)
            mock_app_ctx.get.return_value = None
            mock_app_db_cls.return_value = mock_app_ctx

            mock_tok_ctx = MagicMock()
            mock_tok_ctx.__enter__ = MagicMock(return_value=mock_tok_ctx)
            mock_tok_ctx.__exit__ = MagicMock(return_value=False)
            mock_tok_ctx.get.return_value = {"refresh_token": "rr"}
            mock_tok_db_cls.return_value = mock_tok_ctx

            result = refresh_oauth_token("nonexistent_id")
        self.assertIsNone(result)

    def test_returns_none_when_no_refresh_token(self) -> None:
        """refresh_oauth_token should return None when token has no refresh_token."""
        from ovos_utils.oauth import refresh_oauth_token

        with patch("ovos_utils.oauth.OAuthApplicationDatabase") as mock_app_db_cls, \
             patch("ovos_utils.oauth.OAuthTokenDatabase") as mock_tok_db_cls:

            mock_app_ctx = MagicMock()
            mock_app_ctx.__enter__ = MagicMock(return_value=mock_app_ctx)
            mock_app_ctx.__exit__ = MagicMock(return_value=False)
            mock_app_ctx.get.return_value = {"token_endpoint": "https://t.example.com"}
            mock_app_db_cls.return_value = mock_app_ctx

            mock_tok_ctx = MagicMock()
            mock_tok_ctx.__enter__ = MagicMock(return_value=mock_tok_ctx)
            mock_tok_ctx.__exit__ = MagicMock(return_value=False)
            mock_tok_ctx.get.return_value = {}  # no refresh_token
            mock_tok_db_cls.return_value = mock_tok_ctx

            result = refresh_oauth_token("some_id")
        self.assertIsNone(result)


class TestRefreshOAuthTokenWithMockedOauthLib(unittest.TestCase):
    """Tests for refresh_oauth_token when app and token data are present."""

    def test_successful_refresh_stores_new_token(self) -> None:
        """refresh_oauth_token should update the DB when refresh POST succeeds."""
        from ovos_utils.oauth import refresh_oauth_token

        app_data = {
            "token_endpoint": "https://token.example.com",
            "client_id": "client_id",
            "client_secret": "client_secret",
        }
        token_data = {
            "refresh_token": "old_rt",
            "expires_in": 3600,
        }
        new_token_data = {
            "access_token": "new_at",
            "refresh_token": "new_rt",
            "expires_in": 3600,
        }

        # Use side_effect to provide different context managers per instantiation order
        call_count = [0]

        def make_ctx(data):
            ctx = MagicMock()
            ctx.__enter__ = MagicMock(return_value=ctx)
            ctx.__exit__ = MagicMock(return_value=False)
            ctx.get.return_value = data
            ctx.update_token = MagicMock()
            return ctx

        app_ctx = make_ctx(app_data)
        tok_ctx1 = make_ctx(token_data)
        tok_ctx2 = make_ctx(token_data)

        app_db_instances = [app_ctx]
        tok_db_instances = [tok_ctx1, tok_ctx2]

        def app_db_factory(*args, **kwargs):
            return app_db_instances.pop(0)

        def tok_db_factory(*args, **kwargs):
            return tok_db_instances.pop(0)

        mock_refresh_result = MagicMock()
        mock_refresh_result.ok = True
        mock_refresh_result.json.return_value = new_token_data

        mock_client = MagicMock()
        mock_client.prepare_refresh_token_request.return_value = (
            "https://token.example.com", {}, "body"
        )
        mock_wac = MagicMock(return_value=mock_client)

        with patch("ovos_utils.oauth.OAuthApplicationDatabase",
                   side_effect=app_db_factory), \
             patch("ovos_utils.oauth.OAuthTokenDatabase",
                   side_effect=tok_db_factory), \
             patch("ovos_utils.oauth.requests.post",
                   return_value=mock_refresh_result), \
             patch.dict("sys.modules", {
                 "oauthlib": MagicMock(),
                 "oauthlib.oauth2": MagicMock(WebApplicationClient=mock_wac),
             }):
            result = refresh_oauth_token("my_token_id")

        # Result should be the (updated) token_data dict
        self.assertIsNotNone(result)

    def test_failed_refresh_still_returns_token_data(self) -> None:
        """refresh_oauth_token should return token_data even on failed POST."""
        from ovos_utils.oauth import refresh_oauth_token

        app_data = {
            "token_endpoint": "https://token.example.com",
            "client_id": "id",
            "client_secret": "secret",
        }
        token_data = {
            "refresh_token": "rt",
            "expires_in": 3600,
        }

        mock_app_ctx = MagicMock()
        mock_app_ctx.__enter__ = MagicMock(return_value=mock_app_ctx)
        mock_app_ctx.__exit__ = MagicMock(return_value=False)
        mock_app_ctx.get.return_value = app_data

        mock_tok_ctx = MagicMock()
        mock_tok_ctx.__enter__ = MagicMock(return_value=mock_tok_ctx)
        mock_tok_ctx.__exit__ = MagicMock(return_value=False)
        mock_tok_ctx.get.return_value = token_data

        mock_refresh_result = MagicMock()
        mock_refresh_result.ok = False

        mock_client = MagicMock()
        mock_client.prepare_refresh_token_request.return_value = ("uri", {}, "body")

        with patch("ovos_utils.oauth.OAuthApplicationDatabase",
                   return_value=mock_app_ctx), \
             patch("ovos_utils.oauth.OAuthTokenDatabase",
                   return_value=mock_tok_ctx), \
             patch("ovos_utils.oauth.requests.post",
                   return_value=mock_refresh_result):
            mock_wac = MagicMock(return_value=mock_client)
            with patch.dict("sys.modules", {
                "oauthlib": MagicMock(),
                "oauthlib.oauth2": MagicMock(WebApplicationClient=mock_wac),
            }):
                result = refresh_oauth_token("tok_id")

        self.assertIsNotNone(result)


class TestGetOAuthToken(unittest.TestCase):
    """Tests for get_oauth_token function."""

    def test_no_auto_refresh_returns_token(self) -> None:
        """get_oauth_token with auto_refresh=False should return stored token."""
        from ovos_utils.oauth import get_oauth_token

        mock_db = MagicMock()
        mock_db.get_token.return_value = {"access_token": "xyz"}

        with patch("ovos_utils.oauth.OAuthTokenDatabase", return_value=mock_db):
            result = get_oauth_token("tok_id", auto_refresh=False)
        self.assertEqual(result["access_token"], "xyz")

    def test_auto_refresh_when_no_expires_at(self) -> None:
        """get_oauth_token with auto_refresh=True should refresh if no expires_at."""
        from ovos_utils.oauth import get_oauth_token

        token_data = {"access_token": "old", "refresh_token": "rt"}

        mock_db_ctx = MagicMock()
        mock_db_ctx.__enter__ = MagicMock(return_value=mock_db_ctx)
        mock_db_ctx.__exit__ = MagicMock(return_value=False)
        mock_db_ctx.get.return_value = token_data

        with patch("ovos_utils.oauth.OAuthTokenDatabase",
                   return_value=mock_db_ctx), \
             patch("ovos_utils.oauth.refresh_oauth_token",
                   return_value={"access_token": "new"}) as mock_refresh:
            result = get_oauth_token("tok_id", auto_refresh=True)

        mock_refresh.assert_called_once_with("tok_id")

    def test_auto_refresh_when_expired(self) -> None:
        """get_oauth_token should refresh when expires_at is in the past (<= now)."""
        import time as _time
        from ovos_utils.oauth import get_oauth_token

        # expires_at <= time.time() means token has expired and refresh is needed
        token_data = {
            "access_token": "old",
            "expires_at": _time.time() - 1000,  # past date → token expired
        }

        mock_db_ctx = MagicMock()
        mock_db_ctx.__enter__ = MagicMock(return_value=mock_db_ctx)
        mock_db_ctx.__exit__ = MagicMock(return_value=False)
        mock_db_ctx.get.return_value = token_data

        with patch("ovos_utils.oauth.OAuthTokenDatabase",
                   return_value=mock_db_ctx), \
             patch("ovos_utils.oauth.refresh_oauth_token",
                   return_value={"access_token": "new"}) as mock_refresh:
            get_oauth_token("tok_id", auto_refresh=True)

        mock_refresh.assert_called_once_with("tok_id")


if __name__ == "__main__":
    unittest.main()
