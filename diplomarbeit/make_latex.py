from pathlib import Path
import contextily as cx
import geopandas as gpd
import pandas as pd
import shapely.geometry as shp
from matplotlib import pyplot as plt

import osmnx as ox

DATA_DICT = Path('../data')
STADIA_API = 'ccf6fac2-c284-43e8-b9f2-83716f034ba2'

def make_geograph_net():

    results_df = gpd.read_file(DATA_DICT / 'building_data.json')
    cities_df = pd.read_csv(DATA_DICT / 'cities.csv', sep=';')

    df_res_vie = results_df[results_df['machine_readable']=='wien']
    cities_vie = cities_df[cities_df['machine_readable']=='wien']

    df_box_vie = gpd.GeoDataFrame({'geometry': [shp.box(float(cities_vie['West'].iloc[0]),
                                                       float(cities_vie['Sued'].iloc[0]),
                                                       float(cities_vie['Ost'].iloc[0]),
                                                       float(cities_vie['Nord'].iloc[0]))]}, crs='EPSG:4326')

    fig, ax = plt.subplots(1,1, figsize=(5,5))
    df_res_vie.plot(ax=ax, color='r')
    df_box_vie.boundary.plot(ax=ax, color='r')
    #ax=df_res_vie.plot(cmap='gist_rainbow', figsize=(10,10))

    fig=ax.get_figure()
    ax.set_box_aspect(1)

    ax.set_axis_off()


    provider = cx.providers.Stadia.AlidadeSmooth(api_key=STADIA_API)
    provider["url"] = provider["url"] + "?api_key={api_key}"
    cx.add_basemap(ax, crs=df_res_vie.crs, source=provider)

    fig.savefig('../temp/wien.png', bbox_inches='tight', pad_inches=0.2)


if __name__ == '__main__':
    #make_geograph_net()

