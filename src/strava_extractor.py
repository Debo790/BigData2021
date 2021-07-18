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
import redis
import sys
import os
sys.path.append(os.getcwd())
import strava_auth
import db_wrapper

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
        for i in range(16):
            print("Waiting for Strava to update query limit, {} minutes to restart...".format(15-i))
            time.sleep(60)


class StravaExtractor:


    def __init__(self, city: List, r: redis.Redis, user: str) -> None:
        self.city = city
        self.boundary = gpd.GeoDataFrame()
        self.runs = set()
        self.rides = set()
        self.runsData = None
        self.ridesData = None
        self.db = db_wrapper.PostgresDB()
        self.r = r
        self.user = user


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
    

    def get_runs_data(self, city: str, consumer: bool):

        global query_counter

        r = open('conf/auth_{}.json'.format(self.user),'r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}

        cols = ['id', 'name', 'activity_type', 'effort_count', 'athlete_count', 'distance', 'average_grade', 
        'maximum_grade', 'elevation_high', 'elevation_low', 'total_elevation_gain', 'polyline']
        self.runsData = pd.DataFrame(columns=cols)
        index = 0
        if consumer:
            for i in self.r.smembers("strava:running:code"):
                req = requests.get("https://www.strava.com/api/v3/segments/{}".format(i.decode("utf-8")), headers=headers).json()
                self.runsData.loc[index] = np.array([req["id"], req["name"], req["activity_type"], req["effort_count"], req["athlete_count"], 
                    req["distance"], req["average_grade"], req["maximum_grade"], req["elevation_high"], 
                    req["elevation_low"], req["total_elevation_gain"], req["map"]["polyline"]])
                index = index+1
                self.r.srem("strava:running:code", i.decode("utf-8"))
                # Query limit counter
                count_check()
                if query_counter%50==0:
                    print("Query counter: {}".format(query_counter))
                query_counter = query_counter+1 
        else: 
            for segmentId in self.runs:
                req = requests.get("https://www.strava.com/api/v3/segments/{}".format(segmentId), headers=headers).json()
                self.runsData.loc[index] = np.array([req["id"], req["name"], req["activity_type"], req["effort_count"], req["athlete_count"], 
                    req["distance"], req["average_grade"], req["maximum_grade"], req["elevation_high"], 
                    req["elevation_low"], req["total_elevation_gain"], req["map"]["polyline"]])
                index = index+1
                self.r.srem("strava:running:code", segmentId)
                # Query limit counter
                count_check()
                if query_counter%50==0:
                    print("Query counter: {}".format(query_counter))
                query_counter = query_counter+1 

        self.runsData["city"] = city


    def get_rides_data(self, city: str, consumer: bool):

        global query_counter

        r = open('conf/auth_{}.json'.format(self.user),'r')
        auth = json.load(r)
        headers = {'Authorization':auth["token_type"]+ " " + auth["access_token"]}

        cols = ['id', 'name', 'activity_type', 'effort_count', 'athlete_count', 'distance', 'average_grade', 
        'maximum_grade', 'elevation_high', 'elevation_low', 'total_elevation_gain', 'polyline']
        self.ridesData = pd.DataFrame(columns=cols)
        index = 0
        if consumer:
            for i in self.r.smembers("strava:riding:code"):
                req = requests.get("https://www.strava.com/api/v3/segments/{}".format(i.decode("utf-8")), headers=headers).json()
                self.ridesData.loc[index] = np.array([req["id"], req["name"], req["activity_type"], req["effort_count"], req["athlete_count"], 
                    req["distance"], req["average_grade"], req["maximum_grade"], req["elevation_high"], 
                    req["elevation_low"], req["total_elevation_gain"], req["map"]["polyline"]])
                index = index+1
                self.r.srem("strava:riding:code", i.decode("utf-8"))
                # Query limit counter
                count_check()
                if query_counter%50==0:
                    print("Query counter: {}".format(query_counter))
                query_counter = query_counter+1 
        else:
            for segmentId in self.rides:
                req = requests.get("https://www.strava.com/api/v3/segments/{}".format(segmentId), headers=headers).json()
                self.ridesData.loc[index] = np.array([req["id"], req["name"], req["activity_type"], req["effort_count"], req["athlete_count"], 
                    req["distance"], req["average_grade"], req["maximum_grade"], req["elevation_high"], 
                    req["elevation_low"], req["total_elevation_gain"], req["map"]["polyline"]])
                index = index+1
                self.r.srem("strava:riding:code", segmentId)
                # Query limit counter
                count_check()
                if query_counter%50==0:
                    print("Query counter: {}".format(query_counter))
                query_counter = query_counter+1 
        
        self.ridesData["city"] = city


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
        r = open('conf/auth_{}.json'.format(self.user),'r')
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
                    self.r.sadd("strava:running:code", req["segments"][i]["id"])
                    # with open('tmp/running.json', 'a') as f:
                    #     json.dump(req, f, indent=4)
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
                    self.r.sadd("strava:riding:code", req["segments"][i]["id"])
                    # with open('tmp/riding.json', 'a') as f:
                    #     json.dump(req, f, indent=4)
                if len(req["segments"])==10:
                    newBoundary = self.reduce_boundary(currentBoundary, city)
                    for i in range(len(newBoundary)):
                        self.get_segments(newBoundary, "riding", i, True)


    def load(self, segments: pd.DataFrame, city: str):
        #Upload to DB
        ti = time.time()
        print("Uploading to DB entries for {}...".format(city))
        self.db.insert_df(segments, "segments")
        print("Segments uploaded for {}. Time elapsed: {} s".format(city, round(time.time()-ti, 2)))


    def run(self, activity_type:str) -> bool:
        # Check for access_token for the selected user, updating it if expired
        auth = strava_auth.StravaAuth(self.user)
        
        # Starting query counter (needed to deal with Strava query limit)
        global query_counter
        query_counter = query_counter+2     # 2 requests -> worst case scenario (expired token)

        # Simple consumer ("clean" segments still not analyzed)
        if self.user=="0":
            ti = time.time()
            self.get_runs_data(self.city[0], consumer=True)
            print("Extracted data for {} running segments for {}. Time elapsed: {} s".format(len(self.runsData), self.city[0], round(time.time()-ti, 2)))
            self.load(self.runsData, self.city[0])
            self.r.sadd("strava:running:cities", self.city[0])
            self.r.save()
            self.get_rides_data(self.city[0], consumer=True)
            print("Extracted data for {} riding segments for {}. Time elapsed: {} s".format(len(self.ridesData), self.city[0], round(time.time()-ti, 2)))
            self.load(self.ridesData, self.city[0])
            self.r.sadd("strava:riding:cities", self.city[0])
            self.r.save()
        else:
            for city in self.city:
                self.get_boundary(city)
                if activity_type == "running":
                    ti = time.time()
                    self.get_segments(self.boundary, activity_type, self.city.index(city), False)
                    print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runs), city, round(time.time()-ti, 2)))
                    print("Collecting running segments data for {}...".format(city))
                    self.get_runs_data(city, consumer=False)
                    print("Extracted data for {} running segments for {}. Time elapsed: {} s".format(len(self.runsData), city, round(time.time()-ti, 2)))
                    self.load(self.runsData, city)
                    self.r.sadd("strava:running:cities", city)
                    self.r.save()
                elif activity_type == "riding":
                    ti = time.time()
                    self.get_segments(self.boundary, activity_type, self.city.index(city), False)
                    print("Found {} riding segments for {}. Time elapsed: {} s".format(len(self.rides), city, round(time.time()-ti, 2)))
                    print("Collecting riding segments data for {}...".format(city))
                    self.get_rides_data(city, consumer=False)
                    print("Extracted data for {} riding segments for {}. Time elapsed: {} s".format(len(self.ridesData), city, round(time.time()-ti, 2)))
                    self.load(self.ridesData, city)
                    self.r.sadd("strava:riding:cities", city)
                    self.r.save()
                else:
                    ti = time.time()
                    self.get_segments(self.boundary, "running", self.city.index(city), False)
                    print("Found {} running segments for {}. Time elapsed: {} s".format(len(self.runs), city, round(time.time()-ti, 2)))
                    self.get_runs_data(city, consumer=False)
                    print("Extracted data for {} running segments for {}. Time elapsed: {} s".format(len(self.runsData), city, round(time.time()-ti, 2)))
                    print("Collecting running segments data for {}...".format(city))
                    self.load(self.runsData, city)
                    self.r.sadd("strava:running:cities", city)
                    ti = time.time()
                    self.get_segments(self.boundary, "riding", self.city.index(city), False)
                    print("Found {} riding segments for {}. Time elapsed: {} s".format(len(self.rides), city, round(time.time()-ti, 2)))
                    print("Collecting riding segments data for {}...".format(city))
                    self.get_rides_data(city, consumer=False)
                    print("Extracted data for {} riding segments for {}. Time elapsed: {} s".format(len(self.ridesData), city, round(time.time()-ti, 2)))
                    self.load(self.ridesData, city)
                    self.r.sadd("strava:riding:cities", city)
                    self.r.save()

        if len(self.r.smembers("strava:running:code"))>0:
            print("There are run segments not included, try to run the consumer (user: 0).")

        if len(self.r.smembers("strava:riding:code"))>0:
            print("There are ride segments not included, try to run the consumer (user: 0).")

        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDT Project 2021 - Strava data extraction")
    parser.add_argument("--city", nargs='+', type=str, help="The city/cities to search for", required=True)
    parser.add_argument("--activity", type=str, help="Activity type to search (running/riding/all) [Default: running]", default="running")
    parser.add_argument("--user", type=str, help="The user who performs the query", required=True)

    r = redis.Redis(host="localhost", port=6379, db=0)

    args = parser.parse_args()

    userCities = args.city
    city = []
    activity_type = args.activity
    user = args.user

    if activity_type not in ["running", "riding", "all"]:
        print("ACTIVITY ERROR: Please, insert a supported activity (running/riding/all)")
        sys.exit(0)

    for i in userCities:
        if activity_type=="running":
            if r.sismember("strava:running:cities", i):
                print("{}'s running data already in database. Skipping.".format(i))
            else:
                city.append(i)
        elif activity_type=="riding":
            if r.sismember("strava:riding:cities", i):
                print("{}'s riding data already in database. Skipping.".format(i))
            else:
                city.append(i)
        else:
            if r.sismember("strava:running:cities", i) and r.sismember("strava:riding:cities", i):
                print("{}'s running and riding data already in database. Skipping.".format(i))
            else:
                city.append(i)

    if city is not None:
        ce = StravaExtractor(city, r, user)
        success = ce.run(activity_type)

        if success:
            print("Done.")

    
    