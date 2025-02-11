import curvy
from matplotlib import pyplot as plt

coords={"Wien":(16, 48, 16.75, 48.5)} # Koordinaten Wiens
curvy = curvy.Curvy(*coords["Wien"], desired_railway_types=["tram"], download=True) # Liest die Tramstrecken Wiens aus
#curvy.download_track_data()
print("Download finished")

# for i in curvy.railway_lines:
#     line = i
#     lower, upper = line.get_error_bounds()
#

def plt_line_curvature(line):
    lower, upper = line.get_error_bounds()

    fig, ax = plt.subplots(1, 1)

    ax.plot(line.s, line.c)
    ax.plot(line.s, lower)
    ax.plot(line.s, upper)

    ax.set_xlabel("Distances s [m]")
    ax.set_ylabel("Curvature c [m]")
    ax.grid()

    plt.suptitle(line.name)
    plt.show()


line = curvy.railway_lines[0]
plt_line_curvature(line)


