import pandas as pd
import geopandas as gpd
import time
import sys
import os
sys.path.append(os.getcwd())

import db_wrapper

class ComuniExtractor:

    def __init__(self) -> None:
        self.db = db_wrapper.PostgresDB()
        self.comuni = gpd.GeoDataFrame()

    def extract(self):
        # Reading italian municipalities
        self.comuni = pd.read_excel("data/Classificazioni statistiche-e-dimensione-dei-comuni_31_12_2020.xls")

        # Columns preparation
        colsDrop = ['Codice Istat del Comune \n(numerico)',
        'Popolazione legale 2011 (09/10/2011)', 'Zona altimetrica',
        'Altitudine del centro (metri)', 'Comune litoraneo', 'Comune isolano',
        'Grado di urbanizzazione', 'Zone costiere']
        renameCols = {'Codice Istat del Comune \n(alfanumerico)':'istat_code', 'Denominazione (Italiana e straniera)':'name',
                    'Denominazione altra lingua':'secondary_name', 'Superficie territoriale (kmq) al 01/01/2020':'area',
                    'Popolazione residente al 31/12/2019':'population', 'Codice Regione':'region'}
        self.comuni = self.comuni.drop(columns=colsDrop).rename(columns=renameCols)

        # Code-region mapping
        regCode = {1: "Piemonte", 2: "Valle d'Aosta / Vallée d'Aoste", 3: "Lombardia", 4:"Trentino Alto-Adige", 5: "Veneto", 
            6: "Friuli-Venezia Giulia", 7: "Liguria", 8: "Emilia-Romagna", 9: "Toscana", 10: "Umbria", 11: "Marche", 
            12: "Lazio", 13: "Abruzzo", 14: "Molise", 15: "Campania", 16: "Puglia", 17: "Basilicata", 
            18:"Calabria", 19:"Sicilia", 20: "Sardegna"}
        self.comuni["region"] = self.comuni["region"].replace(regCode)

        # Municipalities' geometries
        istat = gpd.read_file("data/istat_administrative_units_2020.gpkg", layer="municipalities")
        istat = istat.to_crs(epsg=4326)

        # Drop useless columns
        colsDrop = ["COD_RIP", "COD_REG", "COD_PROV", "COD_CM", "COD_UTS", "PRO_COM_T", "COMUNE", "COMUNE_A", "CC_UTS"]
        istat = istat[istat.PRO_COM!=41032] # Frazione accorpata
        istat = istat.rename(columns={'PRO_COM':'istat_code'}).drop(columns=colsDrop)
        self.comuni = istat.merge(self.comuni, on='istat_code', how='left')

        # Rearranging columns
        cols = self.comuni.columns.to_list()
        a, b = cols.index('geometry'), cols.index('population')
        cols[b], cols[a] = cols[a], cols[b]
        self.comuni = self.comuni[cols]

    
    def load(self):
        #Upload to DB
        ti = time.time()
        print("Uploading to DB municipalities' entries...")
        self.db.insert_gdf(self.comuni, "comuni")
        print("Segments uploaded for municipalities. Time elapsed: {} s".format(round(time.time()-ti, 2)))

    def run(self) -> bool:
        self.extract()
        self.load()
        return True

if __name__ == "__main__":

    ce = ComuniExtractor()
    success = ce.run()

    if success:
        print("Done.")
    