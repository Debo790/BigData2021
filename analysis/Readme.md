## Analysis

This script runs over data stored in db and compute the sport index for each city.  
Results are stored in multiple Redis set and hashmap, while GeoJSON results useful for Top10 segments for each city are stored in ```flask/data/{city}.json```.  
Results are also printed on console and saved in ```out.txt``` to have a global visualization of all the components that contribute to compose the score. 

To run the analysis, redis-server should be running. To run the script, type:

```python3 -W ignore analysis/analysis.py --time [seconds]```

from the root directory. User can choose how often the analysis can run by setting parameter ```time``` (expressed in seconds). Default is 30 minutes.
