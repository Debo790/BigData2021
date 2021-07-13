import sys
import os
import redis
import pandas as pd
import geopandas as gpd
import argparse
sys.path.append(os.getcwd())
import src.db_wrapper as wrapper

class Analyzer():

    def __init__(self, r: redis.Redis, city: str) -> None:
        self.db = wrapper.PostgresDB()
        self.r = r
        self.city = city
        self.strava = pd.DataFrame
        self.osm = gpd.GeoDataFrame
        self.coni = pd.DataFrame
        self.municipality = gpd.GeoDataFrame
    
    def get_osm(self, city: str):
        self.osm = self.db.return_gdf("select * from osm where city='{}'".format(city))
        print("osm: {}".format(len(self.osm)))


    def get_strava(self, city: str):
        cols = ["id", "name", "type", "effort_count", "athlete_count", "distance", "average_grade",
        "maximum_grade", "elevation_high", "elevation_low", "total_elevation_gain", "polyline", "city"]
        self.strava = self.db.return_df("select * from segments where city='{}'".format(city), cols)
        print("strava: {}".format(len(self.strava)))
        
    
    def get_coni(self, city: str):
        self.coni = self.db.return_df("select * from coni where comune='{}'".format(city), ["id", "name", "region", "province", "municipality", "agonism", "practicing"])
        print("coni: {}".format(len(self.coni)))
        

    def get_municipality(self, city: str):
        self.municipality = self.db.return_gdf("select * from comuni where name='{}'".format(city))
        print("comune: {}".format(self.municipality["population"][0]))

# indice di sportività di Vigonza = (n° di items sportivi +                                   
#                                (0.8*praticanti + 2*agonisti)*società iscritte +
#                                (numero di segmenti strava)*(atleti distinti))              
#                                / numero di abitanti di Vigonza

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
        print("---- {} ----".format(city))
        print("population: {}, area: {}, density: {}".format(population, area, density))
        print("items: {}, societies: {}, agonists: {}, practicers: {}".format(sport_items, societies, agonist, practicing))
        print("total segments: {}, total efforts: {}, distinct athletes: {}".format(segments, total_effort, total_athletes))



    def run(self) -> bool:
        self.get_osm(self.city)
        self.get_coni(self.city)
        self.get_strava(self.city)
        self.get_municipality(self.city)
        self.compute_index(self.city)
        
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BDT Project 2021 - Data analysis")
    parser.add_argument("--city", type=str, help="the city to extract", required=True)
    args = parser.parse_args()
    city = args.city

    r = redis.Redis(host='localhost', port=6379, db=0)

    an = Analyzer(r, city)
    if an.run():
        print("Done.")

    