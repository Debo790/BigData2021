import collections
from flask import Flask, render_template
import redis
import sys
import os
sys.path.append(os.getcwd())
app = Flask(__name__)

r = redis.Redis(host="localhost", port=6379, db=0)
result = r.zrevrange("sport:index", 0, -1, withscores=True)


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=result)


@app.route("/<string:city>")
def test(city):
    results = r.hgetall("{}:top10".format(city))
    res = collections.OrderedDict(sorted(results.items()))
    coni = r.get("{}:coni".format(city)).decode("utf-8")
    agonist = r.get("{}:coni:agonist".format(city)).decode("utf-8")
    practicing = r.get("{}:coni:practicing".format(city)).decode("utf-8")
    osm = r.get("{}:osm".format(city)).decode("utf-8")
    population = r.get("{}:population".format(city)).decode("utf-8")
    area = r.get("{}:area".format(city)).decode("utf-8")
    segments = r.get("{}:segments".format(city)).decode("utf-8")
    return render_template('about.html', title=city, result = list(res.values()), coni = coni, agonist = agonist, practicing = practicing, osm = osm, population = population, area = area, segments = segments)
    

if __name__ == '__main__':
    app.run(debug=True)