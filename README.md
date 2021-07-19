# BigData2021 - Sport indexes for italian cities

This project aims to classify italian cities based on how much their inhabitants are sportive. A sport index is calculated for each city considering how many OpenStreetMap sport features are present in its territory, how many societies are registered to CONI and how many segments are featured on Strava for that city.  
Results are displayed in a simple webapp where user can see the leaderboard and the most important Strava segments for each city.

## Usage

All the scripts should be run from root directory. Parameter ```-W ignore``` is not required but suggested, since it will prevent possible warning messages related to geopandas dependencies.

The following guide refers to a Unix environment. All the scripts have been tested on Linux.

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

## Credentials

To communicate with the database, the file ```conf/config.ini``` has to be created. A sample is available at ```conf/config_sample.ini``` (section: postgresql).  
The setup of a Strava user credentials is not required to run a demo, but if you want to add more cities to the available ones the required parameters has to be specified in the same file (e.g. for the user 0, section: strava0) and in the authentication one (e.g. for the user 0 ```conf/auth_user0.json```). A sample is provided at ```conf/auth_usernumber.json```, while a proper walkthrough can be found [here](https://github.com/franchyze923/Code_From_Tutorials/blob/master/Strava_Api/request_links.txt). 

# Quick start

After having set up credentials, run:

```python3 setup.py```

to create the database and load the dump. Then, start redis-server and load ```tmp/dump.rdb```.

To visualize the demo, run:

```python3 flask/app.py```

You can now access the demo at ```https://localhost:5000/``` to have an overview of the index leaderboard. Further details about any city can be found by clicking the city's name or by typing ```https://localhost:5000/{city}```.

## Packages

* Analysis: contains the script to run the analysis and compute the index and the partial results
* Flask: contains files and data required exclusively for the demo
* Src: contains ETL scripts and helper modules
* Conf: contains configuration files related to DB and Strava user(s)

Further details are provided in each directory, along with command intructions.

### Contacts

For any additional information, contact us at:  
Andrea Debeni: <andrea.debeni@studenti.unitn.it>  
Giulia Dalle Sasse: <giulia.dallesasse@studenti.unitn.it>
