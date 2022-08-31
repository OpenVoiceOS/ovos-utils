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


class OvosWeather:
    def __init__(self):
        self.api = OVOSApiService()

    @property
    def uuid(self):
        return self.api.get_uuid()

    @property
    def headers(self):
        self.api.get_session_challenge()
        return {'session_challenge': self.api.get_session_token(),  'backend': 'OWM'}

    def get_weather_onecall(self, query):
        reqdata = {"lat": query.get("lat"),
                   "lon": query.get("lon"),
                   "units": query.get("units"),
                   "lang": query.get("lang")}
        url = f'https://api.openvoiceos.com/weather/onecall_weather_report/{self.uuid}'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r.json()

class OvosWolframAlpha:
    def __init__(self):
        self.api = OVOSApiService()

    @property
    def uuid(self):
        return self.api.get_uuid()

    @property
    def headers(self):
        self.api.get_session_challenge()
        return {'session_challenge': self.api.get_session_token()}

    def get_wolfram_spoken(self, query):
        reqdata = {"input": query.get("input"),
                   "units": query.get("units")}
        url = f'https://api.openvoiceos.com/wolframalpha/spoken/{self.uuid}'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r
    
    def get_wolfram_simple(self, query):
        reqdata = {"input": query.get("input"),
                   "units": query.get("units")}
        url = f'https://api.openvoiceos.com/wolframalpha/simple/{self.uuid}'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r
    
    def get_wolfram_full(self, query):
        reqdata = {"input": query.get("input"),
                   "units": query.get("units")}
        url = f'https://api.openvoiceos.com/wolframalpha/full/{self.uuid}'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r.json()

class OvosEdamamRecipe:
    def __init__(self):
        self.api = OVOSApiService()
        
    @property
    def uuid(self):
        return self.api.get_uuid()

    @property
    def headers(self):
        self.api.get_session_challenge()
        return {'session_challenge': self.api.get_session_token()}
    
    def get_recipe(self, query):
        reqdata = {"query": query.get("query"),
                   "count": query.get("count", 5)}
        url = f'https://api.openvoiceos.com/recipes/search_recipe/'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r.json()
    
class OvosOmdb:
    def __init__(self):
        self.api = OVOSApiService()
        
    @property
    def uuid(self):
        return self.api.get_uuid()
    
    @property
    def headers(self):
        self.api.get_session_challenge()
        return {'session_challenge': self.api.get_session_token()}

    def search_movie(self, query):
        reqdata = {"movie_name": query.get("movie_name"),
                   "movie_year": query.get("movie_year"),
                   "movie_id": query.get("movie_id")}
        
        url = f'https://api.openvoiceos.com/omdb/search_movie/'
        r = requests.post(url, data=reqdata, headers=self.headers)
        return r.json()