from typing import List
import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame
from osm2geojson.helpers import overpass_call
from osm2geojson.main import xml2geojson
from osm2geojson.main import json2geojson
import argparse
import time
import redis
from db_wrapper import PostgresDB

class CityExtractor:

    def __init__(self, city:List):
        self.city = city
        self.items = None
        self.db = PostgresDB()
        #self.boundary = None


    def extract(self, city):
        
        print("Extracting nwr and routes for {}".format(city))

        # nwr stays for "node, ways and relation"
        # every item with a sport tag is included
        # out geom adds geometries to each item
        # qt sorts by quadtile index, faster than order by id
        myquery = '''
            (area["name"="{}"][admin_level=8];)->.searchArea;
            area["name"="Italia"]->.wrap;
            (
            nwr["sport"](area.searchArea);
            nwr["landuse"="winter_sports"](area.searchArea);
            nwr["leisure"="fitness_station"](area.searchArea);
            );
            out geom qt;
            rel(pivot.searchArea)(area.wrap) -> .ex;
            //.ex out geom;
            way(r.ex)->.cross;
            relation(around.cross:0)["route"="hiking"]->.remove;
            relation["route"="hiking"](area.searchArea)->.all;
            (.all; - .remove;);
            out geom qt;
            '''.format(city)

        ti = time.time()
        result = overpass_call(myquery)
        res = xml2geojson(result)
        self.items = gpd.GeoDataFrame.from_features(res)
        if len(self.items) <= 0:
            raise ConnectionError("No items were found for {}. Try with another city or check your Overpass query limit.".format(city))
        else:
            self.items = self.items.set_crs(epsg=4326)

            # Columns reorder
            cols = self.items.columns.to_list()
            cols = cols[-1:] + cols[:-1]
            self.items = self.items[cols]
            
            tf = time.time()
            print("Extracted {} elements for {}. Time elapsed: {} s".format(len(self.items), city, round(tf-ti, 2)))
    

    def update(self, city, r: redis.Redis):
        # Update Redis
        r.sadd("osm:cities", city)

    def load(self, city):
        #Upload to DB
        ti = time.time()
        print("Uploading to DB entries for {}...".format(city))
        self.db.insert_gdf(self.items, "osm")
        print("Data uploaded for {}. Time elapsed: {} s".format(city, round(time.time()-ti, 2)))


    def run(self, r: redis.Redis) -> bool:
        for city in self.city:
            self.extract(city)
            #self.get_boundary()
            self.update(city, r)
            self.load(city)
        return True


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="BDT Project 2021 - OSM data extraction")
    parser.add_argument("--city", nargs='+', type=str, help="the city to extract", required=True)
    parser.add_argument("--update", help="update even if data are already in db")

    args = parser.parse_args()

    userCities = args.city
    cities = []
    update = args.update

    r = redis.Redis(host="localhost", port=6379, db=0)

    if update:
        ce = CityExtractor(userCities)
        success = ce.run(r)

        if success:
            print("Done.")
    else: 
        for i in userCities:
            if r.sismember("osm:cities", i):
                print("{}'s OSM data already in database. Skipping.".format(i))
            else:
                cities.append(i)

        if cities is not None:
            ce = CityExtractor(cities)
            success = ce.run(r)

            if success:
                print("Done.")
    