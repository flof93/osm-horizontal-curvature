from typing import Tuple
from time import sleep

import pandas as pd
import difflib

def match_station(single: str, multiple: list) -> Tuple[str, str]:
    possibles_list=[]
    thresh = 1
    while len(possibles_list) < 5:

        for i in multiple:
            diffscore = difflib.SequenceMatcher(a=i, b=single).ratio()
            if diffscore >= thresh:
                possibles_list.append((diffscore, i))
                continue
            else:
                continue

        if thresh > 0:
            thresh -= 0.5

    if len(possibles_list) == 1:
        print('1 passende Station für %s gefunden:' % single)
        print('%s Score: %s' %(possibles_list[0][1], possibles_list[0][0]))
        sleep(0.25)
        return single, possibles_list[0][1]
    else:
        possibles_list.sort()
        print('Mögliche Stationen für %s:' % single)
        for i in range(len(possibles_list)):
            print ('[%s] %s - %s' %(i, possibles_list[i][1], possibles_list[i][0]))

        chosen = input('Gewählte Lösung: ')
        while not chosen.isnumeric():
            print('Bitte eine Zahl eingeben!')
            chosen = input('Gewählte Lösung: ')

            while not 0 <= int(chosen) <= len(possibles_list):
                print('Bitte eine Zahl zwischen 0 und %s eingeben!' %len(possibles_list))
                chosen = input('Gewählte Lösung: ')

        chosen = int(chosen)
        return single, possibles_list[chosen][1]

def extract_lines(network: pd.DataFrame) -> pd.DataFrame:

    grouped = network.groupby(['Linie'])
    data_df =[]

    for name, group in grouped:
        distance = group['Distanz'].max()/1000
        curvature = group['Winkel'].max() / distance

        data_df.append([name[0],
                        group['Nummer'].unique()[0],
                        group['From'].unique()[0],
                        group['To'].unique()[0],
                        distance,
                   curvature
                   #group['Gauge'].unique()[0],
                   ])

    columns=['line_name', 'line_number', 'from','to','distance','curvature']
    df_lines = pd.DataFrame(data=data_df, columns=columns)

    return df_lines

#TODO: Mappingtabelle erzeugen, dann in der GTFS-Ergebnistabelle die OSM-Bezeichnungen hinzufügen und dann mergen.

def match_osm_on_gtfs(osm: pd.DataFrame, gtfs: pd.DataFrame, filepath: str) -> dict:
    try:
        with open(file=filepath) as data:
            for row in data:
                gtfs, osm  = row.split(sep=',')
                matching_dict={osm: gtfs}

    except FileNotFoundError:
        matching_dict = dict()

    osm_first_stops_for_gtfs = list()
    osm_last_stops_for_gtfs = list()

    for line in osm.iterrows():
        osm_first_stop = line[1]['from']
        osm_last_stop = line[1]['to']
        try:
            osm_first_stops_for_gtfs.append(matching_dict[osm_first_stop])
        except KeyError:
            osm_new, gtfs_new = match_station(single=osm_first_stop, multiple = gtfs['first_stop_name'].unique().tolist())
            matching_dict[osm_new] = gtfs_new
            osm_first_stops_for_gtfs.append(osm_new)

        try:
            osm_last_stops_for_gtfs.append(matching_dict[osm_last_stop])
        except KeyError:
            osm_new, gtfs_new = match_station(single=osm_last_stop, multiple=gtfs['last_stop_name'].unique().tolist())
            matching_dict[osm_new] = gtfs_new
            osm_last_stops_for_gtfs.append(osm_new)

    osm['osm_first_stop_name'] = osm_first_stops_for_gtfs
    osm['osm_last_stop_name'] = osm_last_stops_for_gtfs

    return matching_dict




