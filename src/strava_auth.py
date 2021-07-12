import json
from time import time
import requests
import configparser
import sys
import os
sys.path.append(os.getcwd())

class StravaAuth:
    
    def __init__(self, user: str):

        self.user = user

        f = open("conf/auth_{}.json".format(user), "r")
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
        secret = config['strava{}'.format(self.user)]['client_secret']
        id = config['strava{}'.format(self.user)]['id']
        
        params = {'client_id':id,
        'client_secret':secret,
        'grant_type':'refresh_token',
        'refresh_token':refresh_token}
        req = requests.post("https://www.strava.com/oauth/token?", params=params)
        #print(req.url)
        with open('conf/auth_{}.json'.format(self.user), 'w') as f:
            json.dump(req.json(), f, indent=4)
        print("Access token updated.")

    def token(self)-> str:
        return self.access_token

    
if __name__ == "__main__":
    StravaAuth("1")