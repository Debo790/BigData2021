import sys
import os
import redis
import pandas as pd
import geopandas as gpd
import argparse
import polyline
import shapely.geometry as shp
sys.path.append(os.getcwd())
import src.db_wrapper as wrapper


class Analyzer():

    def __init__(self, r: redis.Redis, city: str) -> None:
        self.db = wrapper.PostgresDB()
        self.r = r
        self.city = city
        self.strava = None
        self.osm = gpd.GeoDataFrame
        self.coni = pd.DataFrame
        self.municipality = gpd.GeoDataFrame
    

    def decode_polyline(self):
        self.strava["geometry"] = None
        for i in range(len(self.strava)):
            pointList = polyline.decode(self.strava.loc[i,"polyline"])
            if len(pointList)>1:
                poly = shp.LineString([[p[0], p[1]] for p in pointList])
                self.strava.loc[i,"geometry"] = poly
        self.strava = self.strava.drop(columns=["polyline"])
        self.strava = gpd.GeoDataFrame(self.strava)
        self.strava = self.strava.set_crs(epsg=4326)


    def get_osm(self, city: str) -> gpd.GeoDataFrame:
        return self.db.return_gdf("select * from osm where city='{}'".format(city))
        #print("osm: {}".format(len(self.osm)))


    def get_strava(self, city: str) -> pd.DataFrame:
        cols = ["id", "name", "type", "effort_count", "athlete_count", "distance", "average_grade",
        "maximum_grade", "elevation_high", "elevation_low", "total_elevation_gain", "polyline", "city"]
        return self.db.return_df("select * from segments where city='{}'".format(city), cols)
        #print("strava: {}".format(len(self.strava)))
        
    
    def get_coni(self, city: str) -> pd.DataFrame:
        return self.db.return_df("select * from coni where comune='{}'".format(city), ["id", "name", "region", "province", "municipality", "agonism", "practicing"])
        #print("coni: {}".format(len(self.coni)))
        

    def get_municipality(self, city: str) -> pd.DataFrame:
        return self.db.return_gdf("select * from comuni where name='{}'".format(city))
        #print("comune: {}".format(self.municipality["population"][0]))

    def update(self, city: str, agonist: int, practicing: int, effort: int, athletes: int):
        self.r.set("{}:osm".format(city), len(self.osm))
        self.r.set("{}:coni".format(city), len(self.coni))
        self.r.set("{}:coni:practicing".format(city), practicing)
        self.r.set("{}:coni:agonist".format(city), agonist)
        self.r.set("{}:segments".format(city), len(self.strava))
        self.r.set("{}:segments:efforts".format(city), effort)
        self.r.set("{}:segments:athletes".format(city), athletes)
        self.r.set("{}:population".format(city), int(self.municipality["population"][0]))
        self.r.set("{}:area".format(city), int(self.municipality["area"][0]))
        self.r.save()

    def compute_index(self, city: str):
        
        # Get all parameters
        sport_items = len(self.osm)
        societies = len(self.coni)
        agonist = sum(self.coni["agonism"])
        practicing = sum(self.coni["practicing"])
        segments = len(self.strava)
        total_effort = sum(self.strava["effort_count"])
        total_athletes = sum(self.strava["athlete_count"])
        population = self.municipality["population"][0]
        area = self.municipality["area"][0]
        density = round(population/area, 2)
        osm_component = (sport_items/area)
        coni_component = (societies*(0.25*practicing+0.75*agonist)/population)
        strava_component = ((segments*total_effort/total_athletes)/density)
        score = (sport_items/area + (societies*(0.25*practicing+0.75*agonist))/population + (segments * total_effort/total_athletes)/density)
        score = (osm_component*0.2 + coni_component*0.2 + strava_component*0.6)/population*10000
        print("---- {} ----".format(city))
        print("population: {}, area: {}, density: {}".format(population, area, density))
        print("items: {}, societies: {}, agonists: {}, practicers: {}".format(sport_items, societies, agonist, practicing))
        print("total segments: {}, total efforts: {}, distinct athletes: {}".format(segments, total_effort, total_athletes))
        print("coni component: {}".format(coni_component))
        print("osm_component: {}".format(osm_component))
        print("strava_component: {}".format(strava_component))
        print("Score for {}= (osm_component*0.2 + coni_component*0.2 + strava_component*0.6)/population*10000 = {}".format(city, score))
        print("-----------------------------")

        self.r.zadd("sport:index", {city: score})
        self.r.save()
        self.update(self.city, agonist, practicing, total_effort, total_athletes)
        self.r.save()

    def run(self) -> bool:
        for i in self.r.smembers("strava:running:cities"):
            self.city = i.decode("utf-8")
            self.osm = self.get_osm(self.city)
            self.coni = self.get_coni(self.city)
            self.strava = self.get_strava(self.city)
            self.decode_polyline()
            self.municipality = self.get_municipality(self.city)
            self.compute_index(self.city)

        
        print("Classification:")
        for i in self.r.zrevrange("sport:index", 0, -1, withscores=True):
            print(i[0].decode("utf-8"), i[1])

        print("Top 10:")
        for i in r.zrevrangebyscore("sport:index", 100, 0, withscores=True, start=0, num=10):
            print(i[0].decode("utf-8"), i[1])
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDT Project 2021 - Data analysis")
    parser.add_argument("--city", type=str, help="the city to extract")
    args = parser.parse_args()
    city = args.city

    r = redis.Redis(host='localhost', port=6379, db=0)

    an = Analyzer(r, city)
    if an.run():
        print("Done.")

    