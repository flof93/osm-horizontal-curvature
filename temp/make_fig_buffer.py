import shapely as shp
import geopandas as gpd
import osmnx as ox

import matplotlib
import matplotlib.pyplot as plt


if __name__ == '__main__':
    with open('./Währing (1.5km).geojson') as file:
        data = file.read()
        stadion = shp.from_geojson(data)

    line = stadion.geoms[0]
    gdf = gpd.GeoDataFrame({'geometry':[line]}, crs='EPSG:4326')
    gdf.to_crs(inplace=True, crs=gdf.estimate_utm_crs())
    buffer=gdf.buffer(distance=100)
    buildings=ox.features_from_bbox(buffer.boundary.buffer(100, cap_style='square').to_crs('EPSG:4326').total_bounds,tags={'building':True})
    buildings.to_crs(crs=buffer.crs, inplace=True)
    buildings_clipped=buildings.clip(mask=buffer)

    bbox=buffer.boundary.buffer(50, cap_style='square').total_bounds

    fig, ax = plt.subplots(1,1)
    buildings.clip(shp.box(*bbox)).plot(ax=ax, color='lightgrey')
    buffer.plot(ax=ax, color='lightyellow')
    buffer.boundary.plot(ax=ax, color='darkorange')
    buildings_clipped.plot(ax=ax)
    gdf.plot(ax=ax, color='r')
    ax.set_axis_off()
    fig.savefig('../../Abbildungen/Buffer.png', transparent = True, format='png', dpi=300, bbox_inches='tight', pad_inches=0.02)
    plt.show()