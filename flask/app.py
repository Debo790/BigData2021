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

an = an.Analyzer(r, city="Trento")
osm_test = an.get_osm(city="Trento")
print(len(osm_test))

@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=result)

@app.route("/about")
def about():
    return render_template('about.html', title="About")
    

@app.route("/city/<string:city>")
def test(city):
    #return render_template('about.html', title="About")
    return city


if __name__ == '__main__':
    app.run(debug=True)