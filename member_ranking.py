"""
Author:     Lars Hauptmann
E-Mail:     larshauptmann@mail.de

No guarantee to work after changed at the website

To execute the script, follow these steps

1. Install Anaconda

2. Create a new environment (run in your console)
    conda env create -n ESN --file requirements.yml
    conda activate ESN

3. (optional) Set the run parameters after line 145

4. Run the script (run in your console)
    python member_ranking.py

"""


import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import matplotlib.pyplot as plt

############################################################################
############# FUNCTIONS ####################################################
############################################################################

def extract_past_events(URL_past, column_name = ['date', 'name', 'org']):

    page_past = requests.get(URL_past)

    soup_past = BeautifulSoup(page_past.content, "html.parser")

    cont0 = soup_past.find_all('td', class_='content0')
    cont1 = soup_past.find_all('td', class_='content1')

    cont = cont0 + cont1

    for i, el in enumerate(cont):
        if el.find('img') != None:
            cont.remove(el)
            

    assert len(cont) %3 == 0, 'error in cont, length is not correct'
    column_name = ['date', 'name', 'org']
    data_past = pd.DataFrame(columns=column_name)
    for i in range(0, len(cont), 3):

        date, name, orgs = cont[i:i+3]

        name = name.find('a')
        
        date = re.search('</b>, (.*)</td>', str(date)).group(1)

        if name == None:
            name = ''
        else:
            name = name.string

        orgs = orgs.find_all('a')
        if len(orgs) != 0:
            orgs = [org.string for org in orgs]


        #print(f'Date: {date} \t Name: {name} \t Org: {org}')
        data_past.loc[i] = [date, name, orgs]


    data_past['date'] = pd.to_datetime(data_past['date'])
    data_past = data_past.sort_values(by='date', ascending=False)

    return data_past

def get_n_per_org(df):
    n_by_org = df.explode('org').groupby("org")["name"].count().sort_values(ascending=False)
    return n_by_org


def extract_future_events(URL_fut, column_name = ['date', 'name', 'org']):
    page_fut = requests.get(URL_fut)

    soup_fut = BeautifulSoup(page_fut.content, "html.parser")

    cont0 = soup_fut.find_all(class_='content0')
    cont1 = soup_fut.find_all(class_='content1')

    cont = cont0 + cont1


    data_fut = pd.DataFrame(columns=column_name)
    for i in range(len(cont)):
        cont_el = cont[i].find_all('td')
        date, name, orgs = cont_el[0], cont_el[-2], cont_el[-1]

        name = name.find('a')
        
        date = re.search('</b>(.*)</td>', str(date)).group(1)

        if name == None:
            name = ''
        else:
            name = name.string

        orgs = orgs.find_all('a')
        if len(orgs) != 0:
            orgs = [org.string for org in orgs]


        #print(f'Date: {date} \t Name: {name} \t Org: {org}')
        data_fut.loc[i] = [date, name, orgs]

    data_fut['date'] = pd.to_datetime(data_fut['date'], dayfirst=True, errors='coerce')
    data_fut = data_fut.sort_values(by='date', ascending=False)

    return data_fut

def extract_team_names(URL_team):
    page_team = requests.get(URL_team)

    soup_team = BeautifulSoup(page_team.content, "html.parser")
    cont0 = soup_team.find_all(class_='content0')
    cont1 = soup_team.find_all(class_='content1')
    cont = cont1 + cont0
    column_names = ['e-mail', 'name', 'nickname']
    data_names = pd.DataFrame(columns = column_names)
    for i in range(len(cont)):
        e_mail, name, nickname = cont[i].find_all('a')
        e_mail, name, nickname = e_mail.string, name.string, nickname.string
        data_names.loc[i] = [e_mail, name, nickname]

    return data_names

def concat_names(all_names, n_per_org):
    all_names = all_names['nickname'].rename('org')
    all_names = pd.Series(index=all_names, data =0, name='name')
    all_n_per_org = all_names.add(n_per_org, fill_value=0).sort_values(ascending=False).astype(int)
    return all_n_per_org

############################################################################
############# CONFIG PARAMETERS ############################################
############################################################################

URL_past = "https://zurich.esn.ch/pastEvents"
URL_fut = "https://zurich.esn.ch/"
URL_team = "https://zurich.esn.ch/team"
start_date = '2022-09-01'

include_future_events = True


############################################################################
############# EXECUTION ####################################################
############################################################################


data_past = extract_past_events(URL_past)
# only take values from this semester
data_past = data_past[data_past['date'] >start_date]

data_future = extract_future_events(URL_fut)

all_data = pd.concat([data_past, data_future], ignore_index=True)
n_per_org = get_n_per_org(all_data)

names_data = extract_team_names(URL_team)


all_n_per_org = concat_names(names_data, n_per_org)


print(f'ESN Members by amount of organized events after {start_date}:')
print(all_n_per_org.to_string())
