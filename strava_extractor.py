import argparse
import sys
import time
from typing import List
import geopandas as gpd
import numpy as np
import pandas as pd
from osm2geojson.helpers import overpass_call
from osm2geojson.main import json2geojson
import shapely.geometry as shp
import requests
import json
import polyline
from strava_auth import StravaAuth
from db_wrapper import PostgresDB


query_counter = 0


# Get coordinates for the envelope of the requested area
# Returns a list with xmin, ymin, xmax, ymax
def get_coords(boundary: gpd.GeoDataFrame, city: int) -> List:
    env = boundary.geometry[city].envelope
    g = [i for i in env.exterior.coords]
    coords = []
    if g[0][1] > g[0][0]:
        coords.append(g[0][1])  # lower bound x
        coords.append(g[0][0])  # lower bound y
        coords.append(g[2][1])  # upper bound x
        coords.append(g[2][0])  # upper bound y
    else: 
        coords.append(g[0][0])  # lower bound x
        coords.append(g[0][1])  # lower bound y
        coords.append(g[2][0])  # upper bound x
        coords.append(g[2][1])  # upper bound y

    #print(coords)
    return coords

# Get query count, wait if exceeded
# Limits: 100 queries every 15 mins, 1000 daily
def count_check():
    global query_counter
    if query_counter==1000:
        print("Query daily limit exceeded.")
        sys.exit(0)
    if query_counter%100==0:
        for i in range(15):
            print("Waiting for Strava to update query limit, {} minutes to restart...".format(i))
            time.sleep(60)


class StravaExtractor:


    def __init__(self, city: List) -> None:
        self.city = city
        self.boundary = gpd.GeoDataFrame()
        self.runs = set()
        self.rides = set()
        self.runsData = None
        self.ridesData = None
        self.segments = gpd.GeoDataFrame()
        self.db = PostgresDB()


    def reduce_boundary(self, boundary: gpd.GeoDataFrame, city: int) -> gpd.GeoDataFrame:
        coords = get_coords(boundary, city)
        xmin = coords[0]
        ymin = coords[1]
        xmax = coords[2]
        ymax = coords[3]
        length = round((ymax-ymin)/4, 4)
        wide = round((xmax-xmin)/4, 4)

        cols = list(np.arange(xmin, xmax, wide))
        rows = list(np.arange(ymin, ymax, length))

        polygons = []
        for x in cols[:-1]:
            for y in rows[:-1]:
                polygons.append(shp.Polygon([(x,y), (x+wide, y), (x+wide, y+length), (x, y+length)]))

        print("Boundary reduced.")
        return gpd.GeoDataFrame({'geometry':polygons})
        

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
            print("Extracted boundaries for {}. Time elapsed: {} s".format(city, round(time.time()-ti, 2)))        
    

    def get_runs_data(self):

        global query_counter

        r = open('conf/auth.json','r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}

        cols = ['id', 'name', 'activity_type', 'effort_count', 'athlete_count', 'distance', 'average_grade', 
        'maximum_grade', 'elevation_high', 'elevation_low', 'total_elevation_gain', 'polyline']
        self.runsData = pd.DataFrame(columns=cols)
        index = 0
        for segmentId in self.runs:
            req = requests.get("https://www.strava.com/api/v3/segments/{}".format(segmentId), headers=headers).json()
            self.runsData.loc[index] = np.array([req["id"], req["name"], req["activity_type"], req["effort_count"], req["athlete_count"], 
                req["distance"], req["average_grade"], req["maximum_grade"], req["elevation_high"], 
                req["elevation_low"], req["total_elevation_gain"], req["map"]["polyline"]])
            index = index+1
            print(req["id"])

            # Query limit counter
            count_check()
            print("Query counter: {}".format(query_counter))
            query_counter = query_counter+1 


    def get_rides_data(self):

        global query_counter

        r = open('conf/auth.json','r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}

        cols = ['id', 'name', 'activity_type', 'effort_count', 'athlete_count', 'distance', 'average_grade', 
        'maximum_grade', 'elevation_high', 'elevation_low', 'total_elevation_gain', 'polyline']
        self.ridesData = pd.DataFrame(columns=cols)
        index = 0
        for segmentId in self.rides:
            req = requests.get("https://www.strava.com/api/v3/segments/{}".format(segmentId), headers=headers).json()
            self.ridesData.loc[index] = np.array([req["id"], req["name"], req["activity_type"], req["effort_count"], req["athlete_count"], 
                req["distance"], req["average_grade"], req["maximum_grade"], req["elevation_high"], 
                req["elevation_low"], req["total_elevation_gain"], req["map"]["polyline"]])
            index = index+1
            
            # Query limit counter
            count_check()
            print("Query counter: {}".format(query_counter))
            query_counter = query_counter+1 


    def decode_polyline(self, segments: pd.DataFrame) -> gpd.GeoDataFrame:
        segments["geometry"] = None
        for i in range(len(segments)):
            pointList = polyline.decode(segments.loc[i,"polyline"])
            poly = shp.LineString([[p[0], p[1]] for p in pointList])
            segments.loc[i,"geometry"] = poly
        segments = segments.drop(columns=["polyline"])
        segments = gpd.GeoDataFrame(segments)
        segments = segments.set_crs(epsg=4326)
        return segments


    def get_segments(self, currentBoundary: gpd.GeoDataFrame, activity_type: str, city: int, grid: bool):

        global query_counter

        print("Searching for {} segments...".format(activity_type))
        if grid:
            coords = get_coords(currentBoundary, city)    
            bounds = "{},{},{},{}".format(coords[0], coords[1],coords[2], coords[3])
        else: 
            coords = get_coords(self.boundary, city)
            bounds = "{},{},{},{}".format(coords[0], coords[1],coords[2], coords[3])
        
        params = {'activity_type':activity_type, 'bounds': bounds}
        r = open('conf/auth.json','r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}
        req = requests.get("https://www.strava.com/api/v3/segments/explore?", params = params, headers=headers)
        
        # Query limit counter
        count_check()
        print("Query counter: {}".format(query_counter))
        query_counter = query_counter+1 

        # Debug
        print(req.url)
        req = req.json()
        
        
        if activity_type == "running":
            if len(req)>0:
                print("grid {}, {} segments found".format(city, len(req["segments"])))
                print("-----------------")
                for i in range(len(req["segments"])):
                    self.runs.add(req["segments"][i]["id"])
                    with open('tmp/running.json', 'a') as f:
                        json.dump(req, f, indent=4)
                if len(req["segments"])==10:
                    newBoundary = self.reduce_boundary(currentBoundary, city)
                    for i in range(len(newBoundary)):
                        self.get_segments(newBoundary, "running", i, True)
        else:
            if len(req)>0:
                print("grid {}, {} segments found".format(city, len(req["segments"])))
                print("-----------------")
                for i in range(len(req["segments"])):
                    self.rides.add(req["segments"][i]["id"])
                    with open('tmp/riding.json', 'a') as f:
                        json.dump(req, f, indent=4)
                if len(req["segments"])==10:
                    newBoundary = self.reduce_boundary(currentBoundary, city)
                    for i in range(len(newBoundary)):
                        self.get_segments(newBoundary, "riding", i, True)


    def load(self, segments: gpd.GeoDataFrame, city: str):
        #Upload to DB
        ti = time.time()
        print("Uploading to DB entries for {}...".format(city))
        self.db.insert_gdf(segments, "segments")
        print("Segments uploaded for {}. Time elapsed: {} s".format(city, round(time.time()-ti, 2)))


    def run(self, activity_type:str) -> bool:
        # Check for access_token, updating it if expired
        auth = StravaAuth()
        
        # Starting query counter (needed to deal with Strava query limit)
        global query_counter
        query_counter = query_counter+2     # 2 requests -> worst case scenario (expired token)
        
        for city in self.city:
            self.get_boundary(city)
            if activity_type == "running":
                ti = time.time()
                self.get_segments(self.boundary, activity_type, self.city.index(city), False)
                print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runs), city, round(time.time()-ti, 2)))
                self.get_runs_data()
                print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runsData), city, round(time.time()-ti, 2)))
                self.segments = self.decode_polyline(self.runsData)
                self.load(self.segments, city)
            elif activity_type == "riding":
                ti = time.time()
                self.get_segments(self.boundary, activity_type, self.city.index(city), False)
                print("Found {} riding segments for {}. Time elapsed: {} s".format(len(self.rides), city, round(time.time()-ti, 2)))
                self.get_rides_data()
                print("Found {} riding segments for {}. Time elapsed: {} s".format(len(self.ridesData), city, round(time.time()-ti, 2)))
                self.segments = self.decode_polyline(self.ridesData)
                self.load(self.segments, city)
            else:
                ti = time.time()
                self.get_segments(self.boundary, "running", self.city.index(city), False)
                print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runs), city, round(time.time()-ti, 2)))
                self.get_runs_data()
                print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runsData), city, round(time.time()-ti, 2)))
                self.segments = self.decode_polyline(self.runsData)
                self.load(self.segments, city)
                ti = time.time()
                self.get_segments(self.boundary, "riding", self.city.index(city), False)
                print("Found {} riding segments for {}. Time elapsed: {} s".format(len(self.rides), city, round(time.time()-ti, 2)))
                self.get_rides_data()
                print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.ridesData), city, round(time.time()-ti, 2)))
                self.segments = self.decode_polyline(self.ridesData)
                self.load(self.segments, city)

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDT Project 2021 - Strava data extraction")
    parser.add_argument("--city", nargs='+', type=str, help="The city/cities to search for", required=True)
    parser.add_argument("--activity", type=str, help="Activity type to search (running/riding/all) [Default: running]", default="running")

    args = parser.parse_args()

    city = args.city
    activity_type = args.activity

    if activity_type not in ["running", "riding", "all"]:
        print("ACTIVITY ERROR: Please, insert a supported activity (running/riding/all)")
        sys.exit(0)

    ce = StravaExtractor(city)
    success = ce.run(activity_type)

    if success:
        print("Done.")