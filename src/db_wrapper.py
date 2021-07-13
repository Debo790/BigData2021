from ctypes import create_string_buffer
from types import MethodDescriptorType
from geopandas.geodataframe import GeoDataFrame
from pandas.core.frame import DataFrame
import psycopg2
import configparser
import geopandas as gpd
import pandas as pd
from sqlalchemy.engine import create_engine

class PostgresDB:

    def __init__(self) -> None:
        self.conn = None
        self.cursor = None


    def connect(self):
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        self.conn = psycopg2.connect(
            host = config['postgresql']['host'],
            database = config['postgresql']['database'],
            user = config['postgresql']['user'],
            password = config['postgresql']['password'],
            port = config['postgresql']['port']
        )
        self.cursor = self.conn.cursor()
        return self
        
    
    def is_connected(self) -> bool:
        return bool(self.conn)
    

    def create_tables(self, geom: bool):
        
        with open("sql_scripts/init_tables.sql", "r") as f:
            query = f.read()
        for q in query.split(";")[:-1]:
            self.cursor.execute(q)
        if geom:
            for table in ["osm", "comuni"]:
                set_crs = "select UpdateGeometrySRID('{}','geometry',4326);".format(table)
                self.cursor.execute(set_crs)
        print("Tables created.")
    

    def insert_gdf(self, gdf: GeoDataFrame, name: str):
        
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        engine = create_engine("postgres://" + config['postgresql']['user'] + ":" +
                            config['postgresql']['password'] + "@" +
                            config['postgresql']['host'] + ":" + 
                            config['postgresql']['port'] + "/" +
                            config['postgresql']['database'])
        con = engine.connect()

        with self.connect():
            self.create_tables(geom=True)

        gdf.to_postgis("{}".format(name).casefold(), engine, if_exists='append', chunksize=None)
        con.close()


    def insert_df(self, df: DataFrame, name: str) -> bool:
        
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        engine = create_engine("postgres://" + config['postgresql']['user'] + ":" +
                            config['postgresql']['password'] + "@" +
                            config['postgresql']['host'] + ":" + 
                            config['postgresql']['port'] + "/" +
                            config['postgresql']['database'])
        con = engine.connect()

        with self.connect():
            self.create_tables(geom=False)

        df.to_sql("{}".format(name).casefold(), con, schema=None, if_exists='append', chunksize=None, index=False)
        con.close()

        return True


    def return_gdf(self, query: str) -> gpd.GeoDataFrame:

        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        engine = create_engine("postgres://" + config['postgresql']['user'] + ":" +
                            config['postgresql']['password'] + "@" +
                            config['postgresql']['host'] + ":" + 
                            config['postgresql']['port'] + "/" +
                            config['postgresql']['database'])
        con = engine.connect()
        self.connect()
        assert self.is_connected()
        res = gpd.read_postgis(query, engine, geom_col="geometry")
        return res


    def return_df(self, query: str, cols: list) -> pd.DataFrame:
        config = configparser.ConfigParser()
        config.read('conf/config.ini')
        engine = create_engine("postgres://" + config['postgresql']['user'] + ":" +
                            config['postgresql']['password'] + "@" +
                            config['postgresql']['host'] + ":" + 
                            config['postgresql']['port'] + "/" +
                            config['postgresql']['database'])
        con = engine.connect()
        self.connect()
        assert self.is_connected()
        self.cursor.execute(query)
        res = self.cursor.fetchall()
        df = pd.DataFrame.from_records(data=res, columns=cols)
        return df
        


    def close(self):

        if self.is_connected():
            self.conn.commit()
            self.cursor.close()
            self.conn.close()
            self.cursor = None
            self.conn = None


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()