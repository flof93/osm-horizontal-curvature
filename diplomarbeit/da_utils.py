from typing import Type
from urllib.error import HTTPError
from urllib.request import Request

import numpy as np
import requests
from pandas import DataFrame

from curvy.utils import OSMRailwayLine
from curvy import Curvy
import pandas as pd


def get_bounding_box(query):
    # Nominatim-Url
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-agent': 'Mozilla/5.0'}

    # Parameter
    parameters = {
        'q' : query,
        'format' : 'json',
        'addressdetails' : 1
    }

    # Anfrage an Nominatim
    response = requests.get(url, params = parameters, headers=headers)

    # Wenn Anfrage erfolgreich war. (Status 200)
    if response.status_code == 200:
        results = response.json()

        if results:
            result = results[0]
            bbox = result.get('boundingbox')

            if bbox:
                return [float(coord) for coord in bbox]
            else:
                return []

        else:
            return []
    else:
        raise requests.exceptions.HTTPError


def get_heights(lat: list, lon: list) -> list:
    url = 'http://localhost:8080/api/v1/lookup'
    list_of_points = []
    ele = []

    if len(lat) != len(lon):
        raise AssertionError('Latitude and Longitude have to be the same length')
    elif lat == [np.NaN] or lon == [np.NaN]:
        return [np.NaN]

    for i in range(len(lat)):
        list_of_points.append(
            {'latitude': lat[i],
            'longitude': lon[i]}
        )

    json = {'locations': list_of_points}

    answer = requests.post(url=url, json=json)
    if answer.status_code == 200:
        results = answer.json()
        for result in results['results']:
            ele.append(result['elevation'])
        return ele
    else:
        answer.raise_for_status()




def get_heights_for_line(line: OSMRailwayLine) -> list:
    return get_heights(lat= [float(i) for i in line.lat], lon= [float(i) for i in line.lon])

    # url = 'http://localhost:8080/api/v1/lookup'
    # list_of_points = []
    # if len(line.lat) != len(line.lon):
    #     raise AssertionError('Latitude and Longitude have to be the same length')
    #
    # ele = []
    # if line.lat and line.lon:
    #     for city in range(len(line.lat)):
    #         list_of_points.append(
    #             {'latitude': float(line.lat[city]),
    #              'longitude': float(line.lon[city])}
    #         )
    #
    #     json = {'locations': list_of_points}
    #
    #     answer = requests.post(url= url, json= json)
    #     if answer.status_code == 200:
    #         results = answer.json()
    #         for result in results['results']:
    #             ele.append(result['elevation'])
    #     else:
    #         raise requests.exceptions.HTTPError
    #
    # return ele

def generate_df(curvy: Curvy) -> DataFrame:
    df_return=pd.DataFrame()
    for line in curvy.railway_lines:
        d = {'Linie': line.name if hasattr(line, 'name') else '',
             'Nummer': line.ref if hasattr(line, 'ref') else '',
             'Distanz': line.s if len(line.s)>0 else [np.NaN],
             'x': line.x if len(line.x)>0 else [np.NaN],
             'y': line.y if len(line.y)>0 else [np.NaN],
             'Latitude': [float(i) for i in line.lat] if len(line.lat)>0 else [np.NaN],
             'Longitude': [float(i) for i in line.lon] if len(line.lon)>0 else [np.NaN],
             'd_Kurvigkeit': line.dgamma if len(line.dgamma)>0 else [np.NaN],
             'Kurvigkeit': line.gamma if len(line.gamma)>0 else [np.NaN],
             'Krümmung': line.c if len(line.c)>0 else [np.NaN]}
        d['Höhe'] = get_heights(lat= d['Latitude'], lon= d['Longitude'])
        df_line=pd.DataFrame(data=d)
        df_return = pd.concat([df_line, df_return])
    return df_return
