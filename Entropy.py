import pandas as pd
import osmnx as ox
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import diplomarbeit as da

from matplotlib.transforms import Bbox
import math


RESULTS_DIR = Path('./results')  # TODO: Make LaTeX-Picture directory for Production

plt.rc('font', family='serif', size=11)
plt.rc('text', usetex=True)

cm = 1/2.54

ox.settings.use_cache = True

cities_df = pd.read_csv('./data/cities.csv', delimiter=';')
cities_dict=cities_df[['Stadt', 'RailModes']].set_index('Stadt').to_dict()['RailModes']
names_dict=cities_df[['Stadt', 'OSM-Name']].set_index('Stadt').to_dict()['OSM-Name']
machine_dict=cities_df[['Stadt', 'machine_readable']].set_index('Stadt').to_dict()['machine_readable']

list_to_get=['Amsterdam',
 'Antwerpen',
 'Berlin',
 'Bordeaux',
 'Brandenburg a. d. Havel',
 'Brüssel',
 'Budapest',
 'Bukarest',
 'Den Haag',
 'Freiburg',
 'Gent',
 'Göteborg',
 'Graz',
 'Helsinki',
 'Innsbruck',
 'Katowice',
 'Köln',
 'Linz',
 'Lviv',
 'Lyon',
 'Mailand',
 'Manchester',
 'Melbourne',
 'München',
 'Portland',
 'Potsdam',
 'Prag',
 'Riga',
 'Rom',
 'Rotterdam',
 'San Francisco',
 'Sankt Petersburg',
 'Sofia',
 'Stuttgart',
 'Turin',
 'Toronto',
 'Ulm',
 'Warschau',
 'Wien',
 'Zagreb',
 'Zürich']

def calculate_phi(entropy:float, n_bins:int=36)->float:
    return 1-((entropy-1.386)/(math.log(n_bins)-1.386))**2



entropy_street=[]
entropy_tram=[]
city_axes = []

n = len(list_to_get)
ncols = int(np.ceil(np.sqrt(n/2)))
nrows = int(np.ceil(n / ncols))
figsize = (ncols * 5 * 1.75, nrows * 5)
#fig, axes = plt.subplots(nrows, ncols, figsize=figsize, subplot_kw={"projection": "polar"})

fig=plt.figure(figsize=figsize)
gs0 = gridspec.GridSpec(nrows, ncols, figure=fig)

ordered_list=sorted(list_to_get)

for grid, place in zip(gs0, ordered_list):
    print(ox.utils.ts(), place)

    # get undirected graphs with edge bearing attributes
    G_street = ox.graph.graph_from_place(names_dict[place], network_type="drive")
    Gu_street = ox.bearing.add_edge_bearings(ox.convert.to_undirected(G_street))
    entropy_street.append(ox.bearing.orientation_entropy(Gu_street))
    #fig, ax = ox.plot.plot_orientation(Gu, ax=ax, title=place, area=True)

    if pd.isna(cities_dict[place]) or cities_dict[place] == 'tram, light_rail':
        filter_modes='["railway"~"tram|light_rail"]'
    else:
        filter_modes='["railway"~"'+cities_dict[place]+'"]'

    G_tram = ox.graph.graph_from_place(names_dict[place], custom_filter = filter_modes)
    Gu_tram = ox.bearing.add_edge_bearings(ox.convert.to_undirected(G_tram))
    entropy_tram.append(ox.bearing.orientation_entropy(Gu_tram))

    gsi=grid.subgridspec(2, 2, height_ratios=[1,10])
    axT = fig.add_subplot(gsi[0,:])
    axT.set_axis_off()
    axT.set_title(place, fontsize=22)
    ax1 = fig.add_subplot(gsi[1,0], projection='polar')
    ox.plot.plot_orientation(Gu_street, ax=ax1, title='Straßen', area=True, title_font={'size':18}, title_y=1.1)
    ax2 = fig.add_subplot(gsi[1,1],projection='polar')
    ox.plot.plot_orientation(Gu_tram, ax=ax2, title='Tram', area=True, color='r', title_font={'size':18}, title_y=1.1)

    city_axes.append((place, [ax1, ax2]))

# Draw once so tight bounding boxes are correct
fig.canvas.draw()
renderer = fig.canvas.get_renderer()

fig.savefig(RESULTS_DIR / 'Orientations.png', dpi=100, bbox_inches='tight')

entropy_df=pd.DataFrame({'Stadt':ordered_list,'H0_strasse':entropy_street, 'H0_tram':entropy_tram})
entropy_df['phi_street']=calculate_phi(entropy_df['H0_strasse'])
entropy_df['phi_tram']=calculate_phi(entropy_df['H0_tram'])
entropy_df.to_csv(RESULTS_DIR / 'Orientations.csv', index=False)

#fig_landscape.savefig(da.DATA_DICT / machine_dict[place] / 'results' / "orientation_landscape.png", dpi=300, bbox_inches="tight")


for place, axes in city_axes:
    bboxes = [ax.get_tightbbox(renderer) for ax in axes if ax.get_visible()]
    bbox = Bbox.union(bboxes)
    # Add a little padding
    bbox = bbox.expanded(1.03, 1.05)
    bbox = bbox.transformed(fig.dpi_scale_trans.inverted())
    fig.savefig(da.DATA_DICT / machine_dict[place] / 'results' / "orientation_landscape.png", dpi=300, bbox_inches=bbox)