from pathlib import Path
import contextily as cx
import geopandas as gpd
import pandas as pd
import shapely.geometry as shp
from matplotlib import pyplot as plt
import geodatasets
import numpy as np

import diplomarbeit as da

from sklearn.linear_model import LinearRegression

import seaborn as sns

import osmnx as ox

DATA_DICT = Path('../data')
STADIA_API = 'ccf6fac2-c284-43e8-b9f2-83716f034ba2'
RESULTS_DIR = Path('../results')  # TODO: Make LaTeX-Picture directory for Production
COLUMN_NAMES_DE = {'curvature': 'Kurvigkeit [gon/km]',
                   'avg_dist': 'Durchschnittlicher Haltestellenabstand [m]',
                   'trip_speed': 'Durchschnittsgeschwindigkeit [km/h]',
                   'height_up': 'Aufstieg [m/km]',
                   'height_down': 'Abstieg [m/km]',
                   'rho_b': 'Bebauungsdichte [-]'}

COLUMN_NAMES_TEX = {'curvature': r'$\bar\gamma$' + '\n' + r'[gon/km]',
                    'avg_dist': r'$\bar l_{Hst}$' + '\n' + r'[m]',
                    'trip_speed': r'$\bar V$' + '\n' + r'[km/h]',
                    'height_up': r'$\bar s^{\uparrow}$' + '\n' + r'[\textperthousand]',
                    'height_down': r'$\bar s^{\downarrow}$' + '\n' + r'[\textperthousand]',
                    'rho_b': r'$\rho_B$' + '\n' + r'[1]'}

COLUMN_NAMES_TEX_SHORT = {'curvature': r'$\bar\gamma$',
                          'avg_dist': r'$\bar l_{Hst}$',
                          'trip_speed': r'$\bar V$',
                          'height_up': r'$\bar s^{\uparrow}$',
                          'height_down': r'$\bar s^{\downarrow}$',
                          'rho_b': r'$\rho_B$'}


def add_alidade_smooth(ax, crs=None):
    provider = cx.providers.Stadia.AlidadeSmooth(api_key=STADIA_API)
    provider["url"] = provider["url"] + "?api_key={api_key}"
    cx.add_basemap(ax, crs=crs, url=cx.providers.CartoDB.Positron, zoom=5)  #source=provider)


def make_geograph_net():
    results_df = gpd.read_file(DATA_DICT / 'building_data.json')
    cities_df = pd.read_csv(DATA_DICT / 'cities.csv', sep=';')

    df_res_vie = results_df[results_df['machine_readable'] == 'wien']
    cities_vie = cities_df[cities_df['machine_readable'] == 'wien']

    df_box_vie = gpd.GeoDataFrame({'geometry': [shp.box(float(cities_vie['West'].iloc[0]),
                                                        float(cities_vie['Sued'].iloc[0]),
                                                        float(cities_vie['Ost'].iloc[0]),
                                                        float(cities_vie['Nord'].iloc[0]))]}, crs='EPSG:4326')

    fig, ax = plt.subplots(1, 1, figsize=(5, 5))
    df_res_vie.plot(ax=ax, color='r')
    df_box_vie.boundary.plot(ax=ax, color='r')
    #ax=df_res_vie.plot(cmap='gist_rainbow', figsize=(10,10))

    fig = ax.get_figure()
    ax.set_box_aspect(1)

    ax.set_axis_off()

    # provider = cx.providers.Stadia.AlidadeSmooth(api_key=STADIA_API)
    # provider["url"] = provider["url"] + "?api_key={api_key}"
    # cx.add_basemap(ax, crs=df_res_vie.crs, source=provider)

    add_alidade_smooth(ax, crs=df_res_vie.crs)

    fig.savefig('../temp/wien.png', bbox_inches='tight', pad_inches=0.2)


def make_city_table(data: gpd.GeoDataFrame):
    agg_func = {'distance': ['mean', 'sum'],
                'trip_speed': ['mean'],
                'number_trips': ['sum'],
                'avg_dist': ['mean'],
                'rho_b': ['mean'],
                'machine_readable': ['count'],
                'Stadt': 'first',
                'ISO3166': 'first'}

    grouped = data[['Stadt', 'distance', 'trip_speed', 'number_trips', 'avg_dist', 'rho_b', 'ISO3166',
                    'machine_readable']].groupby(by=['ISO3166', 'Stadt']).aggregate(func=agg_func)
    grouped.rename(columns={'machine_readable': 'Anzahl Relationen'}, inplace=True)
    grouped.rename_axis(['ISO3166', 'Stadt']).reset_index(inplace=True)
    grouped.columns = grouped.columns.droplevel(1)
    header = ['Land', 'Stadt', r'$n_{{Linien}}$', r'$\bar V$ [\unit{{\kilo\metre\per\hour}}]',
              r'$\bar l_{{Hst}}$ [\unit{{\metre}}]']
    df_out = grouped.drop(columns='distance').reindex(
        ['ISO3166', 'Stadt', 'Anzahl Relationen', 'trip_speed', 'avg_dist'],
        axis=1)
    df_out.to_latex(RESULTS_DIR / 'cities.tex',
                    columns=['ISO3166', 'Stadt', 'Anzahl Relationen', 'trip_speed', 'avg_dist'],
                    index=False,
                    header=header,
                    float_format="%.2f",
                    column_format='llSSS')
    return grouped


def make_worldmap(data: gpd.GeoDataFrame):
    world = gpd.read_file(geodatasets.get_path("naturalearth.land"))

    grouped = data[['geometry', 'Stadt']].dissolve(by='Stadt')
    grouped.to_crs('EPSG:4087', inplace=True)
    grouped['center'] = grouped.centroid
    grouped.set_geometry('center')
    grouped.to_crs('EPSG:4326', inplace=True)

    fig, ax = plt.subplots()  #1, 1, figsize=(12, 9))
    world.to_crs(crs=grouped.crs).plot(ax=ax, alpha=0.2, color="grey")
    grouped.plot(ax=ax, color='r', marker='+', markersize=5)

    #fig=ax.get_figure()
    #ax.set_axis_off()
    #add_alidade_smooth(ax, crs=grouped.crs)

    #fig.set_size_inches(10, 3)

    fig.savefig(RESULTS_DIR / 'worldmap.png', bbox_inches='tight', pad_inches=0.2, dpi=600)


def paired_density_and_scatterplot(data: gpd.GeoDataFrame | pd.DataFrame):
    g = sns.PairGrid(data=data, diag_sharey=False)
    g.map_upper(sns.scatterplot, s=15, color='C0')
    g.map_diag(sns.kdeplot, lw=2, color='C1')
    g.map_lower(sns.kdeplot, linewidths=1, color='C2')
    return g


def correlation_heatmap(data: gpd.GeoDataFrame):
    sns.set_style('white')
    corr = data.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool), 1)
    g = sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5, vmin=-1, vmax=1, mask=mask,
                    square=True, cbar_kws={"shrink": .8})
    #g.set_title('Korrelationsmatrix')
    g.set_yticklabels(labels=g.get_yticklabels(), va='center')
    return g


def add_subplot(data: pd.DataFrame, x: tuple[str, str], y: tuple[str, str], subaxis: int, axs: plt.Axes) -> None:
    model = LinearRegression(fit_intercept=True)
    data_unabh = data[[x[0]]]
    model.fit(X=data_unabh, y=data[y[0]])
    x_between = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
    fx = model.predict(X=x_between)
    r_square = model.score(X=data_unabh, y=data[y[0]])

    data.plot.scatter(x=x[0], y=y[0], ax=axs[subaxis])  # , marker='x', s=10, c="navy")
    intercept_pre= '+' if model.intercept_>0 else ''
    axs[subaxis].plot(x_between[:, 0], fx, c="red",
                      label="y={0:.4f}x{3}{1:.2f}\nR²={2:.2f}".format(model.coef_[0], model.intercept_, r_square, intercept_pre))
    axs[subaxis].set_xlabel(x[1])
    axs[subaxis].set_ylabel(y[1])
    axs[subaxis].legend()
    return None


def make_city_diags(data: gpd.GeoDataFrame):
    sns.set_style('darkgrid')

    x_axis = [('curvature', COLUMN_NAMES_TEX['curvature']),
              ('avg_dist', COLUMN_NAMES_TEX['avg_dist']),
              #('height_up', 'Durchschnittlicher\nAufstieg [m/km]'),
              #('rho_b', 'Bebauungsdichte'),
              ]

    y_axis = [('trip_speed', COLUMN_NAMES_TEX['trip_speed']),
              ]

    for i in data['city'].unique():
        city_data = data[data['city'] == i]

        fig, axs = plt.subplots(nrows=1, ncols=len(x_axis), sharey=True, figsize=(len(x_axis) * 5, 5))
        #fig.suptitle(city_data['Stadt'].unique()[0], fontsize=16)

        axs[0].set_ylim(0, 40)

        for j in range(len(x_axis)):
            max = data.dropna(axis='index')[x_axis[j][0]].max()
            if max < 1:
                axs[j].set_xlim(0, da.utils.round_up(max, 1))
            else:
                axs[j].set_xlim(0, da.utils.round_up(max, -1))

            add_subplot(data=city_data, x=x_axis[j], y=y_axis[0], subaxis=j, axs=axs)

        plt.savefig(fname=DATA_DICT / i / 'results' / 'corr.png', bbox_inches='tight', pad_inches=0.2)
        plt.close()


if __name__ == '__main__':
    data = gpd.read_file(DATA_DICT / 'building_data.json').dropna(axis='index')
    data_de = data.rename(columns=COLUMN_NAMES_DE)
    data_tex = data[['curvature', 'height_up', 'height_down', 'trip_speed', 'avg_dist', 'rho_b']].rename(
        columns=COLUMN_NAMES_TEX)
    data_tex_short = data[['curvature', 'height_up', 'height_down', 'trip_speed', 'avg_dist', 'rho_b']].rename(
        columns=COLUMN_NAMES_TEX_SHORT)

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')

    make_city_table(data)
    #make_geograph_net()
    #make_worldmap(data)

    make_city_diags(data)

    g = paired_density_and_scatterplot(data_tex)
    g.figure.savefig(RESULTS_DIR / 'paired_density_and_scatterplot.png', dpi=600, bbox_inches='tight')
    plt.close(g.figure)

    g = correlation_heatmap(data_tex_short)
    g.figure.savefig(RESULTS_DIR / 'correlation_heatmap.png', dpi=600, bbox_inches='tight')
