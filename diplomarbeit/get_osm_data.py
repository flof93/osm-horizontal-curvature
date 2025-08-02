import csv
from tqdm import tqdm

import curvy
from matplotlib import pyplot as plt
import scipy
import numpy as np
import pickle

import os

# import pandas as pd
# import seaborn as sns

import logging.config

import diplomarbeit as da

logger = logging.getLogger(__name__)

# for city in curvy.railway_lines:
#     line = city
#     lower, upper = line.get_error_bounds()
#

def plt_curvature(line, plt_radius = False ,error_bounds = False, filter_savgol = False, savgol_win_l = 51, savgol_poly_o = 3):

    fig, ax = plt.subplots(1, 1)

    ax.set_xlabel("Distances s [m]")
    ax.set_ylabel("Curvature c [m]")

    ax.plot(line.s, line.c)

    if plt_radius: # Zeigt Radius im Graph an (Hinterfragenswert, siehe Bettinger et.al.)
        ax.plot(line.s, np.divide(1,line.c))

    if error_bounds: # Zeigt Fehlerbereich nach Bettinger et.al. an
        lower, upper = line.get_error_bounds()
        ax.plot(line.s, lower)
        ax.plot(line.s, upper)

    if filter_savgol: # legt Savitzky-Golay filter über Krümmung
        sav_gol = scipy.signal.savgol_filter(line.c, savgol_win_l, savgol_poly_o)
        ax.plot(line.s, sav_gol)

    ax.grid()

    plt.suptitle(line.name)

    plt.show()

def plt_line(line, x_y=True):
    fig, ax = plt.subplots(1, 1)
    if x_y:
        ax.plot(line.x,line.y,color=line.color)
    else:
        ax.plot([float(i) for i in line.lon], [float(i) for i in line.lat], color=line.color)
    ax.grid()
    plt.suptitle(line.name)
    plt.show()

def plt_line_curvature(line):
    fig, ax = plt.subplots(3, 1)
    ax[0].plot(line.x, line.y, color=line.color)
    ax[1].plot(line.s, line.c)
    ax[2].plot(line.s, line.dgamma)
    fig.suptitle(line.name)
    ax[0].set_xlabel("x-Coordinate [m]")
    ax[0].set_ylabel("y-Coordinate [m]")
    #ax[1].set_xlabel("Distances s [m]")
    ax[1].set_ylabel("Curvature c [1/m]")
    ax[2].set_xlabel("Distances s [m]")
    ax[2].set_ylabel("Change of Angle [gon]")

    #ax.grid()

def plt_network(network : curvy.Curvy, city: str = ""):
    fig, ax = plt.subplots()
    for line in network.railway_lines:
        ax.plot(line.lon,line.lat,color=line.color)
    ax.grid()
    if city:
        fig.suptitle(city)
        fig.canvas.manager.set_window_title(city)
    #ax.set_aspect('equal', adjustable='box')
    plt.show()




# def calc_dist(line):
#     dist=[]
#     for city in line.s:
#         if city == 0:
#             dist.append(0)
#         else:
#             dist.append(line.s[city]-line.s[city-1]) # Error: city is np.float64 not list

def load_data(coordinates: dict, force_download: bool = False, data_path: str = './data/'):
    networks = {}

    for location in tqdm(coordinates):
        if not os.path.exists(data_path + location):
            os.makedirs(data_path + location + '/osm')
            os.makedirs(data_path + location + '/timetable')

        elif not os.path.exists(data_path + location + '/osm'):
            os.makedirs(data_path + location + '/osm')

        elif not os.path.exists(data_path + location + '/timetable'):
            os.makedirs(data_path + location + '/timetable')

        download = force_download
        try:
            with open(data_path + location + "/osm/raw_data.pickle", "rb") as file:
                new_network = pickle.load(file)
                logger.info("Loaded City %s from disk" % location)

        except FileNotFoundError:
            print("%s.pickle not found" % location)
            download = True


        if download:
            print("Starting download of %s" % location)
            new_network: curvy.Curvy = curvy.Curvy(*coordinates[location]['coords'],
                                             desired_railway_types = coordinates[location]['modes'],
                                             download=True, recurse='>')  # Liest die Tramstrecken aus
            new_network.save(data_path + location + "/osm/raw_data.pickle")
            logger.info("Saved %s as Pickle" % location)

        networks[location] = new_network

    return networks

def load_csv_input(file_path: str) -> dict:
    """loads a csv-File with Cities and returns a dictionary"""
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
                                    'modes':modes, 'name':row['Stadt']}
            else:
                bbox = da.utils.get_bounding_box(row['machine_readable'])
                if bbox:
                    out_dict[row['machine_readable']] = {'coords': (bbox[2], bbox[0], bbox[3], bbox[1]),
                                          'modes': modes, 'name':row['Stadt']}
                else:
                    logger.warning('No bbox for City %s' % row['Stadt'])
                    continue

    logger.info("Loaded CSV-File: %s" % file_path)
    return out_dict


def main(data_path: str = './data/'):
    cityfile = data_path + 'cities.csv'
    coords: dict = load_csv_input(file_path= cityfile)
    print('Loading Cities\n')
    netzwerke = load_data(coordinates= coords, force_download=False, data_path = data_path)

    print('\nCities added, generating DataFrames and calculating Heights.\n')
    for city in tqdm(netzwerke):
        network = netzwerke[city]
        df_linien = da.utils.generate_df(network)
        df_linien.reset_index(inplace=True)
        #df_linien.to_feather('./Auswertung/Networks/%s.feather' % city)
        df_linien.to_csv(path_or_buf='%s%s/osm/processed.csv' % (data_path, city), index=False)

    return netzwerke

if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.WARNING)
    netze = main()



    #coords: dict = load_csv_input("cities.csv")
    #coords = {'Budapest':{'coords':(18.8,47.30,19.40,47.70), 'modes':['tram','light_rail']}} # For testing purposes
    #coords = {'Gmunden': {'coords': (13.77,47.90,14,48), 'modes': ['tram', 'light_rail']}}  # For testing purposes
    # bbox = da.utils.get_bounding_box('Portland')
    # coords = {'Portland':{'coords':(bbox[2]-1, bbox[0]-1, bbox[3], bbox[1]), 'modes':['tram', 'light_rail']}}
    #
    # print ('Loading Cities')
    # netzwerke = load_data(coords, force_download=True)
    #
    # print('Cities added, generating DataFrames and calculating Heights.')
    # #stadt, linie, richtung, dist, curvature_angular, gauge, elevation_max, elevation_min = [], [], [], [], [], [], [], []
    # for city in tqdm(netzwerke):
    #     network = netzwerke[city]
    #     df_linien = da.utils.generate_df(network)
    #     df_linien.reset_index(inplace=True)
    #
    #     # line_draw = network.railway_lines[0]
    #     # plt_line(line_draw)
    #     # plt_curvature(line_draw)
    #     # plt_line_curvature(line_draw)
    #     plt_network(network, city=city)
    #     # fig, ax = plt.subplots(10, 10)
    #     # plt.show()

#    df_linien['Höhe'] = da.utils.get_heights(lat= df_linien['Latitude'].tolist(), lon= df_linien['Longitude'].tolist())


    #
    #     for j in network.railway_lines:
    #         try:
    #             curv = max(j.gamma) / (max(j.s) / 1000) #TODO: Muss in Auswertung korrigiert werden!
    #             curvature_angular.append(curv)
    #             dist.append(max(j.s) / 1000)
    #
    #         except ValueError:
    #             logger.warning(
    #                 "Ignoring %s %s, no values for curvature or change of angle available" % (str(city), str(j)))
    #             curvature_angular.append(np.nan)
    #             dist.append((np.nan))
    #
    #         stadt.append(city)
    #         linie.append(j.ref if hasattr(j, 'ref') else '')
    #         richtung.append(str(j))
    #
    #         try:
    #             gauge.append(int(j.ways[0].tags['gauge']))
    #         except (KeyError, IndexError, ValueError):
    #             gauge.append(np.nan)
    #             logger.warning("No Gauge data for line %s in %s available" % (str(j), str(city)))
    #         # except TypeError: # könnte relevant sein, wenn die Linie im Dreischienengleis startet
    #
    #         ele = da.utils.get_heights_for_line(j)
    #         if ele:
    #             elevation_min.append(min(ele))
    #             elevation_max.append(max(ele))
    #         else:
    #             elevation_min.append(np.nan)
    #             elevation_max.append(np.nan)
    #
    #
    #
    #
    # d = {"Stadt": stadt, "Linie": linie, "Richtung": richtung, "Distanz": dist, "Kurvigkeit": curvature_angular,
    #      'Spurweite': gauge, 'Höhe_Max': elevation_max, 'Höhe_Min': elevation_min}
    # df = pd.DataFrame(data=d)
    # df.to_feather('Auswertung/data.feather')



    #
    # pt_cities = pd.pivot_table(data=df,
    #                            values=["Kurvigkeit", "Distanz"],
    #                            index=["Stadt", 'Spurweite'],
    #                            aggfunc={'Kurvigkeit': 'mean', 'Distanz': ('sum', 'mean')})
    # pt_gauge = pd.pivot_table(data=df, values=["Kurvigkeit", "Distanz"], index="Spurweite", aggfunc='mean')
    # print(pt_cities)
    # print(pt_gauge)
    #
    # pandas.read_csv('cities.csv')
    #
    # sns.boxplot(data=df, y='Kurvigkeit', x='Spurweite', orient='v')
    #
