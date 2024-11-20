from json_database import JsonStorageXDG
from ovos_config.locations import get_xdg_cache_save_path


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
