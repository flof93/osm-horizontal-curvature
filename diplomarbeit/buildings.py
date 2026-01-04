import os.path

import osmnx as ox
import geopandas as gpd
import pandas as pd

import shapely as shp

import requests.exceptions
from concurrent.futures import ThreadPoolExecutor


# street = ox.geocode_to_gdf('Haidgasse, Vienna, Austria')
# area = street.buffer(distance=0.0001)
# buildings = ox.features_from_polygon(area[0], {'building': True})
# cut = buildings.clip(mask=area)
# fig, ax = plt.subplots()
# area.exterior.plot(ax=ax, color='red')
# cut.plot(ax=ax)

def calculate_buffer_width(city: str) -> float:
    graph = ox.graph.graph_from_place(city, network_type='drive')
    d = pd.Series([d['length'] for u, v, d in graph.edges(data=True)])
    return d.median()


def get_buffer_line(gdf: gpd.GeoDataFrame, width: str, inplace: bool = False) -> gpd.GeoSeries:
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


def download_buildings_along_lines(agg_gdf: gpd.GeoDataFrame, data_path: str = './data/', timeout: int = 180):
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
        #time.sleep(30)

    # print('Starting Download')
    # if inplace:
    #     for i in gdf.iterrows():
    #         print(ox.utils.ts(), '-', i[1]['Stadt'], '-', i[1]['line_name'])
    #         dl_info_single = ox.features_from_polygon(polygon=i[1]['buffer_geometry'], tags=data_tags)
    #         dl_info_single['Stadt']=i[1]['Stadt']
    #         dl_info_single['line_name']=i[1]['line_name']
    #         dl_info = pd.concat([dl_info, dl_info_single])
    # else:
    #     for i in download_buffer:
    #         dl_info_single = ox.features_from_polygon(polygon=i, tags=data_tags)
    #         dl_info = pd.concat([dl_info, dl_info_single])
    #
    # # if inplace:
    # #     gdf['buildings_buffer'] = dl_info
    #
    # return dl_info[['geometry', 'Stadt', 'line_name']]


def download_buildings_bbox(data_path: str, filename: str = 'cities.csv', force_download: bool = False) -> None:
    data = pd.read_csv(data_path + filename, sep=';')
    print('Downloading Building Data')
    for idx, row in data.iterrows():
        city = row['machine_readable']
        if force_download or not os.path.exists(data_path + city + '/buildings/city_buildings.json'):
            print(ox.utils.ts(), '-', row['Stadt'])
            #bbox = (float(row['West']), float(row['Sued']), float(row['Ost']), float(row['Nord']))
            bbox = shp.box(float(row['West']), float(row['Sued']), float(row['Ost']), float(row['Nord']))
            bbox_enl = ox.utils_geo.buffer_geometry(bbox, data['Buffer_Width'].max())
            payload = ox.features_from_bbox(bbox=shp.total_bounds(bbox_enl), tags={'building': True})
            city = row['machine_readable']
            data_to_save = payload[payload['geometry'].type.isin({"Polygon", "MultiPolygon"})]['geometry']
            data_to_save.to_file(filename=data_path + city + '/buildings/city_buildings.json')


def process_city(city, data, data_path):
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
            clipped_line = gpd.GeoDataFrame({'geometry':[pd.NA], 'element':[pd.NA], 'id':[pd.NA]}, crs=data.crs)
        clipped_line['Stadt'] = row['Stadt']
        clipped_line['line_name'] = row['line_name']
        clipped_line.drop(labels=['element', 'id'], axis="columns", inplace=True)
        clipped_df = pd.concat([clipped_df, clipped_line], ignore_index=True)
    clipped_df = clipped_df.dissolve(by='line_name', as_index=False)
    return clipped_df


def clip_lines(data: gpd.GeoDataFrame, data_path: str = './data/'):
    cities = data['machine_readable'].unique()
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_city, city, data, data_path) for city in cities]
        results = [f.result() for f in futures]
    clipped_df = pd.concat(results, ignore_index=True)
    data = data.merge(right=clipped_df.rename_geometry(col='clipped_buildings'))
    return data


def calc_building_density(data: gpd.GeoDataFrame, inplace: bool = False, cleanup: bool = False) -> list:
    data.to_crs('EPSG:6933')
    densities = data['clipped_buildings'].area / data['buffer_geometry'].area
    if inplace:
        data['rho_b'] = densities
    if cleanup and inplace:
        data.drop(labels=['buffer_geometry', 'clipped_buildings'], axis='columns', inplace=True)
    return densities

def calc_main(data_dict) -> None:
    data = gpd.read_file(data_dict + 'results.json')
    get_buffer_line(data, 'Buffer_Width', True)
    data = clip_lines(data=data)
    calc_building_density(data=data, inplace=True, cleanup=True)
    data.to_file(data_dict + 'building_data.json')

if __name__ == '__main__':
    data_dict = './data/'

    data = gpd.read_file(data_dict + 'results.json')
    #data = data[data['Stadt']=='Berlin']

    download_buildings_bbox(data_path=data_dict)
    #agg_gdf = make_download_gdf_poly(gdf=data, width='Buffer_Width')
    #agg_gdf = make_download_gdf_bbox(gdf=data, width='Buffer_Width')
    #download_buildings_along_lines(agg_gdf=agg_gdf)
    get_buffer_line(data, 'Buffer_Width', True)
    data = clip_lines(data=data)

    calc_building_density(data=data, inplace=True, cleanup=True)
    data.to_file(data_dict + 'building_data.json')
    # data.to_crs('EPSG:6933')
    # data['rho_b'] = data['clipped_buildings'].area / data['buffer_geometry'].area
    # data.drop(labels=['buffer_geometry','clipped_buildings'], axis='columns').to_file(data_dict+'building_data.json')

    #buildings = get_data_along_lines(gdf=data, width='Buffer_Width', data_tags={'building':True}, inplace=True)
    #buildings.to_file(data_dict+'building_data.json')
