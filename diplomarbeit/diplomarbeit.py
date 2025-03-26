import csv

import pandas

import curvy
from matplotlib import pyplot as plt
import scipy
import numpy as np
import pickle
import pandas as pd
import seaborn as sns

import logging.config

from curvy import Curvy
import utils

logger = logging.getLogger(__name__)

# for i in curvy.railway_lines:
#     line = i
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

def plt_line(line):
    fig, ax = plt.subplots(1, 1)
    ax.plot(line.x,line.y,color=line.color)
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

def plt_network(network : Curvy, city: str = ""):
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
#     for i in line.s:
#         if i == 0:
#             dist.append(0)
#         else:
#             dist.append(line.s[i]-line.s[i-1]) # Error: i is np.float64 not list

def load_data(coordinates: dict, force_download: bool = False):
    networks = {}
    n = 0
    for location in coordinates:
        download = force_download
        try:
            with open("Pickles/" + location + ".pickle", "rb") as file:
                new_network = pickle.load(file)
                logger.info("Loaded City %s from disk" % location)

        except FileNotFoundError:
            print("%s .pickle not found" % location)
            download = True


        if download:
            print("Starting download of %s" % location)
            new_network: Curvy = curvy.Curvy(*coordinates[location]['coords'],
                                             desired_railway_types = coordinates[location]['modes'],
                                             download=True)  # Liest die Tramstrecken aus
            new_network.save("Pickles/" + location + ".pickle")
            logger.info("Saved %s as Pickles/%s.pickle" % (location, location))

        networks[location] = new_network
        n += 1

        print(location + " added, " + str(int(n / len(coordinates) * 100)) + "% done")
    return networks

def load_csv_input(file_path: str) -> dict:
    """loads a csv-File with Cities and returns a dictionary"""
    out_dict = {}
    with open(file_path, newline='') as csvfile:
        data = csv.DictReader(csvfile, delimiter=";", quotechar='\'', quoting=csv.QUOTE_NONNUMERIC)
        for row in data:

            modes = row['RailModes'].split(',')
            if modes == ['']:
                modes = ['tram', 'light_rail']

            if row['West'] and row['Sued'] and row['Ost'] and row['Nord']:
                out_dict[row['Stadt']]={'coords':(row['West'],row['Sued'],row['Ost'],row['Nord']),
                                    'modes':modes}
            else:
                bbox = utils.get_bounding_box(row['Stadt'])
                if bbox:
                    out_dict[row['Stadt']] = {'coords': (bbox[2], bbox[0], bbox[3], bbox[1]),
                                          'modes': modes}
                else:
                    logger.warning('No bbox for City %s' % row['Stadt'])
                    continue

    logger.info("Loaded CSV-File: %s" % file_path)
    return out_dict


def main(input: str = 'cities.csv'):
    coords: dict = load_csv_input(input)
    #coords = {'Budapest':{'coords':(18.8,47.30,19.40,47.70), 'modes':['tram','light_rail']}} # For testing purposes

    netzwerke = load_data(coords, force_download=False)
    stadt, linie, richtung, dist, curvature, gauge = [], [], [], [], [], []
    for i in netzwerke:
        network = netzwerke[i]
        # line_draw = network.railway_lines[0]
        # plt_line(line_draw)
        # plt_curvature(line_draw)
        # plt_line_curvature(line_draw)
        # plt_network(network, city=i)
        # fig, ax = plt.subplots(10, 10)
        # plt.show()

        for j in network.railway_lines:
            try:
                curv = max(j.gamma) / (max(j.s) / 1000)
                curvature.append(curv)
                dist.append(max(j.s) / 1000)
            except ValueError:
                logger.warning("Ignoring %s %s, no values for curvature or change of angle available" % (str(i), str(j)))
                curvature.append(np.nan)
                dist.append((np.nan))

            stadt.append(i)

            try:
                linie.append(j.ref)
            except AttributeError:
                linie.append("")

            richtung.append(str(j))

            try:
                gauge.append(int(j.ways[0].tags['gauge']))
            except (KeyError, IndexError):
                gauge.append(np.nan)
                logger.warning("No Gauge data for line %s available" % str(j))

            # except TypeError: # könnte relevant sein, wenn die Linie im Dreischienengleis startet



    d = {"Stadt": stadt, "Linie": linie, "Richtung": richtung, "Distanz": dist, "Kurvigkeit": curvature,
         'Spurweite': gauge}
    df = pd.DataFrame(data=d)
    pt_cities = pd.pivot_table(data=df,
                               values=["Kurvigkeit", "Distanz"],
                               index=["Stadt", 'Spurweite'],
                               aggfunc={'Kurvigkeit': 'mean', 'Distanz': ('sum', 'mean')})
    pt_gauge = pd.pivot_table(data=df, values=["Kurvigkeit", "Distanz"], index="Spurweite", aggfunc='mean')
    print(pt_cities)
    print(pt_gauge)

if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.WARNING)
    #main()

    coords: dict = load_csv_input("cities.csv")
    # coords = {'Budapest':{'coords':(18.8,47.30,19.40,47.70), 'modes':['tram','light_rail']}} # For testing purposes

    netzwerke = load_data(coords, force_download=False)
    stadt, linie, richtung, dist, curvature, gauge = [], [], [], [], [], []
    for i in netzwerke:
        network = netzwerke[i]
        # line_draw = network.railway_lines[0]
        # plt_line(line_draw)
        # plt_curvature(line_draw)
        # plt_line_curvature(line_draw)
        # plt_network(network, city=i)
        # fig, ax = plt.subplots(10, 10)
        # plt.show()

        for j in network.railway_lines:
            try:
                curv = max(j.gamma) / (max(j.s) / 1000)
                curvature.append(curv)
                dist.append(max(j.s) / 1000)
            except ValueError:
                logger.warning(
                    "Ignoring %s %s, no values for curvature or change of angle available" % (str(i), str(j)))
                curvature.append(np.nan)
                dist.append((np.nan))

            stadt.append(i)

            try:
                linie.append(j.ref)
            except AttributeError:
                linie.append("")

            richtung.append(str(j))

            try:
                gauge.append(int(j.ways[0].tags['gauge']))
            except (KeyError, IndexError):
                gauge.append(np.nan)
                logger.warning("No Gauge data for line %s available" % str(j))

            # except TypeError: # könnte relevant sein, wenn die Linie im Dreischienengleis startet

    d = {"Stadt": stadt, "Linie": linie, "Richtung": richtung, "Distanz": dist, "Kurvigkeit": curvature,
         'Spurweite': gauge}
    df = pd.DataFrame(data=d)
    df.to_feather('Auswertung/data.feather')
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
