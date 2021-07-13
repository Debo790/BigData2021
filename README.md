# BigData2021 - Sport index from OSM and Strava

First running tips, improvements to this readme will follow.

## Usage

Remember to run the scripts from root directory. Parameter ```-W ignore``` is not required but suggested, since it will prevent possible warning messages related to geopandas dependencies.

Scripts are tested on Linux. Windows shows issues with some geopandas dependencies, but if the module is already installed it should run without inconvenients. In any case, the following guide is referred to a Unix environment.

### Virtual environment setup

Create the virtual environment:

```
# Use python or python3 (depending on the recognised command)
python -m venv ./venv
```

Activate virtual environment:

```
source venv/bin/activate
```

Install required dependencies:

```
pip install -r requirements.txt
```

## Data collection

### OpenStreetMap

Extract sportive nodes, ways and routes for the specified city/cities. The update parameter forces data collection even if the city's data are already stored in db (useful for debug purpose, use it only if necessary).
Multiple cities can be passed as parameters, suggested limit is 3 due to not overload Overpass API.

```
python3 -W ignore src/osm_extractor.py --city [insert city/cities] [--update]
```

Data are stored in a Postgres database, while the list of cities is available in Redis (key: osm:cities).

### Strava

To retrieve Strava running and riding data for a specific city/cities, run the following command:

```
python3 -W ignore src/strava_extractor.py --city [insert city/cities] --activity [riding/running/all] --user [user]
```

Data are stored in a Postgres database, while the list of cities is available in Redis (key: osm:cities). 
Activity parameter added, it's not required and default is "running". Available options are riding, running and all (riding+running).
Multiple cities can be passed as parameters, but if too many results are retrieved it can take quite a long time due to Strava limitations (1000 queries/day per user).

Configuration data are stored in conf/config.ini and conf/auth_\[user\].json (private). 

### Demographics

To store demographics data related to Italy's municipalites, run the following command:

```
python3 -W ignore src/extract_comuni.py
```
Data will be stored in a Postgres database. 

### CONI

To store CONI data related to societies affiliate to CONI, run the following command:
```
python3 -W ignore src/coni_extractor.py [--to_json]
```
If parameter to_json is present, results are stored in ```tmp/dati_CONI.json```. This is suggested only for debug purpose.
The whole process can take a while, so it's better to change range parameters (line 33) to get faster results. Data are already stored in a Postgres database anyway.

## Metrics calculation

Metrics should be calculated when retrieved from DB.

They should be stored in a middle-layer DB to be presented to the final user.
