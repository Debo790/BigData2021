import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import time
from db_wrapper import PostgresDB

class ConiExtractor:

    def __init__(self) -> None:
        self.societa = pd.DataFrame()
        self.db = PostgresDB()

    def extractSocieties(self):

        # ESTRAZIONE CODICI SOCIETA'--------------------------------------------------------------------------
        # Le società sono numerate in ordine progressivo, ma alcuni numeri mancano (forse alcune società sono state chiuse o trasferite),
        # quindi prima salviamo tutti i codici delle società in una lista, poi ne estraiamo i dettagli dai relativi link, ciclando la lista stessa

        all_societa="https://www.coni.it/it/registro-societa-sportive/home/registro-2-0.html?reg=0&start=" 
        codici_societa=[]           # link contenente i codici di tutte le società
        dati_societa=[]             # lista di dizionari con i dettagli delle società

        ti = time.time()
        for k in range(0,2000,20):    #ciclare fino a 102260 (in totale sono 102265. 5 società sull'ultima pagina)
            indirizzo=all_societa+str(k)
            print("Fetching {}".format(indirizzo))
            page=requests.get(indirizzo)
            soup = BeautifulSoup(page.content, 'html.parser')
            results = soup.find('div', class_='lista')
            el = 0
            for element in results:
                if len(element)>1:
                    numero = str(element).split()[2]                # link società
                    numero=numero.strip('">')               
                    codici_societa.append(numero.split('=')[-1])    # codice società
                    #print("In results... Association no. {}".format(el))
                    el+=1
            print("Parsed {} associations. Elapsed time: {} s".format(k+20, round(time.time()-ti, 2)))
            print("-----------------------------------------------")

        #print("Associations' codes: ".format(codici_societa))
        print("-----------------------------------------------")
        #---------------------------------------------------------------------------------------------------

            
        # ESTRAZIONE DATI SOCIETA'--------------------------------------------------------------------------
        print("Extracting associations data.....")
        baseURL="https://www.coni.it/it/registro-societa-sportive/home/registro-2-0/registro_dettaglio.html?id_societa="


        for codice in codici_societa:
            indirizzo=baseURL+str(codice)
            page = requests.get(indirizzo)
            #print(page.content)
            soup = BeautifulSoup(page.content, 'html.parser')
            #trovo la parte della pagina che mi interessa:
            results = soup.find('section', id='component')
            #print(results.prettify())

            societa_luogo = results.find('div', class_='dati-descrittivi')
            name=societa_luogo.find('h3', class_='nome').text
            regione=societa_luogo.find('p', class_='regione').text
            provincia=societa_luogo.find('span', class_='provincia').text
            comune=(societa_luogo.find('p', class_='comune').text).split()[0]

            societa_numeri=results.find('div', class_='dati-container')
            agonistici_praticanti=[societa_numeri('span', class_='numero')[2].text, societa_numeri('span', class_='numero')[3].text]

            dettaglio = {'code': codice,
            'name': name,
            'region': regione,
            'province': provincia,
            'comune': comune,
            'agonistici': agonistici_praticanti[0],
            'praticanti': agonistici_praticanti[1]
            }
            dati_societa.append(dettaglio)
            print("Adding: {}".format(dettaglio["name"]))
            self.societa = pd.DataFrame(dettaglio, index=[0])
            self.load(self.societa)
            
        #-----------------------------------------------------------


        # OUTPUT FILE -- DEBUG PURPOSE:
        with open('tmp/dati_CONI.json', 'w') as outfile:
            json.dump(dati_societa, outfile)

    def load(self, societa: pd.DataFrame):
        self.db.insert_df(societa, "coni")
        print("Inserted societa {}".format(societa["code"][0]))

    def run(self):
        self.extractSocieties()

if __name__ == "__main__":
    
    extractor = ConiExtractor()
    extractor.run()