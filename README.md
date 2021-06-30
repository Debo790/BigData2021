# BigData2021 - Sport index from OSM and Strava

First running tips, improvements to this readme will follow.

## Data collection

### OpenStreetMap

Run the following command:

```
python3 -W ignore osm_extractor.py --city [insert city/cities]
```

Data are stored in a local DB (Postgres). Easy to analyse in a Notebook at the moment.

Next steps: 
- DB upsert, maybe RDS
- (Redis?)

### Strava

Run the following command:

```
python3 -W ignore strava_extractor.py --city [insert city/cities] --activity [riding/running/all]
```

Data are now stored in a local Db (Postgres). 
Activity parameter added, it's not required and default is "running". Available options are riding, running and all (riding+running).
Multiple cities can be passed as parameters, but if too many results are retrieved it can take quite a long time due to Strava limitations.

Configuration data are stored in conf/config.ini and conf/auth.json (private). 

Next steps:
- DB upsert, maybe RDS
- (Redis?)

### Demographics

Populations will be stored in a DB. Coming.

### CONI

CONI data will be stored in a DB. Coming.

## Metrics calculation

Metrics should be calculated when retrieved from DB.

They should be stored in a middle-layer DB to be presented to the final user.
