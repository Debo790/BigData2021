import geopandas as gpd
from osm2geojson.helpers import overpass_call
from osm2geojson.main import xml2geojson

city = "(area[\"name:it\"=\"Roma\"];)->.searchArea;"

myquery = '''
    {}
    (
    nwr["sport"](area.searchArea);
    );
    out geom;
    out body;
    (._;>;);
    out skel qt;
    '''.format(city)

result = overpass_call(myquery)
res = xml2geojson(result)


gdf = gpd.GeoDataFrame.from_features(res)
if len(gdf)==0:
    print(city)
    city = city.replace("\"name:it\"", "name")
    myquery = '''
        {}
        (
        nwr["sport"](area.searchArea);
        );
        out geom;
        out body;
        (._;>;);
        out skel qt;
        '''.format(city)
    result = overpass_call(myquery)
    res = xml2geojson(result)
    gdf = gpd.GeoDataFrame.from_features(res)
print(len(gdf))