import argparse
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import time
import redis
from db_wrapper import PostgresDB

class ConiExtractor:

    
    def __init__(self, r: redis.Redis) -> None:
        self.codici = set()    # codici di tutte le societa iscritte al Coni
        self.dati = []      # lista di dizionari con i dettagli delle società (utilizzato per debug)
        self.societa = pd.DataFrame()
        self.db = PostgresDB()
        self.r = r

    
    def extractSocietiesCode(self):

        # ESTRAZIONE CODICI SOCIETA'--------------------------------------------------------------------------
        # Le società sono numerate in ordine progressivo, ma alcuni numeri mancano (forse alcune società sono state chiuse o trasferite),
        # quindi prima salviamo tutti i codici delle società in una lista, poi ne estraiamo i dettagli dai relativi link, ciclando la lista stessa

        all_societa="https://www.coni.it/it/registro-societa-sportive/home/registro-2-0.html?reg=0&start=" 
        
        ti = time.time()
        for k in range(0,102260,20):    #ciclare fino a 102260 (in totale sono 102265. 5 società sull'ultima pagina)
            indirizzo=all_societa+str(k)
            print("Fetching {}".format(indirizzo))
            try:
                page=requests.get(indirizzo, timeout=120)
            except:
                print("Connection timed out for the bunch {}-{}. Page discarded.".format(k, k+20))
            
            if page.ok:

                soup = BeautifulSoup(page.content, 'html.parser')
                results = soup.find('div', class_='lista')
                el = 0
                if len(results)>0 and results is not None:
                    for element in results:
                        if len(element)>1:
                            numero = str(element).split()[2]                # link società
                            numero=numero.strip('">')           
                            if not self.r.sismember("coni:added", numero.split('=')[-1]):
                                self.codici.add(numero.split('=')[-1])
                                self.r.sadd("coni:code", numero.split('=')[-1])
                                #print("In results... Association no. {}".format(el))
                                el+=1
                else:
                    print("Skipped last one, no results retrieved.")

                if(len(self.codici)%2000 == 0 and len(self.codici) != 0):
                    # Wait to let Coni's website breathe
                    print("5 seconds waiting...")
                    time.sleep(5)

                print("Parsed {} associations. Elapsed time: {} s".format(len(self.codici), round(time.time()-ti, 2)))
                print("-----------------------------------------------")

        #print("Associations' codes: ".format(self.codici))
        print("-----------------------------------------------")
        #---------------------------------------------------------------------------------------------------

            
    def extractSocietiesData(self, to_json: bool, timeout: int):

        # ESTRAZIONE DATI SOCIETA'--------------------------------------------------------------------------
        print("Extracting associations data.....")
        baseURL="https://www.coni.it/it/registro-societa-sportive/home/registro-2-0/registro_dettaglio.html?id_societa="

        ti = time.time()
        for codice in self.r.smembers("coni:code"):
            codice = codice.decode("utf-8")
            indirizzo=baseURL+str(codice)
            try:
                page = requests.get(indirizzo, timeout=timeout)
                self.r.srem("coni:code", codice)
                self.r.sadd("coni:added", codice)
            
                if page.ok:

                    #print(page.content)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    #trovo la parte della pagina che mi interessa:
                    results = soup.find('section', id='component')
                    #print(results.prettify())

                    if results is not None:
                        societa_luogo = results.find('div', class_='dati-descrittivi')
                        name=societa_luogo.find('h3', class_='nome').text
                        regione=societa_luogo.find('p', class_='regione').text
                        provincia=societa_luogo.find('span', class_='provincia').text
                        comune=(societa_luogo.find('p', class_='comune').text).split()[0]

                        #print("Adding: {}".format(name))

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
                        
                        self.societa = self.societa.append(dettaglio, ignore_index=True)
                        if to_json:
                            self.dati.append(dettaglio)
                    
                    else:
                        print("Issue in retrieving data, skipped.")

                    if(len(self.societa)%200 == 0):
                        print("Waiting 5 sec. Requested data for {} societies.".format(len(self.societa)))
                        time.sleep(5)

                    if(len(self.societa)%1000 == 0):
                        self.load(self.societa)
                        self.societa = pd.DataFrame()
                        print("Time elapsed for the bulk: {} s.".format(round(time.time()-ti, 2)))
                        ti = time.time()

            except requests.exceptions.Timeout:
                print("Connection timed out for association with code {}. Association discarded.".format(codice))
                self.r.sadd("coni:discarded", codice)

        self.load(self.societa) # Last upload
        self.societa = pd.DataFrame()
        #-----------------------------------------------------------

        # OUTPUT FILE -- DEBUG PURPOSE:
        if to_json:
            with open('tmp/dati_CONI.json', 'w') as outfile:
                json.dump(self.dati, outfile)


    def load(self, societa: pd.DataFrame):
        if self.db.insert_df(societa, "coni"):
            print("Inserted {} associations.".format(len(societa)))


    def run(self, to_json: bool, timeout: int) -> bool:
        self.extractSocietiesCode()
        self.extractSocietiesData(to_json, timeout)
        while self.r.scard("coni:discarded") > 0 and timeout<=30:
            timeout = timeout+10
            print("Round completed. Timeout increased to {}s. Missing {} associations.".format(timeout, self.r.scard("coni:discarded")))
            self.r.delete("coni:discarded")
            self.extractSocietiesData(to_json, timeout)
        return True


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="BDT Project 2021 - CONI associations data extraction")
    parser.add_argument("--to_json", help="Write results in tmp/dati_CONI.json (debug purpose only)")
    args = parser.parse_args()

    r = redis.Redis(host="localhost", port=6379, db=0)

    extractor = ConiExtractor(r)
    success = False
    if args.to_json:
        success = extractor.run(to_json=True, timeout=10)
    else:
        success = extractor.run(to_json=False, timeout=10)

    if success:
        print("Associations data extracted and loaded.")