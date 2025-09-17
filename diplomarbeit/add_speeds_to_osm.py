from typing import Tuple

import numpy as np
import pandas as pd
import difflib


def match_station(single: str, multiple: list) -> Tuple[str, str]:
    thresh: float = 0.8
    do_ask: bool = True

    scores_list: list = []
    for i in multiple:
        score = difflib.SequenceMatcher(a=i, b=single).ratio()
        scores_list.append((score, i))

    scores_list.sort(reverse=True)
    if scores_list[0][0] == 1:
        return single, scores_list[0][1]
    else:
        while do_ask:
            possible_stations = [i for i in scores_list if i[0] >= thresh]
            if len(possible_stations) == 0:
                thresh -= 0.2
                continue
            elif len(possible_stations) == 1 and possible_stations[0][0] > 0.84:
                return single, possible_stations[0][1]

            print('Mögliche Stationen für %s:' % single)
            for i in range(len(possible_stations)):
                print('[%s] %s - %s' % (i, possible_stations[i][1], possible_stations[i][0]))

            if thresh <= 0:
                print('+++++++++++++++++++++++++\nALLE STATIONEN ANGEZEIGT!\n+++++++++++++++++++++++++')
                answer = input('Bitte passende Station für %s wählen ([X] für keine der Möglichkeiten): ' % single)
            else:
                answer = input('Bitte passende Station für %s wählen ([M] für mehr Stationen, [X] für keine der Möglichkeiten): ' % single)

            if answer.lower() == 'x':
                return single, np.NaN
            elif answer.lower() == 'm':
                thresh -= 0.2
                continue
            elif answer.isnumeric():
                answer = int(answer)
                if answer <= i:
                    return single, possible_stations[answer][1]
                else:
                    thresh -= 0.2
                    continue


def extract_lines(network: pd.DataFrame) -> pd.DataFrame:
    grouped = network.groupby(['Linie'])
    data_df = []

    for name, group in grouped:
        distance = group['Distanz'].max() / 1000
        curvature = group['Winkel'].max() / distance

        data_df.append([name[0],
                        group['Nummer'].unique()[0],
                        group['From'].unique()[0],
                        group['To'].unique()[0],
                        distance,
                        curvature
                        #group['Gauge'].unique()[0],
                        ])

    columns = ['line_name', 'line_number', 'from', 'to', 'distance', 'curvature']
    df_lines = pd.DataFrame(data=data_df, columns=columns)

    return df_lines


def match_gtfs_on_osm(osm: pd.DataFrame, gtfs: pd.DataFrame, filepath: str, inline: bool = True) -> dict:
    try:
        df = pd.read_csv(filepath_or_buffer=filepath)
        matching_dict = dict(df.to_dict(orient='tight')['data'])

    except FileNotFoundError:
        matching_dict = dict()

    osm_first_stops_for_gtfs = list()
    osm_last_stops_for_gtfs = list()

    for line in osm.iterrows():
        osm_first_stop = line[1]['from']
        osm_last_stop = line[1]['to']
        if pd.notna(osm_first_stop):
            try:
                osm_first_stops_for_gtfs.append(matching_dict[osm_first_stop])
            except KeyError:
                osm_new, gtfs_new = match_station(single=osm_first_stop, multiple=gtfs['first_stop_name'].unique().tolist())
                matching_dict[osm_new] = gtfs_new
                osm_first_stops_for_gtfs.append(gtfs_new)
        else:
            osm_first_stops_for_gtfs.append(np.NaN)

        if pd.notna(osm_last_stop):
            try:
                osm_last_stops_for_gtfs.append(matching_dict[osm_last_stop])
            except KeyError:
                osm_new, gtfs_new = match_station(single=osm_last_stop, multiple=gtfs['last_stop_name'].unique().tolist())
                matching_dict[osm_new] = gtfs_new
                osm_last_stops_for_gtfs.append(gtfs_new)
        else:
            osm_last_stops_for_gtfs.append(np.NaN)

    if inline:
        osm['gtfs_first_stop_name'] = osm_first_stops_for_gtfs
        osm['gtfs_last_stop_name'] = osm_last_stops_for_gtfs

    pd.DataFrame.from_dict(data=matching_dict, orient='index').to_csv(path_or_buf=filepath)

    return matching_dict


def merge_osm_gtfs(osm: pd.DataFrame, gtfs: pd.DataFrame, ignore_line_number: bool = False) -> pd.DataFrame:

    if ignore_line_number:
        left_on = ['gtfs_first_stop_name', 'gtfs_last_stop_name']
        right_on = ['first_stop_name', 'last_stop_name']
    else:
        left_on = ['line_number', 'gtfs_first_stop_name', 'gtfs_last_stop_name']
        right_on = ['route_short_name', 'first_stop_name', 'last_stop_name']

    return_data = pd.merge(left=osm.astype({'line_number': 'str'}),
                           right=gtfs.astype({'route_short_name': 'str'}),
                           how='left',
                           left_on=left_on,
                           right_on=right_on
                           )
    return return_data


def main(data_dict: str, city: str, ignore_line_number: bool = False):
    gtfs = pd.read_csv('%s%s/timetable/results/trip_speeds_route_direction.csv' % (data_dict, city))
    osm = extract_lines(pd.read_csv('%s%s/osm/processed.csv' % (data_dict, city)))
    match_gtfs_on_osm(osm=osm, gtfs=gtfs, filepath='%s%s/station_matching.csv' % (data_dict, city))
    new = merge_osm_gtfs(osm=osm, gtfs=gtfs, ignore_line_number= ignore_line_number)
    return new


if __name__ == '__main__':
    data_dict = './data/'
    city = 'prag'
    main(data_dict, city)
