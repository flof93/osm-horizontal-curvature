import os.path
from pathlib import Path

import osmnx as ox
import geopandas as gpd
import pandas as pd

import shapely as shp

import requests.exceptions
from concurrent.futures import ThreadPoolExecutor

from geopandas import GeoDataFrame


def calculate_buffer_width(city: str) -> float:
    """
    Calculates the mean edge length of a street network of city
    :param city: city name to get street network and calculate mean edge length
    :return: mean edge length of street network
    """
    graph = ox.graph.graph_from_place(city, network_type='drive')
    d = pd.Series([d['length'] for u, v, d in graph.edges(data=True)])
    return d.median()


def get_buffer_line(gdf: gpd.GeoDataFrame, width: str, inplace: bool = False) -> gpd.GeoSeries:
    """
    Calculates Buffers around the geometry of gdf with given width
    :param gdf: gepandas.GeoDataFrame to calculate buffers for
    :param width: column in gdf, where buffer width for geometry is given
    :param inplace: if True: add buffer geometry to gdf (in column 'buffer_geometry').
    :return: geopandas.GeoSeries containing only buffer geometries
    """

    tmp_series = gpd.GeoSeries(data=[], crs=gdf.crs)
    print('Berechne Buffer-Geometrie')
    for idx, row in gdf.iterrows():
        #print(ox.utils.ts(), '-', row['Stadt'], '-', row['line_name'])
        gdf_wgs = gpd.GeoDataFrame(data={'geometry': [row['geometry']]}, crs=gdf.crs)
        try:
            utm_zone = gdf_wgs.estimate_utm_crs()
            buffer_wgs = gdf_wgs.to_crs(utm_zone).buffer(distance=row[width]).to_crs(crs=gdf.crs).geometry
        except ValueError:
            buffer_wgs = gpd.GeoSeries(pd.NA)

        tmp_series = pd.concat([tmp_series, buffer_wgs])

    tmp_series.reset_index(drop=True, inplace=True)
    if inplace:
        gdf['buffer_geometry'] = tmp_series
    return tmp_series


def make_download_gdf_poly(gdf: gpd.GeoDataFrame, width: str, data_path: str = './data/') -> gpd.GeoDataFrame:
    """
    Not used in production!
    Dissolves all buffer geometries in gdf for each city and writes it to download_polys.json
    :param gdf: geopandas.Geodataframe
    :param width: column in gdf, where buffer width for geometry is given
    :param data_path: path to data directiory
    :return: geodataframe with dissolved geometries on city level
    """
    print('Erzeuge Download-Polys')
    #download_buffer = get_buffer_line(gdf=gdf, width=width, inplace=True)
    if 'buffer_geometry' not in gdf:
        download_buffer = get_buffer_line(gdf=gdf, width=width, inplace=True)
    else:
        download_buffer = gdf

    download_buffer.set_geometry(col='buffer_geometry', inplace=True)
    download_buffer_agg = download_buffer.dissolve(by='machine_readable', as_index=False)[
        ['machine_readable', 'buffer_geometry', 'Stadt']]
    download_buffer_agg['buffer_simp'] = download_buffer_agg.to_crs('EPSG:4087').simplify_coverage(1)
    agg_data = download_buffer_agg[['machine_readable', 'buffer_simp', 'Stadt']].set_geometry(col='buffer_simp')
    agg_data = agg_data.to_crs('EPSG:4326')
    agg_data.to_file(data_path + 'download_polys.json')
    return agg_data


def make_download_gdf_bbox(gdf: gpd.GeoDataFrame, width: str, data_path: str = './data/') -> gpd.GeoDataFrame:
    """
    Not used in production!
    Dissolves all bounding boxes of buffer geometries in gdf for each city and writes it to download_polys.json
    :param gdf: geopandas.Geodataframe
    :param width: column in gdf, where buffer width for geometry is given
    :param data_path: path to data directiory
    :return: geodataframe with dissolved bboxes of line buffers on city level
    """
    print('Erzeuge Download-BBox')
    if 'buffer_geometry' not in gdf:
        download_buffer = get_buffer_line(gdf=gdf, width=width, inplace=True)
    else:
        download_buffer = gdf

    download_buffer = pd.concat([download_buffer, download_buffer.bounds], axis=1)

    boxes = gpd.GeoSeries([], crs='EPSG:4326')
    for idx, row in download_buffer.iterrows():
        box = shp.box(row['minx'], row['miny'], row['maxx'], row['maxy'])
        box_gs = gpd.GeoSeries([box], crs='EPSG:4326')
        boxes = pd.concat([boxes, box_gs])

    boxes.reset_index(drop=True, inplace=True)
    download_buffer['buffer_boxes'] = boxes

    download_buffer.set_geometry(col='buffer_boxes', inplace=True)
    download_buffer_agg = download_buffer.dissolve(by='machine_readable', as_index=False)[
        ['machine_readable', 'buffer_boxes', 'Stadt']]
    download_buffer_agg['buffer_simp'] = download_buffer_agg.to_crs('EPSG:4087').simplify_coverage(1)
    agg_data = download_buffer_agg[['machine_readable', 'buffer_simp', 'Stadt']].set_geometry(col='buffer_simp')
    agg_data = agg_data.to_crs('EPSG:4326')
    agg_data.to_file(data_path + 'download_polys.json')
    return agg_data


def download_buildings_along_lines(agg_gdf: gpd.GeoDataFrame, data_path: str = './data/', timeout: int = 180) -> None:
    """
    Not used in production!
    Downloads building data from OSM using OSMnx (OSM features tagged with 'building')
    :param agg_gdf: geopandas.GeoDataFrame containing borders to download in geometry.
    :param data_path: Path to the data directory
    :param timeout: Timeout in seconds for downloading data from OSM
    """
    print('Downloading Building Data')
    ox.settings.requests_timeout = timeout
    for i, row in agg_gdf.iterrows():
        city = row['machine_readable']
        if os.path.exists(data_path + city + '/buildings/city_buildings.shp'):
            continue
        print(ox.utils.ts(), '-', row['Stadt'])
        try:
            payload = ox.features_from_polygon(polygon=row['buffer_simp'], tags={'building': True})['geometry']
        except requests.exceptions.ReadTimeout:
            print(row['Stadt'], ': Timeout!')
            continue
        payload.to_file(filename=data_path + city + '/buildings/city_buildings.geojson', use_arrow=True,
                        driver='GeoJSON')


def download_buildings_bbox(data_path: Path, filename: str = 'cities.csv', force_download: bool = False) -> None:
    """
    Downloads all buildings in the box given in filename (usually cities.csv) for each City in filename.
    filename must contain 4 columns ('West', 'South', 'North', 'Ost').
    :rtype: None (Saves downloaded Data to 'buildings / city_buildings.json' in the respective city's directory.)
    :param data_path: Path to the data directory
    :param filename: Filename to read Cities from.
    :param force_download: bool: if True: forces a redownload of all cities, even if a file already exists
    """
    data = pd.read_csv(data_path / filename, sep=';')
    print('Downloading Building Data')
    for idx, row in data.iterrows():
        city = row['machine_readable']
        if force_download or not os.path.exists(data_path / city / 'buildings' / 'city_buildings.json'):
            print(ox.utils.ts(), '-', row['Stadt'])
            bbox = shp.box(float(row['West']), float(row['Sued']), float(row['Ost']), float(row['Nord']))
            bbox_enl = ox.utils_geo.buffer_geometry(bbox, data['Buffer_Width'].max())
            payload = ox.features_from_bbox(bbox=shp.total_bounds(bbox_enl), tags={'building': True})
            city = row['machine_readable']
            data_to_save = payload[payload['geometry'].type.isin({"Polygon", "MultiPolygon"})]['geometry']
            data_to_save.to_file(filename=data_path / city / 'buildings' / 'city_buildings.json')


def process_city(city: str, data: gpd.GeoDataFrame, data_path: Path|str) -> GeoDataFrame:
    """
    Helper function to clip the building data from a bigger area to only the wanted line buffers.
    Dissolves line buffers into one geometry for each line.
    :param city: City to read building data from disk
    :param data: gpd.GeoDataFrame containing buffer geometries
    :param data_path: Path to the data directory
    :return: Building data for each line
    :rtype: GeoDataFrame
    """
    clipped_df = gpd.GeoDataFrame(data={'geometry': [], 'Stadt': [], 'line_name': []}, crs=data.crs)
    print(ox.utils.ts(), '-', city)
    if os.path.exists(data_path + city + '/buildings/city_buildings.json'):
        buildings: gpd.GeoDataFrame = gpd.read_file(data_path + city + '/buildings/city_buildings.json')
    else:
        return clipped_df

    for idx, row in data[data['machine_readable'] == city].iterrows():
        try:
            clipped_line = buildings.clip(mask=row['buffer_geometry'])
        except TypeError:
            clipped_line = gpd.GeoDataFrame({'geometry': [pd.NA], 'element': [pd.NA], 'id': [pd.NA]}, crs=data.crs)
        clipped_line['Stadt'] = row['Stadt']
        clipped_line['line_name'] = row['line_name']
        clipped_line.drop(labels=['element', 'id'], axis="columns", inplace=True)
        clipped_df = pd.concat([clipped_df, clipped_line], ignore_index=True)
    clipped_df = clipped_df.dissolve(by='line_name', as_index=False)
    return clipped_df


def clip_lines(data: gpd.GeoDataFrame, data_path: str | Path = './data/') -> GeoDataFrame:
    """
    Parallelized function call of process city.
    :param data: gpd.GeoDataFrame containing buffer geometries
    :param data_path: Path to the data directory
    :return: All building geometries along each line
    :rtype: GeoDataFrame
    """
    cities = data['machine_readable'].unique()
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_city, city, data, data_path) for city in cities]
        results = [f.result() for f in futures]
    clipped_df = pd.concat(results, ignore_index=True)
    data = data.merge(right=clipped_df.rename_geometry(col='clipped_buildings'))
    return data


def calc_building_density(data: gpd.GeoDataFrame, inplace: bool = False, cleanup: bool = False) -> list:
    """
    Calculates building densities ('rho_b') along each line.
    :param data: GeoDataFrame containing dissolved building geometries
    :param inplace: if True: adds column 'rho_b' in data
    :param cleanup: if inplace and cleanup are True: drops buffer_geometry and  building data columns to save space.
    :return: list containing building densities
    """
    data.to_crs('EPSG:6933')
    densities = data['clipped_buildings'].area / data['buffer_geometry'].area * 100
    if inplace:
        data['rho_b'] = densities
    if cleanup and inplace:
        data.drop(labels=['buffer_geometry', 'clipped_buildings'], axis='columns', inplace=True)
    return densities


def calc_main(data_dict: Path) -> None:
    """
    Calls all necessary functions to calculate building densities.
    Writes final Data to building_data.json in data_dict.
    :param data_dict: Path to the data directory
    """
    data = gpd.read_file(data_dict / 'results.json')
    download_buildings_bbox(data_path=data_dict)
    get_buffer_line(data, 'Buffer_Width', True)
    data = clip_lines(data=data)
    calc_building_density(data=data, inplace=True, cleanup=True)
    data.to_file(data_dict / 'building_data.json')


if __name__ == '__main__':
    data_dict = Path('./data/')
    calc_main(data_dict=data_dict)
