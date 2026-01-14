#==============#
# OFFENE TODOS #
#==============#

# TODO: Doc-Strings und Dokumentation

#===========#
# Parkplatz #
#===========#
### Lineare Regression und Darstellungen

data.dropna(axis='rows', inplace=True)

print("Corr curv/speed", data['curvature'].corr(data['trip_speed'], method='pearson'))
print("Corr dist/speed", data['avg_dist'].corr(data['trip_speed'], method='pearson'))

model = LinearRegression(fit_intercept=True)
data_unabh = data[['curvature', 'avg_dist']]
model.fit(X=data_unabh, y=data['trip_speed'])

print("k:", model.coef_)
print("d:", model.intercept_)
print("R²: ", model.score(X=data_unabh, y=data['trip_speed']))

fig, ax = plt.subplots(nrows=1, ncols=2)
data.dropna(axis='rows').plot.scatter(x='curvature', y='trip_speed', ax=ax[0], marker='x', s=10, c="navy")
x = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
fx = model.predict(X=x)
ax[0].plot(x[:, 0], fx, c="red")

data.dropna(axis='rows').plot.scatter(x='avg_dist', y='trip_speed', ax=ax[1], marker='x', s=10, c="navy")
ax[1].plot(x[:, 1], fx, c="red")
plt.show()

df_draw = data.dropna(axis='rows')[['curvature', 'avg_dist', 'trip_speed']]
sns.set_style('darkgrid')

# g = sns.PairGrid(df_draw, diag_sharey=False)
# g.map_upper(sns.scatterplot, s=15)
# g.map_lower(sns.kdeplot)
# g.map_diag(sns.kdeplot, lw=2)
# plt.show()


# =================
# Projektion Buffer
# =================

import geopandas as gpd
from shapely.geometry import LineString
from shapely.ops import transform
import pyproj
import matplotlib.pyplot as plt

def buffer_global(geometry, distance_m):
    """
    Erzeugt einen Buffer in Metern um ein beliebiges Geometrieobjekt (global gültig).
    Automatisch lokale UTM-Projektion.
    """
    # Mittelpunkt des Objekts bestimmen
    lon, lat = geometry.centroid.x, geometry.centroid.y

    # Automatisch passende UTM-Zone wählen
    utm_zone = int((lon + 180) / 6) + 1
    hemisphere = 'north' if lat >= 0 else 'south'
    utm_crs = f"+proj=utm +zone={utm_zone} +{'north' if hemisphere=='north' else 'south'} +datum=WGS84 +units=m +no_defs"

    # Projektionen definieren
    proj_wgs84 = pyproj.CRS("EPSG:4326")
    proj_utm = pyproj.CRS.from_proj4(utm_crs)

    # Transformationen definieren
    project_to_utm = pyproj.Transformer.from_crs(proj_wgs84, proj_utm, always_xy=True).transform
    project_to_wgs84 = pyproj.Transformer.from_crs(proj_utm, proj_wgs84, always_xy=True).transform

    # 1️⃣ Geometrie nach UTM transformieren
    geom_utm = transform(project_to_utm, geometry)

    # 2️⃣ Buffer in Metern erzeugen
    buffer_utm = geom_utm.buffer(distance_m)

    # 3️⃣ Buffer zurück in WGS84 transformieren
    buffer_wgs84 = transform(project_to_wgs84, buffer_utm)
    return buffer_wgs84


# 🌐 Beispiel: Eine Linie irgendwo auf der Welt
line = LineString([
    (-74.0060, 40.7128),  # New York City
    (-73.9352, 40.7306)
])

# Buffer von 100 m
buffer_geom = buffer_global(line, 100)

# GeoDataFrames erzeugen
gdf_line = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326")
gdf_buffer = gpd.GeoDataFrame(geometry=[buffer_geom], crs="EPSG:4326")

# Visualisierung
fig, ax = plt.subplots(figsize=(6, 6))
gdf_buffer.plot(ax=ax, color="lightblue", alpha=0.5, label="100 m Buffer")
gdf_line.plot(ax=ax, color="red", linewidth=2, label="LineString")
plt.legend()
plt.show()



for i in data[data['Stadt']=='Wien'].iterrows():
    print(ox.utils.ts(), '-', i[1]['Stadt'], '-', i[1]['line_name'])
    dl_info_single = ox.features_from_xml(polygon=i[1]['buffer_geometry'], tags={'building':True}, filepath='./OSM-Downloads/austria-251117.osm')
    dl_info = pd.concat([dl_info, dl_info_single])



ag=feed.agency[feed.agency['agency_id'].isin(feed.routes[feed.routes['route_type'].isin([0,900,901,902])]['agency_id'])]

#=========================================#
# Grafik für Raster bzw. Radialkonzentrik #
#=========================================#

barcelona = ox.graph_from_point((41.395029, 2.170953), 500, dist_type='bbox')
ox.plot_graph(barcelona, figsize=(10, 10), bgcolor='w', edge_color='k', node_color='k')