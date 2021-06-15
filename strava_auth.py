import json
from time import time
import requests
import configparser

class StravaAuth:
    
    def __init__(self):
        f = open("conf/auth.json", "r")
        auth = json.load(f)
        if auth["expires_at"] > time():
            self.token_type = auth["token_type"]
            self.access_token = auth["access_token"]
            self.refresh_token = auth["refresh_token"]
            self.expiresAt = auth["expires_at"]
        else:
            #print(auth["refresh_token"])
            self.update(auth["refresh_token"])
        
    def update(self, refresh_token):
        
        print("Access token expired. Refreshing...")
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        secret = config['strava']['client_secret']
        id = config['strava']['id']
        
        params = {'client_id':id,
        'client_secret':secret,
        'grant_type':'refresh_token',
        'refresh_token':refresh_token}
        req = requests.post("https://www.strava.com/oauth/token?", params=params)
        #print(req.url)
        with open('conf/auth.json', 'w') as f:
            json.dump(req.json(), f, indent=4)
        print("Access token updated.")

    def token(self)-> str:
        return self.access_token

    
if __name__ == "__main__":
    StravaAuth()