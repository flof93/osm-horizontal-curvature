import pandas as pd
import osmnx as ox
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.transforms import Bbox

import math

import diplomarbeit as da


def calculate_phi(entropy: float, n_bins: int = 36) -> float:
    """
    Calculates phi according to Boeing, 2019 (doi: 10.1007/s41109-019-0189-1)

    :param entropy: Shannon's entropy for the given network
    :param n_bins: Number of Bins to categorize the Orientations into
    :return: Value of phi
    :rtype: float
    """
    return 1 - ((entropy - np.log(4)) / (math.log(n_bins) - np.log(4))) ** 2


def calc_entropy() -> None:
    """
    Downloads the street and tram networks from OSM using OSMnx,
    Calculates phi and adds it to building_results.json
    Creates Polar Histogram Plots for the orientations (for digital and print usage)
    :rtype: None
    """

    plt.rc('font', family='serif', size=11)
    plt.rc('text', usetex=True)

    ox.settings.use_cache = True

    cities_df = pd.read_csv(da.DATA_DIR / 'cities.csv', delimiter=';')
    cities_dict = cities_df[['Stadt', 'RailModes']].set_index('Stadt').to_dict()['RailModes']
    names_dict = cities_df[['Stadt', 'OSM-Name']].set_index('Stadt').to_dict()['OSM-Name']
    machine_dict = cities_df[['Stadt', 'machine_readable']].set_index('Stadt').to_dict()['machine_readable']

    # List to get is hardcoded -- retrieve List from cities.txt
    list_to_get = ['Amsterdam',
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

    dict_Gu_street = {}
    dict_Gu_tram = {}
    entropy_street = []
    entropy_tram = []
    city_axes = []

    n = len(list_to_get)
    ncols = 4
    nrows = int(np.ceil(n / ncols))
    figsize = (ncols * 5 * 1.75, nrows * 5)
    #fig, axes = plt.subplots(nrows, ncols, figsize=figsize, subplot_kw={"projection": "polar"})

    fig = plt.figure(figsize=figsize)
    gs0 = gridspec.GridSpec(nrows, ncols, figure=fig)

    ordered_list = sorted(list_to_get)

    print(ox.utils.ts(), 'Loading Data')
    for place in ordered_list:

        try:
            Gu_street = ox.io.load_graphml(da.DATA_DIR / machine_dict[place] / 'orientations' / 'street.graphml')
        except FileNotFoundError:
            print(ox.utils.ts(), 'Downloading Streets of', place)
            G_street = ox.graph.graph_from_place(names_dict[place], network_type="drive")
            Gu_street = ox.bearing.add_edge_bearings(ox.convert.to_undirected(G_street))
            ox.io.save_graphml(Gu_street, da.DATA_DIR / machine_dict[place] / 'orientations' / 'street.graphml')

        # get undirected graphs with edge bearing attributes

        entropy_street.append(ox.bearing.orientation_entropy(Gu_street))
        dict_Gu_street[place] = Gu_street
        # fig, ax = ox.plot.plot_orientation(Gu, ax=ax, title=place, area=True)

        try:
            Gu_tram = ox.io.load_graphml(da.DATA_DIR / machine_dict[place] / 'orientations' / 'tram.graphml')
        except FileNotFoundError:
            print(ox.utils.ts(), 'Downloading Trams of', place)
            if pd.isna(cities_dict[place]) or cities_dict[place] == 'tram, light_rail':
                filter_modes = '["railway"~"tram|light_rail"]'
            else:
                filter_modes = '["railway"~"' + cities_dict[place] + '"]'

            G_tram = ox.graph.graph_from_place(names_dict[place], custom_filter=filter_modes)
            Gu_tram = ox.bearing.add_edge_bearings(ox.convert.to_undirected(G_tram))
            ox.io.save_graphml(Gu_tram, da.DATA_DIR / machine_dict[place] / 'orientations' / 'tram.graphml')

        entropy_tram.append(ox.bearing.orientation_entropy(Gu_tram))
        dict_Gu_tram[place] = Gu_tram

    print(ox.utils.ts(), 'Starting Drawing Big picture')
    # draws all plots into one file -- for digital usage

    for grid, place in zip(gs0, ordered_list):
        gsi = grid.subgridspec(2, 2, height_ratios=[1, 10])
        axT = fig.add_subplot(gsi[0, :])
        axT.set_axis_off()
        axT.set_title(place, fontsize=22)
        ax1 = fig.add_subplot(gsi[1, 0], projection='polar')
        ox.plot.plot_orientation(dict_Gu_street[place], ax=ax1, title='Straßen', area=True, title_font={'size': 18},
                                 title_y=1.1)
        ax2 = fig.add_subplot(gsi[1, 1], projection='polar')
        ox.plot.plot_orientation(dict_Gu_tram[place], ax=ax2, title='Tram', area=True, color='r',
                                 title_font={'size': 18}, title_y=1.1)

        city_axes.append((place, [ax1, ax2]))

    # Draw once so tight bounding boxes are correct
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    fig.savefig(da.RESULTS_DIR / 'Orientations.png', dpi=300, bbox_inches='tight')

    #fig_landscape.savefig(da.DATA_DIR / machine_dict[place] / 'results' / "orientation_landscape.png", dpi=300, bbox_inches="tight")

    print(ox.utils.ts(), 'Drawing city Pictures')
    for place, axes in city_axes:
        bboxes = [ax.get_tightbbox(renderer) for ax in axes if ax.get_visible()]
        bbox = Bbox.union(bboxes)
        # Add a little padding
        bbox = bbox.expanded(1.03, 1.05)
        bbox = bbox.transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(da.RESULTS_DIR / 'Appendix_Results' / machine_dict[place] / "orientation_landscape.png", dpi=300,
                    bbox_inches=bbox)
        fig.savefig(da.DATA_DIR / machine_dict[place] / 'results' / "orientation_landscape.png", dpi=300,
                    bbox_inches=bbox)

    plt.close(fig)

    # Draw smaller Pictures
    # draws plots into two seperate files -- for printing
    print(ox.utils.ts(), 'Drawing smaller Picture')
    nrows_sml = int(np.ceil(n / 2 / ncols))
    figsize_sml = (ncols * 5 * 1.65, nrows_sml * 5)
    fig1 = plt.figure(figsize=figsize_sml)
    gs1 = gridspec.GridSpec(nrows_sml, ncols, figure=fig1)
    fig2 = plt.figure(figsize=figsize_sml)
    gs2 = gridspec.GridSpec(nrows_sml, ncols, figure=fig2)

    for grid, place in zip(gs1, ordered_list[:ncols * nrows_sml]):
        gsi = grid.subgridspec(2, 2, height_ratios=[1, 10])
        axT = fig1.add_subplot(gsi[0, :])
        axT.set_axis_off()
        axT.set_title(place, fontsize=22)
        ax1 = fig1.add_subplot(gsi[1, 0], projection='polar')
        ox.plot.plot_orientation(dict_Gu_street[place], ax=ax1, title='Straßen', area=True, title_font={'size': 18},
                                 title_y=1.1)
        ax2 = fig1.add_subplot(gsi[1, 1], projection='polar')
        ox.plot.plot_orientation(dict_Gu_tram[place], ax=ax2, title='Tram', area=True, color='r',
                                 title_font={'size': 18}, title_y=1.1)

    #fig1.canvas.draw()
    fig1.savefig(da.RESULTS_DIR / 'Orientations1.pdf', dpi=300, bbox_inches='tight')
    fig1.savefig(da.RESULTS_DIR / 'Orientations1.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)

    for grid, place in zip(gs2, ordered_list[ncols * nrows_sml:]):
        gsi = grid.subgridspec(2, 2, height_ratios=[1, 10])
        axT = fig2.add_subplot(gsi[0, :])
        axT.set_axis_off()
        axT.set_title(place, fontsize=22)
        ax1 = fig2.add_subplot(gsi[1, 0], projection='polar')
        ox.plot.plot_orientation(dict_Gu_street[place], ax=ax1, title='Straßen', area=True, title_font={'size': 18},
                                 title_y=1.1)
        ax2 = fig2.add_subplot(gsi[1, 1], projection='polar')
        ox.plot.plot_orientation(dict_Gu_tram[place], ax=ax2, title='Tram', area=True, color='r',
                                 title_font={'size': 18}, title_y=1.1)
    fig2.savefig(da.RESULTS_DIR / 'Orientations2.pdf', dpi=300, bbox_inches='tight')
    fig2.savefig(da.RESULTS_DIR / 'Orientations2.png', dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # Calculate phi
    entropy_df = pd.DataFrame({'Stadt': ordered_list, 'H0_strasse': entropy_street, 'H0_tram': entropy_tram})
    entropy_df['phi_street'] = calculate_phi(entropy_df['H0_strasse'])
    entropy_df['phi_tram'] = calculate_phi(entropy_df['H0_tram'])
    entropy_df.to_csv(da.DATA_DIR / 'Orientations.csv', index=False)


if __name__ == '__main__':
    calc_entropy()
