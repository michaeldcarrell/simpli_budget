import json
import requests
from django.conf import settings


class Plaid:
    def __init__(self):
        self.base_url = 'https://production.plaid.com'
        self.__client_id = settings.PLAID_CLIENT_ID
        self.__secret = settings.PLAID_SECRET
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.link_token = None
        self.access_token = None

    def get_link_token(self, access_token: str = None):
        url = f'{self.base_url}/link/token/create'
        params = {
            'client_id': self.__client_id,
            'secret': self.__secret,
            'client_name': 'Simpli Budget',
            'user': {
                'client_user_id': 'custom_michael'
            },
            'products': ['transactions'],
            'country_codes': ['US'],
            'language': 'en'
        }
        # This allows for use of the link update
        if access_token is not None:
            params['access_token'] = access_token

        res = requests.request('POST', url, data=json.dumps(params), headers=self.headers)
        if res.status_code == 200:
            self.link_token = res.json()['link_token']
            if access_token is not None:
                return {
                    'success': True,
                    'token': self.link_token,
                    'token_type': 'item'
                }
            else:
                return {
                    'success': True,
                    'token': self.link_token,
                    'token_type': 'link'
                }
        else:
            return {
                'success': False,
                'code': res.status_code,
                'response_text': res.text
            }

    def public_token_exchange(self, public_token: str):
        url = f'{self.base_url}/item/public_token/exchange'
        params = {
            'client_id': self.__client_id,
            'secret': self.__secret,
            'public_token': public_token
        }
        res = requests.request('POST', url, data=json.dumps(params), headers=self.headers)
        if res.status_code == 200:
            self.access_token = res.json()['access_token']
            return {
                'success': True,
                'token': self.access_token
            }
        else:
            return {
                'success': False,
                'code': res.status_code,
                'response_text': res.text
            }