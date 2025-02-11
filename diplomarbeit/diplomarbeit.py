import curvy
from matplotlib import pyplot as plt
import scipy
import numpy as np

from curvy import Curvy

coords={"Wien":(16, 48, 17, 48.5)} # Koordinaten Wiens
#curvy.download_track_data()


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
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(line.x, line.y, color=line.color)
    ax[1].plot(line.s, line.c)
    ax.grid()

def plt_network(network : Curvy):
    fig, ax = plt.subplots()
    for line in network.railway_lines:
        ax.plot(line.lon,line.lat,color=line.color)
    ax.grid()
    #ax.set_aspect('equal', adjustable='box')
    plt.show()




def calc_dist(line):
    dist=[]
    for i in line.s:
        if i == 0:
            dist.append(0)
        else:
            dist.append(line.s[i]-line.s[i-1]) # Error: i is np.float64 not list


if __name__ == "__main__":
    wien_network: Curvy = curvy.Curvy(*coords["Wien"],
                        desired_railway_types=["tram"],
                        download=True)  # Liest die Tramstrecken Wiens aus
    print("Download finished")
    line_draw = wien_network.railway_lines[0]
    #plt_line(line_draw)
    #plt_curvature(line_draw)
    #plt_line_curvature(line_draw)
    #plt_network(wien_network)


