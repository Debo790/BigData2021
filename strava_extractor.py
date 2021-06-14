import argparse
import time
from typing import List
import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame
from osm2geojson.helpers import overpass_call
from osm2geojson.main import json2geojson
from shapely import affinity
import requests
import json
from strava_auth import StravaAuth



def get_coords(boundary: GeoDataFrame) -> List:
        env = boundary.geometry[0].envelope
        g = [i for i in env.exterior.coords]
        coords = []
        coords.append(g[0][0])  # lower bound x
        coords.append(g[0][1])  # lower bound y
        coords.append(g[2][0])  # upper bound x
        coords.append(g[2][1])  # upper bound y
        print(coords)
        return coords

class StravaExtractor:
    def __init__(self, city: str) -> None:
        self.city = city
        self.boundary = None

    def get_boundary(self):

        print("Getting boundaries for {}".format(self.city))

        query = '''
            [out:json];
            area[name="{}"][admin_level=8][boundary=administrative]->.target;
            area["name"="Italia"][boundary=administrative]->.wrap;
            rel(pivot.target)(area.wrap);

            out geom;
        '''.format(self.city)

        ti = time.time()
        
        result = overpass_call(query)
        res = json2geojson(result)
        self.boundary = gpd.GeoDataFrame.from_features(res)
        
        if len(self.boundary) <= 0:
            raise ConnectionError("No boundaries were found for {}. Try with another city or check your Overpass query limit.".format(self.city))
        else:
            tf = time.time()
            print("Extracted boundaries for {}. Time elapsed: {} s".format(self.city, round(tf-ti, 2)))        
    
    def get_segments(self, auth: StravaAuth, activity_type: str):
        print("Searching for {} segments...".format(activity_type))
        coords = get_coords(self.boundary)
        bounds = "{},{},{},{}".format(coords[1], coords[0],coords[3], coords[2])
        params = {'activity_type':activity_type, 'bounds': bounds}
        r = open('conf/auth.json','r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}
        req = requests.get("https://www.strava.com/api/v3/segments/explore?", params = params, headers=headers)
        # Debug
        print(req.url)
        if activity_type == "running":
            with open('tmp/running.json', 'w') as f:
                json.dump(req.json(), f, indent=4)
        else:
            with open('tmp/riding.json', 'w') as f:
                json.dump(req.json(), f, indent=4)
    
    def run(self) -> bool:
        auth = StravaAuth()
        #print(auth.token())
        self.get_boundary()
        ti = time.time()
        self.get_segments(auth, "running")
        print("Found running segments for {}. Time elapsed: {} s".format(self.city, round(ti-time.time(), 2)))
        ti = time.time()
        self.get_segments(auth, "riding")
        print("Found riding segments for {}. Time elapsed: {} s".format(self.city, round(ti-time.time(), 2)))
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDT Project 2021 - Strava data extraction")
    parser.add_argument("--city", type=str, help="The city to extract", required=True)

    args = parser.parse_args()

    city = args.city

    ce = StravaExtractor(city)
    success = ce.run()

    if success:
        print("Done.")