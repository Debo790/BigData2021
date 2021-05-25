import requests
from bs4 import BeautifulSoup
from os import utime
import json


# ESTRAZIONE CODICI SOCIETA'--------------------------------------------------------------------------
# Le società sono numerate in ordine progressivo, ma alcuni numeri mancano (forse alcune società sono state chiuse o trasferite),
# quindi prima salviamo tutti i codici delle società in una lista, poi ne estraiamo i dettagli dai relativi link, ciclando la lista stessa

all_societa="https://www.coni.it/it/registro-societa-sportive/home/registro-2-0.html?reg=0&start=" 
codici_societa=[]           # link contenente i codici di tutte le società
dati_societa=[]             # lista di dizionari con i dettagli delle società

for k in range(0,60,20):    #ciclare fino a 102260 (in totale sono 102265. 5 società sull'ultima pagina)
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
            print("In results... Association no. {}".format(el))
            el+=1
    print("Parsed {} associations".format(k+20))
    print("-----------------------------------------------")

print("Associations' codes: ")
print(codici_societa)
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

    dettaglio = {'code:': codice,
    'Name:': name,
    'Region:': regione,
    'Province:': provincia,
    'Comune:': comune,
    'Agonistici:': agonistici_praticanti[0],
    'Praticanti:': agonistici_praticanti[1]
    }
    dati_societa.append(dettaglio)
    print("Adding: {}".format(dettaglio["Name:"]))
    
#-----------------------------------------------------------


# OUTPUT FILE:
with open('dati_CONI.json', 'w') as outfile:
    json.dump(dati_societa, outfile)