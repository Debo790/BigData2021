import argparse
import time
from typing import List
import geopandas as gpd
import numpy as np
from osm2geojson.helpers import overpass_call
from osm2geojson.main import json2geojson
from shapely.geometry import Polygon
import requests
import json
from strava_auth import StravaAuth


# Get coordinates for the envelope of the requested area
# Returns a list with xmin, ymin, xmax, ymax
def get_coords(boundary, city: int) -> List:
        env = boundary.geometry[city].envelope
        g = [i for i in env.exterior.coords]
        coords = []
        coords.append(g[0][1])  # lower bound x
        coords.append(g[0][0])  # lower bound y
        coords.append(g[2][1])  # upper bound x
        coords.append(g[2][0])  # upper bound y
        print(coords)
        return coords

def tooMany(activity: set) -> bool:
    if len(activity)==10:
        return True
    else: 
        return False

class StravaExtractor:
    def __init__(self, city: List) -> None:
        self.city = city
        self.boundary = gpd.GeoDataFrame()
        self.grid = None
        self.runs = set()
        self.rides = set()

    def reduce_boundary(self, city: int):
        coords = get_coords(self.boundary, city)
        xmin = coords[0]
        ymin = coords[1]
        xmax = coords[2]
        ymax = coords[3]
        length = round((ymax-ymin)/8, 4)
        wide = round((xmax-xmin)/8, 4)

        cols = list(np.arange(xmin, xmax, wide))
        rows = list(np.arange(ymin, ymax, length))

        polygons = []
        for x in cols[:-1]:
            for y in rows[:-1]:
                polygons.append(Polygon([(x,y), (x+wide, y), (x+wide, y+length), (x, y+length)]))

        self.grid = gpd.GeoDataFrame({'geometry':polygons})
        print("Reduced.")

    def get_boundary(self, city: str):

        print("Getting boundaries for {}".format(city))

        query = '''
            [out:json];
            area[name="{}"][admin_level=8][boundary=administrative]->.target;
            area["name"="Italia"][boundary=administrative]->.wrap;
            rel(pivot.target)(area.wrap);

            out geom;
        '''.format(city)

        ti = time.time()
        
        result = overpass_call(query)
        res = json2geojson(result)
        self.boundary = self.boundary.append(gpd.GeoDataFrame.from_features(res), ignore_index=True)
        
        if len(self.boundary) <= 0:
            raise ConnectionError("No boundaries were found for {}. Try with another city or check your Overpass query limit.".format(city))
        else:
            tf = time.time()
            print("Extracted boundaries for {}. Time elapsed: {} s".format(city, round(tf-ti, 2)))        
    

    def get_segments(self, auth: StravaAuth, activity_type: str, city: int, grid: bool) -> bool:

        print("Searching for {} segments...".format(activity_type))
        if grid:
            
            coords = get_coords(self.grid, city)    
        else: 
            coords = get_coords(self.boundary, city)
        bounds = "{},{},{},{}".format(coords[0], coords[1],coords[2], coords[3])
        
        params = {'activity_type':activity_type, 'bounds': bounds}
        r = open('conf/auth.json','r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}
        req = requests.get("https://www.strava.com/api/v3/segments/explore?", params = params, headers=headers).json()
        
        # Debug
        #print(req.url)
        print("grid {}, {} segments found".format(city, len(req)))
        
        if activity_type == "running":
            if len(req)>0:
                for i in range(len(req["segments"])):
                    self.runs.add(req["segments"][i]["id"])
        #    with open('tmp/running.json', 'w') as f:
        #        json.dump(req.json(), f, indent=4)
        else:
            if len(req)>0:
                for i in range(len(req["segments"])):
                    self.rides.add(req["segments"][i]["id"])
        #    with open('tmp/riding.json', 'w') as f:
        #        json.dump(req.json(), f, indent=4)
        if len(req["segments"])==10:
            return True
        else:
            return False
    
    def run(self) -> bool:
        # Check for access_token, updating it if expired
        auth = StravaAuth()
        #print(auth.token())
        for city in self.city:
            self.get_boundary(city)
            ti = time.time()
            count = self.get_segments(auth, "running", self.city.index(city), False)
            if count:
                self.reduce_boundary(self.city.index(city))
                for i in range(len(self.grid)):
                    self.get_segments(auth, "running", i, True)
            print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runs), city, round(ti-time.time(), 2)))
            ti = time.time()
            self.get_segments(auth, "riding", self.city.index(city), False)
            if count:
                self.reduce_boundary(self.city.index(city))
                for i in range(len(self.grid)):
                    self.get_segments(auth, "riding", i, True)
            print("Found {} riding segments for {}. Time elapsed: {} s".format(len(self.rides), city, round(ti-time.time(), 2)))
            print("Waiting 10s to not overload Overpass...")
            time.sleep(10)
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDT Project 2021 - Strava data extraction")
    parser.add_argument("--city", nargs='+', type=str, help="The city to extract", required=True)

    args = parser.parse_args()

    city = args.city

    ce = StravaExtractor(city)
    success = ce.run()

    if success:
        print("Done.")