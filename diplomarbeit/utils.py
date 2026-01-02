import shutil

import numpy as np
import requests
import zipfile
import io
import os

import diplomarbeit.buildings
from curvy.utils import OSMRailwayLine
import curvy
import pandas as pd


import logging.config
import csv

from osmnx.utils import ts

import gtfs_kit as gk

logger = logging.getLogger(__name__)


def get_nominatim_bounding_box(query):     # Nominatim-Url
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
                nominatim_bbox_out = [float(coord) for coord in bbox]
            else:
                nominatim_bbox_out =  []

        else:
            nominatim_bbox_out =  []
    else:
        raise requests.exceptions.HTTPError

    return nominatim_bbox_out

def get_gtfs_bounding_box(gtfs_path: str):
    shapes = pd.read_csv(gtfs_path + "shapes.txt", dtype={'shape_id':'str'}, usecols=['shape_id', 'shape_pt_lat', 'shape_pt_lon'])
    trips = pd.read_csv(gtfs_path + 'trips.txt', dtype={'shape_id':'str', 'route_id':'str'}, usecols=['shape_id', 'route_id'])
    routes = pd.read_csv(gtfs_path + 'routes.txt', dtype={'shape_id':'str', 'route_id':'str'}, usecols=['route_type', 'route_id'])

    df = routes[routes['route_type'].isin([0, 900, 901, 902])].merge(trips)
    df_tram = df.merge(shapes)

    east = min(df_tram['shape_pt_lon'])
    west = max(df_tram['shape_pt_lon'])
    south = min(df_tram['shape_pt_lat'])
    north = max(df_tram['shape_pt_lat'])
    return [south, north, east, west]

def get_bounding_box(query:str, data_path:str, osm_name:str):
    nominatim_bbox = get_nominatim_bounding_box(osm_name)
    if os.path.exists(data_path + query + '/timetable/shapes.txt'):
        gtfs_bbox = get_gtfs_bounding_box(data_path + query + '/timetable/')
    else:
        gtfs_bbox = [np.NaN,np.NaN,np.NaN,np.NaN]

    south = min(nominatim_bbox[0], gtfs_bbox[0])
    north = max(nominatim_bbox[1], gtfs_bbox[1])
    east = min(nominatim_bbox[2], gtfs_bbox[2])
    west = max(nominatim_bbox[3], gtfs_bbox[3])

    return [south, north, east, west]


def get_heights(lat: list, lon: list) -> list:
    url = 'http://localhost:8080/api/v1/lookup'
    headers = {'Accept': 'application/json','Content-Type': 'application/json'}
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

    answer = requests.post(url=url, json=json, headers=headers)
    if answer.status_code == 200:
        results = answer.json()
        for result in results['results']:
            ele.append(result['elevation'])
        return ele
    else:
        answer.raise_for_status()




def get_heights_for_line(line: OSMRailwayLine) -> list:
    return get_heights(lat= [float(i) for i in line.lat], lon= [float(i) for i in line.lon])


def generate_df(curvy: curvy.Curvy, generate_heights: bool = True) -> pd.DataFrame:
    df_return=pd.DataFrame()
    for line in curvy.railway_lines:
        d : dict = {
            'Linie': getattr(line, 'name') if hasattr(line, 'name') else '',
            'Nummer': getattr(line, 'ref') if hasattr(line, 'ref') else '',
            'Distanz': line.s if len(line.s)>0 else [np.NaN],
            'x': line.x if len(line.x)>0 else [np.NaN],
            'y': line.y if len(line.y)>0 else [np.NaN],
            'Latitude': [float(i) for i in line.lat] if len(line.lat)>0 else [np.NaN],
            'Longitude': [float(i) for i in line.lon] if len(line.lon)>0 else [np.NaN],
            'd_Winkel': line.dgamma if len(line.dgamma)>0 else [np.NaN],
            'Winkel': line.gamma if len(line.gamma)>0 else [np.NaN],
            'Krümmung': line.c if len(line.c)>0 else [np.NaN],
            'Gauge': int(line.ways[0].tags['gauge']) if len(line.ways) > 0 and 'gauge' in line.ways[0].tags and line.ways[0].tags['gauge'].isnumeric() else np.NaN,
            #'Gauge':
            'From': getattr(line, 'from') if hasattr(line, 'from') else '',
            'To': getattr(line, 'to') if hasattr(line, 'to') else ''
        }
        if generate_heights:
            d['Höhe'] = get_heights(lat= d['Latitude'], lon= d['Longitude'])
            aufstieg_list = [0]
            abstieg_list = [0]
            for i in range(len(d['Höhe'])):
                if i == 0:
                    continue
                    # aufstieg_list.append(0)
                    # abstieg_list.append(0)
                else:
                    delta_h=d['Höhe'][i]-d['Höhe'][i-1]
                    aufstieg_list.append(aufstieg_list[i-1] + abs(delta_h)) if delta_h > 0 else aufstieg_list.append(aufstieg_list[i-1])
                    abstieg_list.append(abstieg_list[i-1] + abs(delta_h)) if delta_h < 0 else abstieg_list.append(abstieg_list[i-1])
            d['Aufstieg'] = aufstieg_list
            d['Abstieg'] = abstieg_list

        df_line=pd.DataFrame(data=d)
        df_return = pd.concat([df_line, df_return])
    return df_return

def load_gtfs_speeds(path_to_trip_speeds):
    with open(path_to_trip_speeds, "r") as file:
        filedata = pd.read_csv(file)
    df = pd.DataFrame(data = filedata)
    return df

def get_uniques(*lists: list) -> list:
    ret = set()
    for element in lists:
        [ret.add(i) for i in element]
    ret = list(ret)
    return ret

def download_and_extraxt_gtfs(city: str, gtfs_url: str, data_path: str = './data/') -> None:
    with requests.get(url=gtfs_url) as payload:
        file = zipfile.ZipFile(io.BytesIO(payload.content))
    file.extractall('%s%s/timetable' % (data_path, city))

def load_csv_input(data_path: str, filename: str = 'cities.csv') -> dict:
    """loads a csv-File with Cities and returns a dictionary"""
    file_path = data_path + filename
    out_dict = {}
    with open(file_path, newline='') as csvfile:
        data = csv.DictReader(csvfile, delimiter=";")#, quotechar='\'', quoting=csv.QUOTE_NONNUMERIC)
        for row in data:

            if row['RailModes'] is None:
                modes = ['']
            else:
                modes = row['RailModes'].split(',')

            if modes == ['']:
                modes = ['tram', 'light_rail']

            if row['West'] and row['Sued'] and row['Ost'] and row['Nord']:
                out_dict[row['machine_readable']]={'coords':(float(row['West']),float(row['Sued']),float(row['Ost']),float(row['Nord'])),
                                    'modes':modes, 'name':row['Stadt'], 'ignore_linenumber': row['Ignore_LineNumber']}
            else:
                bbox = get_bounding_box(query= row['machine_readable'], data_path= data_path, osm_name=row['OSM-Name'])
                if bbox:
                    out_dict[row['machine_readable']] = {'coords': (bbox[2], bbox[0], bbox[3], bbox[1]),
                                          'modes': modes, 'name':row['Stadt'], 'ignore_linenumber': row['Ignore_LineNumber']}
                else:
                    logger.warning('No bbox for City %s' % row['Stadt'])
                    continue

    logger.info("Loaded CSV-File: %s" % file_path)
    return out_dict

def cleanup_input(data_path: str, filename: str = 'cities.csv', recalculate: bool = False):
    data = pd.read_csv(data_path+filename, sep=';')
    west, sued, ost, nord, buffer = [], [], [], [], []

    if not 'West' in data.columns or recalculate:
        data["West"] = np.nan
    if not 'Ost' in data.columns or recalculate:
        data["Ost"] = np.nan
    if not 'Sued' in data.columns or recalculate:
        data["Sued"] = np.nan
    if not 'Nord' in data.columns or recalculate:
        data["Nord"] = np.nan
    if not 'Buffer_Width' in data.columns or recalculate:
        data['Buffer_Width'] = np.nan

    for i, row in data.iterrows():
        print(ts(), '-', row['Stadt'])

        feed = None
        if not os.path.exists(data_path + row['machine_readable'] + '/timetable'):
            try:
                feed = gk.read_feed(row['GTFS-Daten'], 'm')
            except [requests.exceptions.MissingSchema, shutil.ReadError]:
                pass

        make_folders(data_path, row['machine_readable'])
        if feed:
            feed.to_file(data_path + row['machine_readable'] + '/timetable/')


        if pd.isna(row['West']) or pd.isna(row['Ost']) or pd.isna(row['Sued']) or pd.isna(row['Nord']):
            bbox = get_bounding_box(query=row['machine_readable'], data_path=data_path, osm_name=row['OSM-Name'])
            if bbox:
                west.append(bbox[2])
                sued.append(bbox[0])
                ost.append(bbox[3])
                nord.append(bbox[1])
            else:
                continue
        else:
            west.append(row['West'])
            sued.append(row['Sued'])
            ost.append(row['Ost'])
            nord.append(row['Nord'])

        if pd.isna(row['Buffer_Width']):
            buffer.append(diplomarbeit.buildings.calculate_buffer_width(row['OSM-Name']))
        else:
            buffer.append(row['Buffer_Width'])

    data.drop(labels=['West', 'Ost', 'Sued', 'Nord', 'Buffer_Width'], axis='columns')
    data['West'] = west
    data['Ost'] = ost
    data['Sued'] = sued
    data['Nord'] = nord
    data['Buffer_Width'] = buffer



    data.sort_values(by='machine_readable', axis='rows').to_csv(data_path+filename, sep=';', index=False)


def make_folders(data_path: str, city: str) -> None:
    os.makedirs(data_path + city + '/osm', exist_ok=True)
    os.makedirs(data_path + city + '/timetable', exist_ok=True)
    os.makedirs(data_path + city + '/buildings', exist_ok=True)