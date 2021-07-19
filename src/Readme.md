## ETL 

### OpenStreetMap

Extract sportive nodes, ways and routes for the specified city/cities. The update parameter forces data collection even if the city's data are already stored in db (useful for debug purpose, use it only if necessary).
Multiple cities can be passed as parameters, suggested limit is 3 due to not overload Overpass API.

```
python3 -W ignore src/osm_extractor.py --city [insert city/cities] [--update]
```

The list of available cities is stored in Redis (key: ```osm:cities```).

### Strava

To retrieve Strava running and riding data for a specific city/cities, run the following command:

```
python3 -W ignore src/strava_extractor.py --city [insert city/cities] --activity [riding/running/all] --user [user]
```

The list of available cities is stored in Redis (keys: ```strava:running:cities``` and ```strava:riding:cities```). 
Activity parameter added, it's not required and default is "running". Available options are riding, running and all (riding+running).
Multiple cities can be passed as parameters, but if too many results are retrieved it can take quite a long time due to Strava limitations (100 queries/15 minutes per user, max 1000 queries/day per user).

User 0 is used as a "cleaner": if segments data weren't collected by the extractor (e.g. due to connection lost, reponse error, query number exceeded, etc) but the segment(s) code(s) has been stored, this user run only the query related to that segment(s).  
Every other user works as specified above (remember to add their data in ```conf/config.ini``` and ```conf/auth_userX.json```.

### Demographics

To store demographics data related to Italy's municipalites, run the following command:

```
python3 -W ignore src/extract_comuni.py
```
Input data are stored in the ```../data``` folder. Source: ISTAT.  
Data will be stored in a Postgres table (these data are already included in the dump). 

### CONI

To store CONI data related to societies affiliate to CONI, run the following command:
```
python3 -W ignore src/coni_extractor.py [--to_json]
```
If parameter to_json is present, results are stored in ```tmp/dati_CONI.json```. This is suggested only for debug purpose.
The whole process can take a while, so it's better to change range parameters (line 33) to get faster results.  
Data will be stored in a Postgres table (these data are already included in the dump). 

## DB_wrapper

Helper class that manages db connections and read/write operations.
