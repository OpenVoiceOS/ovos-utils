import json
import requests
from json_database import JsonStorageXDG


class OVOSApiService:

    def __init__(self) -> None:
        self.uuid_storage = JsonStorageXDG("ovos_api_uuid")
        self.token_storage = JsonStorageXDG("ovos_api_token")

    def register_device(self):
        if self.check_if_uuid_exists():
            return
        else:
            created_challenge = requests.get('https://api.openvoiceos.com/create_challenge')
            challenge_response = created_challenge.json()
            register_device = requests.get('https://api.openvoiceos.com/register_device/' + challenge_response['challenge'] + '/' + challenge_response['secret'])
            register_device_uuid = challenge_response['challenge']
            self.uuid_storage['uuid'] = register_device_uuid
            self.uuid_storage.store()

    def check_if_uuid_exists(self):
        if "uuid" in self.uuid_storage:
            return True
        return False

    def get_session_challenge(self):
        session_challenge_request = requests.get('https://api.openvoiceos.com/get_session_challenge')
        session_challenge_response = session_challenge_request.json()
        self.token_storage["challenge"] = session_challenge_response['challenge']
        self.token_storage.store()

    def get_uuid(self):
        return self.uuid_storage.get("uuid", "")

    def get_session_token(self):
        return self.token_storage.get("challenge", "")
