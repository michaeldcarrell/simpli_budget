import os

class Plaid:
    def __init__(self, access_token: str = None, public_token: str = None, last_load_date: str = None,
                 user_id: str = None):
        self.access_token = access_token
        self.public_token = public_token
        self.base_url = 'https://production.plaid.com'
        self.__client_id = os.environ['PLAID_CLIENT_ID']
        self.__secret = os.environ['PLAID_SECRET']
        self.headers = {
            'Content-Type': 'application/json'
        }
        self.link_token = None
        self.last_load_date = last_load_date
        self.user_id = user_id
        self.__server = 'cba.database.windows.net'
        self.__database = 'cba'

    def get_link_token(self, access_token: str):
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