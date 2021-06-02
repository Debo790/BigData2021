import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame
from osm2geojson.helpers import overpass_call
from osm2geojson.main import xml2geojson
from osm2geojson.main import json2geojson
import argparse
import time

class CityExtractor:

    def __init__(self, city:str):
        self.city = city
        self.items = None
        self.boundary = None

    def extract(self):
        
        print("Extracting nwr and routes for {}".format(self.city))

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
            '''.format(self.city)

        ti = time.time()
        result = overpass_call(myquery)
        res = xml2geojson(result)
        self.items = gpd.GeoDataFrame.from_features(res)
        if len(self.items) <= 0:
            raise ConnectionError("No items were found for {}. Try with another city or check your Overpass query limit.".format(self.city))
        else:

            tf = time.time()
            print("Extracted {} elements for {}. Time elapsed: {} s".format(len(self.items), self.city, round(tf-ti, 2)))
    
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
        
               
    def update(self):
        # Update Redis
        print("Redis updating...")

    def load(self):
        #Upload to DB
        print("Uploading to DB...")

    def run(self) -> bool:
        self.extract()
        self.get_boundary()
        self.update()
        self.load()
        return True


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="BDT Project 2021 - OSM data extraction")
    parser.add_argument("--city", type=str, help="the city to extract", required=True)

    args = parser.parse_args()

    city = args.city

    ce = CityExtractor(city)
    success = ce.run()

    if success:
        print("Done.")