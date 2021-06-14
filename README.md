# BigData2021 - Sport index from OSM and Strava

First running tips, improvements to this readme will follow.

## Data collection

### OpenStreetMap

Run the following command:

```
python3 -W ignore osm_extractor.py --city [insert city]
```

Data will be stored in a GeoDataFrame (in a DB in a while). Easy to analyse in a Notebook at the moment.

Next steps: 
- Input of cities in a list format
- DB upload and configuration
- (Redis?)

### Strava

Run the following command:

```
python3 -W ignore strava_extractor.py --city [insert city]
```

Data will be stored in tmp/running.json and tmp/riding.json. At the moment only the first iteration is available. Multi-iteration over the city will be available soon.

Configuration data are stored in conf/config.ini and conf/auth.json (private). 

Next steps:
- Multi-iteration over a city (include all segments available)
- Segments-scraping to store useful data segments
- DB upload
- (Redis?)
