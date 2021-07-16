import collections
from flask import Flask, render_template
import redis
import sys
import os
import geopandas as gpd
sys.path.append(os.getcwd())
app = Flask(__name__)
import analysis.analysis as an

r = redis.Redis(host="localhost", port=6379, db=0)
result = r.zrevrange("sport:index", 0, -1, withscores=True)
#print(result)

#an = an.Analyzer(r, city="Trento")
#osm_test = an.get_osm(city="Trento")
#print(len(osm_test))

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=result)

@app.route("/about")
def about():
    #return render_template('about.html', title="About")
    return result
    

@app.route("/<string:city>")
def test(city):
    results = r.hgetall("{}:top10".format(city))
    res = collections.OrderedDict(sorted(results.items()))
    coni = r.get("{}:coni".format(city))
    agonist = r.get("{}:coni:agonist".format(city))
    practicing = r.get("{}:coni:practicing".format(city))
    osm = r.get("{}:osm".format(city))
    population = r.get("{}:population".format(city))
    area = r.get("{}:area".format(city))
    segments = r.get("{}:segments".format(city))
    return render_template('about.html', title=city, result = list(res.values()), coni = coni, agonist = agonist, practicing = practicing, osm = osm, population = population, area = area, segments = segments)
    


if __name__ == '__main__':
    app.run(debug=True)