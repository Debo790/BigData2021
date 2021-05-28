import geopandas as gpd
from geopandas.geodataframe import GeoDataFrame
from osm2geojson.helpers import overpass_call
from osm2geojson.main import xml2geojson
import argparse

class CityExtractor:

    def __init__(self, city:str, items: GeoDataFrame):
        self.city = city
        self.items = items

    def extract(self):
        
        target = "(area[\"name:it\"=\"{}\"][admin_level=8];)->.searchArea;".format(self.city)

        myquery = '''
            {}
            (
            nwr["sport"](area.searchArea);
            );
            out geom;
            out body;
            (._;>;);
            out skel qt;
            '''.format(target)

        result = overpass_call(myquery)
        res = xml2geojson(result)


        self.items = gpd.GeoDataFrame.from_features(res)
        if len(self.items)==0:
            target = target.replace("\"name:it\"", "name")
            myquery = '''
                {}
                (
                nwr["sport"](area.searchArea);
                );
                out geom;
                out body;
                (._;>;);
                out skel qt;
                '''.format(target)
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

    def run(self):
        self.extract()
        self.update()
        self.load()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--city", type=str, help="the city to search", required=True)

    args = parser.parse_args()

    city = args.city

    ce = CityExtractor(city, None)
    ce.run()

    print("Done.")