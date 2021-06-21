# BigData2021 - Sport index from OSM and Strava

First running tips, improvements to this readme will follow.

## Data collection

### OpenStreetMap

Run the following command:

```
python3 -W ignore osm_extractor.py --city [insert city/cities]
```

Data will be stored in a GeoDataFrame (in a DB in a while). Easy to analyse in a Notebook at the moment.

Next steps: 
- DB upload and configuration
- (Redis?)

### Strava

Run the following command:

```
python3 -W ignore strava_extractor.py --city [insert city/cities] --activity [riding/running/all]
```

Data are not perfectly stored (for the moment) in tmp/running.json and tmp/riding.json. Segments' data are memory-stored in ridesData and runsData, upload in DB is coming. 
Activity parameter added, it's not required and default is "running". Available options are riding, running and all (riding+running).
Multiple cities can be passed as parameters, but if too many results are retrieved it can take quite a long time due to Strava limitations.

Configuration data are stored in conf/config.ini and conf/auth.json (private). 

Next steps:
- DB upload
- (Redis?)
