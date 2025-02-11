import curvy
from matplotlib import pyplot as plt
import scipy

coords={"Wien":(16, 48, 16.75, 48.5)} # Koordinaten Wiens
#curvy.download_track_data()


# for i in curvy.railway_lines:
#     line = i
#     lower, upper = line.get_error_bounds()
#

def plt_line_curvature(line, error_bounds = False, filter_savgol = False, savgol_win_l = 51, savgol_poly_o = 3):

    fig, ax = plt.subplots(1, 1)

    ax.set_xlabel("Distances s [m]")
    ax.set_ylabel("Curvature c [m]")

    ax.plot(line.s, line.c)
    if error_bounds:
        lower, upper = line.get_error_bounds()
        ax.plot(line.s, lower)
        ax.plot(line.s, upper)

    if filter_savgol:
        sav_gol = scipy.signal.savgol_filter(line.c, savgol_win_l, savgol_poly_o)
        ax.plot(line.s, sav_gol)

    ax.grid()

    plt.suptitle(line.name)

    plt.show()

if __name__ == "__main__":
    curvy = curvy.Curvy(*coords["Wien"],
                        desired_railway_types=["tram"],
                        download=True)  # Liest die Tramstrecken Wiens aus
    print("Download finished")
    line_draw = curvy.railway_lines[0]
    plt_line_curvature(line_draw)


