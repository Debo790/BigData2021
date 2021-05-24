import geopandas as gpd
from osm2geojson.helpers import overpass_call
from osm2geojson.main import xml2geojson

myquery = '''
    area[name="Suzzara"]->.searchArea;
    (
    nwr["sport"](area.searchArea);
    );
    out geom;
    out body;
    (._;>;);
    out skel qt;
    '''

result = overpass_call(myquery)
res = xml2geojson(result)


gdf = gpd.GeoDataFrame.from_features(res)