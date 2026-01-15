from typing import Any

from tqdm import tqdm

import curvy
from matplotlib import pyplot as plt
import scipy
import numpy as np
import pickle

import os

import logging.config

import diplomarbeit as da

logger = logging.getLogger(__name__)


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






def load_data(coordinates: dict, force_download: bool = False, data_path: str = './data/') -> dict[Any, Any]:
    networks = {}

    for location in tqdm(coordinates, desc='Loading OSM-Data'):
        da.utils.make_folders(data_path, location)

        download = force_download
        try:
            with open(data_path + location + "/osm/raw_data.pickle", "rb") as file:
                new_network = pickle.load(file)
                logger.info("Loaded City %s from disk" % location)

        except FileNotFoundError:
            logger.info("%s.pickle not found" % location)
            download = True


        if download:
            logger.info("Starting download of %s" % location)
            new_network: curvy.Curvy = curvy.Curvy(*coordinates[location]['coords'],
                                             desired_railway_types = coordinates[location]['modes'],
                                             download=True, recurse='>')  # Liest die Tramstrecken aus
            new_network.save(data_path + location + "/osm/raw_data.pickle")
            logger.info("Saved %s as Pickle" % location)

        networks[location] = new_network

    return networks

def main(data_path: str = './data/', force_download: bool = False, generate_heights: bool = False):
    coords: dict = da.utils.load_csv_input(data_path=data_path, filename='cities.csv')
    logger.info('Beginning Loading Cities')
    netzwerke = load_data(coordinates= coords, force_download=force_download, data_path = data_path)

    logger.info('Cities added, generating DataFrames and calculating Heights.\n')
    for city in tqdm(netzwerke, desc='Generating Heights'):
        if force_download or not os.path.exists('%s%s/osm/processed.csv' % (data_path, city)) or generate_heights:
            network = netzwerke[city]
            df_linien = da.utils.generate_df(network, generate_heights=True)
            df_linien.reset_index(inplace=True)
            df_linien.to_csv(path_or_buf='%s%s/osm/processed.csv' % (data_path, city), index=False)
            logger.info('Heights for %s generated and <processed.csv> written' % city)

    return None

if __name__ == "__main__":
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(filename='myapp.log', level=logging.INFO, format=FORMAT)
    netze = main(force_download=False, generate_heights=False)



