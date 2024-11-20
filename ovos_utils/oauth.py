import time

import requests
from json_database import JsonStorageXDG
from oauthlib.oauth2 import WebApplicationClient
from ovos_config.locations import get_xdg_cache_save_path

from ovos_utils.log import LOG


class OAuthTokenDatabase(JsonStorageXDG):
    """ This helper class creates ovos-config-assistant/ovos-backend-manager compatible json databases
        This allows users to use oauth even when not using a backend"""

    def __init__(self):
        super().__init__("ovos_oauth", xdg_folder=get_xdg_cache_save_path())

    def add_token(self, token_id, token_data):
        self[token_id] = token_data

    def update_token(self, token_id, token_data):
        self.add_token(token_id, token_data)

    def get_token(self, token_id):
        return self.get(token_id)

    def delete_token(self, token_id):
        if token_id in self:
            self.pop(token_id)
            return True
        return False

    def total_tokens(self):
        return len(self)


class OAuthApplicationDatabase(JsonStorageXDG):
    """ This helper class creates ovos-config-assistant/ovos-backend-manager compatible json databases
        This allows users to use oauth even when not using a backend"""

    def __init__(self):
        super().__init__("ovos_oauth_apps", xdg_folder=get_xdg_cache_save_path())

    def add_application(self, oauth_service,
                        client_id, client_secret,
                        auth_endpoint, token_endpoint, callback_endpoint, scope,
                        shell_integration=True):
        self[oauth_service] = {"oauth_service": oauth_service,
                               "client_id": client_id,
                               "client_secret": client_secret,
                               "auth_endpoint": auth_endpoint,
                               "token_endpoint": token_endpoint,
                               "callback_endpoint": callback_endpoint,
                               "scope": scope,
                               "shell_integration": shell_integration}

    def get_application(self, oauth_service):
        return self.get(oauth_service)

    def update_application(self, oauth_service,
                           client_id, client_secret,
                           auth_endpoint, token_endpoint,
                           callback_endpoint, scope, shell_integration=True):
        self.add_application(oauth_service,
                             client_id, client_secret,
                             auth_endpoint, token_endpoint,
                             callback_endpoint, scope, shell_integration)

    def delete_application(self, oauth_service):
        if oauth_service in self:
            self.pop(oauth_service)
            return True
        return False

    def total_apps(self):
        return len(self)


def refresh_oauth_token(token_id):
    """
        Refresh Oauth token for token_idential token_id.

        Argument:
            token_id:   development credentials identifier

        Returns:
            json string containing token and additional information
    """
    # Load all needed data for refresh
    with OAuthApplicationDatabase() as db:
        app_data = db.get(token_id)
    with OAuthTokenDatabase() as db:
        token_data = db.get(token_id)

    if (app_data is None or
            token_data is None or 'refresh_token' not in token_data):
        LOG.warning("Token data doesn't contain a refresh token and "
                    "cannot be refreshed.")
        return

    refresh_token = token_data["refresh_token"]

    # Fall back to token endpoint if no specific refresh endpoint
    # has been set
    token_endpoint = app_data["token_endpoint"]

    client_id = app_data["client_id"]
    client_secret = app_data["client_secret"]

    # Perform refresh
    client = WebApplicationClient(client_id, refresh_token=refresh_token)
    uri, headers, body = client.prepare_refresh_token_request(token_endpoint)
    refresh_result = requests.post(uri, headers=headers, data=body,
                                   auth=(client_id, client_secret))

    if refresh_result.ok:
        new_token_data = refresh_result.json()
        # Make sure 'expires_at' entry exists in token
        if 'expires_at' not in new_token_data:
            new_token_data['expires_at'] = time.time() + token_data['expires_in']
        # Store token
        with OAuthTokenDatabase() as db:
            token_data.update(new_token_data)
            db.update_token(token_id, token_data)

    return token_data


def get_oauth_token(token_id, auto_refresh=True):
    """
        Get Oauth token for token_id

        Argument:
            token_id:   development credentials identifier
            auto_refresh: refresh expired tokens automatically

        Returns:
            json string containing token and additional information
    """
    if auto_refresh:
        expired = False
        with OAuthTokenDatabase() as db:
            token_data = db.get(token_id)
        if "expires_at" not in token_data:
            expired = True
        elif token_data["expires_at"] >= time.time():
            expired = True
        if expired:
            return refresh_oauth_token(token_id)
    return OAuthTokenDatabase().get_token(token_id)
