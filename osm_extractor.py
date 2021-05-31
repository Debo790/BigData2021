import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame
from osm2geojson.helpers import overpass_call
from osm2geojson.main import xml2geojson
import argparse

class CityExtractor:

    def __init__(self, city:str, items: GeoDataFrame) -> None:
        self.city = city
        self.items = items

    def extract(self):
        
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
            '''.format(self.city)

        result = overpass_call(myquery)
        res = xml2geojson(result)
        self.items = gpd.GeoDataFrame.from_features(res)
        print("Parsed {} elements for {}".format(len(self.items), self.city))
        
    def update(self):
        # Update Redis
        print("Redis updating...")

    def load(self):
        #Upload to DB
        print("Uploading to DB...")

    def run(self) -> bool:
        self.extract()
        self.update()
        self.load()
        return True


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="BDT Project 2021 - OSM data extraction")
    parser.add_argument("--city", type=str, help="the city to extract", required=True)

    args = parser.parse_args()

    city = args.city

    ce = CityExtractor(city, None)
    success = ce.run()

    if success:
        print("Done.")