import numpy as np
import requests
import zipfile
import io
import os

from curvy.utils import OSMRailwayLine
import curvy
import pandas as pd


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
    stops = pd.read_csv(gtfs_path + "shapes.txt")
    east = min(stops['shape_pt_lon'])
    west = max(stops['shape_pt_lon'])
    south = min(stops['shape_pt_lat'])
    north = max(stops['shape_pt_lat'])
    return [south, north, east, west]

def get_bounding_box(query:str, data_path:str):
    nominatim_bbox = get_nominatim_bounding_box(query)
    if os.path.exists(data_path + query + '/timetable/shapes.txt'):
        gtfs_bbox = get_gtfs_bounding_box(data_path + query + '/timetable/')
    else:
        gtfs_bbox = [np.NaN,np.NaN,np.NaN,np.NaN]

    south = min(nominatim_bbox[0], gtfs_bbox[0])
    north = min(nominatim_bbox[1], gtfs_bbox[1])
    east = min(nominatim_bbox[2], gtfs_bbox[2])
    west = min(nominatim_bbox[3], gtfs_bbox[3])

    return [south, north, east, west]


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
            #TODO: Auf- und Abstieg berechnen
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
