from time import sleep
from typing import Tuple

import pandas as pd
import difflib

def match_station(single: str, multiple: list) -> Tuple[str, str]:
    possibles_list=[]
    thresh = 1
    while len(possibles_list) < 1:

        for i in multiple:
            diffscore = difflib.SequenceMatcher(a=i, b=single).ratio()
            if diffscore >= thresh:
                possibles_list.append((diffscore, i))
                continue
            else:
                continue

        if thresh > 0:
            thresh -= 0.2

    if len(possibles_list) == 1:
        print('1 passende Station für %s gefunden:' % single)
        print('%s Score: %s' %(possibles_list[0][1], possibles_list[0][0]))
        sleep(1)
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

def map_osm_gtfs(osm_data: str, gtfs_data: str):
    pass


def find_gtfs_speed(osm: pd.DataFrame, gtfs: pd.DataFrame) -> float:
    pass

    #for index, line in osm.iterrows()[1]:

# TODO: make Matching system