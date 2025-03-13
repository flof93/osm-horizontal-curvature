import csv

import curvy
from matplotlib import pyplot as plt
import scipy
import numpy as np
import pickle
import pandas as pd

import logging.config

from curvy import Curvy

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

def load_data(coordinates: dict):
    networks = {}
    n = 0
    for location in coordinates:
        try:
            with open("Pickles/" + location + ".pickle", "rb") as file:
                new_network = pickle.load(file)

        except FileNotFoundError as msg:
            print(location + ".pickle not found - Starting download")
            new_network: Curvy = curvy.Curvy(*coordinates[location]['coords'],
                                             desired_railway_types = coordinates[location]['modes'],
                                             download=True)  # Liest die Tramstrecken aus
            new_network.save("Pickles/" + location + ".pickle")

        networks[location] = new_network
        n += 1

        print(location + " added, " + str(int(n / len(coordinates) * 100)) + "% done")
    return networks

def load_curvy_input(file_path: str) -> dict:
    """loads a csv-File with Cities and returns a dictionary"""
    out_dict = {}
    with open(file_path, newline='') as csvfile:
        data = csv.DictReader(csvfile, delimiter=";", quotechar='\'', quoting=csv.QUOTE_NONNUMERIC)
        for row in data:
            out_dict[row['Stadt']]={'coords':(row['West'],row['Sued'],row['Ost'],row['Nord']),
                                    'modes':row['Rail Modes'].split(',')}
    return out_dict





if __name__ == "__main__":
    logging.basicConfig(filename='myapp.log', level=logging.INFO)

    # coords = {}
    # coords["Wien"]= (16, 48, 17, 48.5) #, # Koordinaten Wiens
    # coords["Graz"]= (15, 46.9, 15.6, 47.2)
    # coords["Innsbruck"]= (11.25, 47.2, 11.5, 47.4)
    # coords["Linz"]= (14, 48, 14.5, 48.5)
    # coords["Berlin"] = (12.7, 52.2, 14.1, 52.9)
    # coords["Gmunden"] = (13.77, 47.90, 14, 48)
    # coords["Prag"] = (14, 49.5, 15, 50.5)
    # coords["Brno"] = (16.4, 49.05, 16.8, 49.35)
    # # coords["Budapest"] = (18.8, 47.30, 19.40, 47.70)
    # coords["Mailand"] = (9.0, 45.30, 9.35, 45.60)
    # coords["San Francisco"] = (-123.2,37.5,-122.25,38)

    coords=load_curvy_input('cities.csv')

    netzwerke = load_data(coords)
    stadt, linie, richtung, dist, curvature, gauge = [], [], [], [], [], []
    for i in netzwerke:
        network = netzwerke[i]
        #line_draw = network.railway_lines[0]
        #plt_line(line_draw)
        #plt_curvature(line_draw)
        #plt_line_curvature(line_draw)
        #plt_network(network, city=i)
        #fig, ax = plt.subplots(10, 10)
        for j in network.railway_lines:
            curv=max(j.gamma)/(max(j.s)/1000)
            #print(str(j) + " Kurvigkeit: " + str(curv) + " gon/km")
            #plt_line_curvature(j)
            #a=j[0]//10
            #b=j[0]%10
            #ax[a,b].plot(network.railway_lines[j[0]].s, network.railway_lines[j[0]].dgamma)
            stadt.append(i)
            linie.append(j.ref)
            richtung.append(str(j))
            dist.append(max(j.s)/1000)
            curvature.append(curv)
            try:
                gauge.append(int(j.ways[0].tags['gauge']))
            except KeyError:
                gauge.append(np.nan)
            #except TypeError: # könnte relevant sein, wenn die Linie im Dreischienengleis startet



        plt.show()

    d={"Stadt":stadt, "Linie":linie, "Richtung":richtung, "Distanz":dist, "Kurvigkeit":curvature, 'Spurweite':gauge}
    df=pd.DataFrame(data=d)
    pt_cities = pd.pivot_table(data=df,
                               values=["Kurvigkeit", "Distanz"],
                               index=["Stadt",'Spurweite'],
                               aggfunc={'Kurvigkeit':'mean', 'Distanz':('sum','mean')})
    pt_gauge = pd.pivot_table(data=df, values=["Kurvigkeit", "Distanz"], index="Spurweite", aggfunc='mean')
    print(pt_cities)
    print(pt_gauge)


