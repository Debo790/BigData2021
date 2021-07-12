import sys
import os
import redis
import pandas as pd
import geopandas as gpd
sys.path.append(os.getcwd())
import src.db_wrapper as wrapper

class Analyzer():

    def __init__(self, r: redis.Redis) -> None:
        self.db = wrapper.PostgresDB()
        self.r = r
        pass


    def run(self) -> bool:
        df = self.db.return_df("select * from osm where city='Genova'")
        print(len(df))
        return True

if __name__ == "__main__":

    r = redis.Redis(host='localhost', port=6379, db=0)

    an = Analyzer(r)
    if an.run():
        print("Done.")

    