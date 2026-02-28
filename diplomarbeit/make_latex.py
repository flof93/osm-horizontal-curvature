from pathlib import Path
from typing import Any

import contextily as cx
import geopandas as gpd
import pandas as pd
import shapely.geometry as shp
from matplotlib import pyplot as plt
import geodatasets
import numpy as np
from matplotlib.colors import ListedColormap

import diplomarbeit as da

from sklearn.linear_model import LinearRegression

import seaborn as sns

import osmnx as ox

from diplomarbeit import DATA_DIR, DATAFIELD_VARIABLENAME

RESULTS_DIR = Path('~/Documents/Diplomarbeit/osm-horizontal-curvature/results').expanduser()  # TODO: Make LaTeX-Picture directory for Production

def set_print_style(textwidth_cm=16, fontsize=10):
    inch = textwidth_cm / 2.54
    sns.set_style('darkgrid')
    plt.rcParams['text.latex.preamble'] =  " \\usepackage{lmodern}"
    plt.rcParams.update({
        'text.usetex': True,
        'figure.figsize':   (inch, inch * 0.5),
        'font.size':        fontsize,
        'axes.titlesize':   fontsize,
        'axes.labelsize':   fontsize,
        'xtick.labelsize':  fontsize - 1,
        'ytick.labelsize':  fontsize - 1,
        'legend.fontsize':  fontsize - 1,
        'figure.dpi':       150,   # für Bildschirm; beim Speichern separat setzen
        'font.family':      'lmodern',
    })

def add_alidade_smooth(ax, crs=None):
    provider = cx.providers.Stadia.AlidadeSmooth(api_key=da.STADIA_API)
    provider["url"] = provider["url"] + "?api_key={api_key}"
    cx.add_basemap(ax, crs=crs, source=cx.providers.CartoDB.Voyager)  #source=provider)

def square_bounds(gdf, padding=0.1):
    xmin, ymin, xmax, ymax = gdf.total_bounds

    width = xmax - xmin
    height = ymax - ymin
    size = max(width, height)

    # add padding
    size *= (1 + padding)

    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2

    return (
        cx - size / 2,
        cy - size / 2,
        cx + size / 2,
        cy + size / 2
    )


def make_geograph_net():
    results_df = gpd.read_file(da.DATA_DIR / 'building_data.json').dropna(axis='index')
    cities_df = pd.read_csv(da.DATA_DIR / 'cities.csv', sep=';')

    cities = results_df.machine_readable.unique()
    for city in cities:

        df_res = results_df[results_df['machine_readable'] == city].to_crs('EPSG:3857')
        df_cities = cities_df[cities_df['machine_readable'] == city]

        df_box = gpd.GeoDataFrame({'geometry': [shp.box(float(df_cities['West'].iloc[0]),
                                                            float(df_cities['Sued'].iloc[0]),
                                                            float(df_cities['Ost'].iloc[0]),
                                                            float(df_cities['Nord'].iloc[0]))]}, crs='EPSG:4326')

        xmin, ymin, xmax, ymax = square_bounds(df_res, padding=0.1)


        fig, ax = plt.subplots(figsize=(6.3, 6.3))
        #ax.set_box_aspect(1)

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect("equal")

        df_res.plot(ax=ax, color='r')
        #df_box.boundary.plot(ax=ax, color='r')
        #ax=df_res.plot(cmap='gist_rainbow', figsize=(10,10))

        add_alidade_smooth(ax, crs=df_res.crs)

        ax.set_axis_off()

        fig.savefig(RESULTS_DIR/'Appendix_Results'/city/'map.png', pad_inches=0, dpi=200, bbox_inches='tight')
        plt.close(fig)

def weighted_average(data:pd.DataFrame, value, weight):
    val = data[value]
    wt = data[weight]
    return (val * wt).sum() / wt.sum()

def make_city_table(data: gpd.GeoDataFrame):
    agg_func = {'distance': ['mean', 'sum'],
                # 'trip_speed': ['mean'],
                'number_trips': ['sum'],
                'curvature': ['mean'],
                'avg_dist': ['mean'],
                'rho_b': ['mean'],
                'machine_readable': ['count'],
                'Stadt': 'first',
                'ISO3166': 'first',
                'gauge': lambda x: r"\\ &  ".join(y + '~mm' for y in map(str, map(int, x.unique().tolist()))),
                'region': 'first',
                'Buffer_Width': 'mean'}
    grouped = data[
        ['Stadt', 'distance', 'trip_speed', 'number_trips', 'curvature', 'avg_dist', 'rho_b', 'gauge', 'ISO3166',
         'machine_readable', 'region', 'Buffer_Width']].groupby(by=['region', 'ISO3166', 'Stadt']).aggregate(func=agg_func)
    grouped['trip_speeds_new'] = data.groupby(['region','ISO3166', 'Stadt']).apply(weighted_average, 'trip_speed',
                                                                                    'number_trips')

    grouped.rename(columns={'machine_readable': 'Anzahl Relationen'}, inplace=True)
    grouped.rename_axis(['Region', 'ISO3166', 'Stadt']).reset_index(inplace=True)
    grouped.columns = grouped.columns.droplevel(1)
    header = ['Region', 'Land', 'Stadt', r'$n_{{Linien}}$', r'$\bar V$ [\unit{{\kilo\metre\per\hour}}]',
              r'$\bar l_{{Hst}}$ [\unit{{\metre}}]']
    df_out = grouped.drop(columns='distance').reindex(
        ['region','ISO3166', 'Stadt', 'Anzahl Relationen', 'trip_speeds_new', 'avg_dist'],
        axis=1)
    df_out.to_latex(RESULTS_DIR / 'cities.tex',
                    columns=['region', 'ISO3166', 'Stadt', 'Anzahl Relationen', 'trip_speeds_new', 'avg_dist'],
                    index=False,
                    header=header,
                    float_format="%.2f",
                    column_format='lllSSS')
    return grouped

def make_statistic_table(data: gpd.GeoDataFrame) -> pd.DataFrame:
    grouped = data[
        ['Stadt', 'Buffer_Width', 'phi_street', 'phi_tram']].groupby(by=['Stadt']).aggregate(
        func='first')
    desc_cit=grouped.describe().T
    desc_rel = data[['curvature', 'height_up', 'height_down', 'trip_speed', 'avg_dist', 'rho_b']].describe().T
    desc=pd.concat([desc_cit,desc_rel])
    desc.rename(da.COLUMN_NAMES_TEX_SHORT, inplace=True)
    desc['count'] = desc['count'].astype(int)
    cols={'count':r'$n$', 'mean':r'$\bar x$', 'std':r's', 'min':r'$min$', '25%':r'$Q_{25}$', '50%':r'$Q_{50}$', '75%':r'$Q_{75}$', 'max':r'$max$'}
    desc.rename(cols, inplace=True, axis=1)
    desc.to_latex(RESULTS_DIR / 'statistics.tex', float_format="%.4f")
    return desc


def make_worldmap(data: gpd.GeoDataFrame):
    sns.set_style("ticks")
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)
    from matplotlib.colors import ListedColormap

    grouped = data[['geometry', 'Stadt', 'region']].dissolve(by='Stadt')
    grouped.to_crs('EPSG:4087', inplace=True)
    grouped['geometry'] = grouped.geometry.centroid
    grouped.to_crs('EPSG:4326', inplace=True)

    fig, ax = plt.subplots(1, 1, figsize=(6.3, 4.5))
    world.to_crs(crs=grouped.crs).plot(ax=ax, alpha=0.1, color="grey")
    world.to_crs(crs=grouped.crs).boundary.plot(ax=ax, alpha=0.8, color="grey", lw=.5)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)

    minx, miny, maxx, maxy = [-12, 35, 38, 65]
    axins = ax.inset_axes(
        (0.04, -0.10, 0.40, 0.85),
        xlim=(minx, maxx), ylim=(miny, maxy), xticklabels=[], yticklabels=[])
    world.to_crs(crs=grouped.crs).plot(ax=axins, alpha=0.1, color="grey")
    world.to_crs(crs=grouped.crs).boundary.plot(ax=axins, alpha=0.8, color="grey", lw=.5)
    ax.indicate_inset_zoom(axins, edgecolor="black")

    cmap_muted = sns.color_palette(None, len(grouped.region.unique()))
    cmap_new = ListedColormap([cmap_muted[x] for x, region in enumerate(data.region.unique())])
    grouped.plot(ax=ax, marker='o', markersize=10, categorical=True, column='region', legend=True, cmap=cmap_new, zorder=5)
    grouped.plot(ax=axins, marker='o', markersize=5, categorical=True, column='region', legend=False, cmap=cmap_new, zorder=5)

    ax.set_yticks([])
    ax.set_xticks([])

    axins.set_yticks([])
    axins.set_xticks([])

    #plt.show()
    fig.savefig(RESULTS_DIR / 'worldmap.png', pad_inches=0.05, dpi=600, bbox_inches='tight')
    plt.close(fig)


def paired_density_and_scatterplot(data: gpd.GeoDataFrame | pd.DataFrame):
    g = sns.PairGrid(data=data, diag_sharey=False, height=1.25, aspect=1)
    g.map_upper(sns.scatterplot, color='C0', s=10, marker='+')
    g.map_diag(sns.kdeplot, color='C1', lw=1)
    g.map_lower(sns.kdeplot, color='C2', linewidths=0.5)
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

    try:
        data.plot.scatter(x=x[0], y=y[0], ax=axs[subaxis])  # , marker='x', s=10, c="navy")
        intercept_pre = '+' if model.intercept_ > 0 else ''
        axs[subaxis].plot(x_between[:, 0], fx, c="red",
                          label="y={0:.4f}x{3}{1:.2f}\nR²={2:.2f}".format(model.coef_[0], model.intercept_, r_square,
                                                                          intercept_pre).replace('.', ','))
        axs[subaxis].set_xlabel(x[1])
        axs[subaxis].set_ylabel(y[1])
        axs[subaxis].legend()
    except TypeError:
        data.plot.scatter(x=x[0], y=y[0], ax=axs)  # , marker='x', s=10, c="navy")
        intercept_pre = '+' if model.intercept_ > 0 else ''
        axs.plot(x_between[:, 0], fx, c="red",
                          label="y={0:.4f}x{3}{1:.2f}\nR²={2:.2f}".format(model.coef_[0], model.intercept_, r_square,
                                                                          intercept_pre).replace('.', ','))
        axs.set_xlabel(x[1])
        axs.set_ylabel(y[1])
        axs.legend()


    return None


def make_city_diags(data: gpd.GeoDataFrame):
    set_print_style()

    x_axis = [('curvature', da.COLUMN_NAMES_TEX['curvature']),
              ('avg_dist', da.COLUMN_NAMES_TEX['avg_dist']),
              #('height_up', 'Durchschnittlicher\nAufstieg [m/km]'),
              #('rho_b', 'Bebauungsdichte'),
              ]

    y_axis = [('trip_speed', da.COLUMN_NAMES_TEX['trip_speed']),
              ]

    for i in data['city'].unique():
        city_data = data[data['city'] == i]

        fig, axs = plt.subplots(nrows=1, ncols=len(x_axis), sharey=True, figsize=(len(x_axis) * 3, 3))
        #fig.suptitle(city_data['Stadt'].unique()[0], fontsize=16)

        axs[0].set_ylim(0, 40)

        for j in range(len(x_axis)):
            max = data.dropna(axis='index')[x_axis[j][0]].max()
            if max < 1:
                axs[j].set_xlim(0, da.utils.round_up(max, 1))
            else:
                axs[j].set_xlim(0, da.utils.round_up(max, -1))

            add_subplot(data=city_data, x=x_axis[j], y=y_axis[0], subaxis=j, axs=axs)

        plt.savefig(fname=RESULTS_DIR/ 'Appendix_Results' / i / 'corr.png', pad_inches=0.2)
        plt.close(fig)

# ~~~~~~~~~~~~~~~~~~~~~~~~~
# CREATE FILES FOR APPENDIX
# ~~~~~~~~~~~~~~~~~~~~~~~~~

def make_var_preamble(variable: str) -> str:
    out = r"\newcommand{" + '\\' + variable + r'}{\textbf{UNDEF!} }'
    return out

def variable_to_tex(variable: str, value: Any) -> str:
    out=r"\renewcommand{"+'\\'+ variable + r'}{' + str(value) + r'}'
    return out

def write_variables_to_file(path: Path, variables_list:dict) -> None:
    payload=''
    for variable in variables_list:
        payload+=variable_to_tex(variable, variables_list[variable])+'\n'
    payload+=r'\input{Chapters/City_Appendix}'+'\n'+r'\pagebreak'
    with open(path, 'w') as f:
        f.write(payload)

# def merge_city_vals(val: pd.DataFrame, data:pd.DataFrame) -> pd.DataFrame:
#     val_drp = val.reset_index(drop=True)
#     val_drp.merge(data, how='left', left_on=['Stadt', 'ISO3166'], right_on=['Stadt', 'ISO3166'])
#     return val_drp

def has_shape_dist(gtfs_path: Path) -> bool:
    stop_times_path = gtfs_path / "stop_times.txt"
    stop_times = pd.read_csv(stop_times_path)

    if 'shape_dist_traveled' not in stop_times.columns or stop_times[
        'shape_dist_traveled'].isnull().any() and (gtfs_path / 'shapes.txt').exists():
        return True
    else:
        return False

def make_city_input(cities:list) -> str:
    out=''
    for city in sorted(cities):
        out += r'\input{Appendix_Results/' + city + r'/tex_vars.tex}'+'\n'
    return out

def variables_to_tex(data: pd.DataFrame, variables_list: dict) -> dict:
    for idx, row in data.iterrows():
        var_pairs={}
        for variable in variables_list:
            var_pairs[variables_list[variable]]=row[variable]
        if pd.isna(row['RailModes']):
            var_pairs['varTagTram']=r'\ding{52}'
            var_pairs['varTagLrt']=r'\ding{52}'
        elif row['RailModes']=='tram':
            var_pairs['varTagTram'] = r'\ding{52}'
            var_pairs['varTagLrt'] = r'\ding{56}'
        elif row['RailModes'] == 'light_rail':
            var_pairs['varTagTram'] = r'\ding{56}'
            var_pairs['varTagLrt'] = r'\ding{52}'
        else:
            raise ValueError('Wrong Rail Modes - Information')

        if has_shape_dist(DATA_DIR/row['machine_readable'] / 'timetable'):
            var_pairs['varShapeDist']=r'\ding{52}'
        else:
            var_pairs['varShapeDist']=r'\ding{56}'

        var_pairs['pictureOrientation'] = r'Appendix_Results/'+row['machine_readable']+r'/orientation_landscape.png'
        var_pairs['pictureCorrelations'] = r'Appendix_Results/' + row['machine_readable'] + r'/corr.png'
        var_pairs['pictureMap'] = r'Appendix_Results/' + row['machine_readable'] + r'/map.png'

        (RESULTS_DIR / 'Appendix_Results' / row['machine_readable']).mkdir(parents=True, exist_ok=True)
        write_variables_to_file((RESULTS_DIR / 'Appendix_Results' / row['machine_readable'] / 'tex_vars.tex'), var_pairs)

    payload = ''
    for var in var_pairs.keys():
        payload += make_var_preamble(var) + '\n'
    with open(RESULTS_DIR / 'Appendix_Results' / 'var_preamble.tex', 'w') as f:
        f.write(payload)

    with open(RESULTS_DIR / 'Appendix_Results' / 'input_appendix.tex', 'w') as f:
        f.write(make_city_input(data.machine_readable.unique().tolist()))




if __name__ == '__main__':
    set_print_style(textwidth_cm=16.0, fontsize=10)
    data = gpd.read_file(da.DATA_DIR / 'building_data.json').dropna(axis='index')
    data_de = data.rename(columns=da.COLUMN_NAMES_DE)
    data_tex = data[['curvature', 'height_up', 'height_down', 'trip_speed', 'avg_dist', 'rho_b']].rename(
        columns=da.COLUMN_NAMES_TEX)
    data_tex_short = data[['curvature', 'height_up', 'height_down', 'trip_speed', 'avg_dist', 'rho_b']].rename(
        columns=da.COLUMN_NAMES_TEX_SHORT)

    city_data = make_city_table(data)
    statistics = make_statistic_table(data)

    cities_csv=pd.read_csv(DATA_DIR / 'cities.csv', sep=';')
    # variables_to_tex(city_data.reset_index(drop=True).merge(cities_csv,
    #                                                         how='left',
    #                                                         left_on=['Stadt', 'ISO3166'],
    #                                                         right_on=['Stadt', 'ISO3166'],
    #                                                         suffixes=(None,'_y')), DATAFIELD_VARIABLENAME)
    #make_geograph_net()
    #make_worldmap(data)

    #make_city_diags(data)

    #g = paired_density_and_scatterplot(data_tex)
    #g.figure.savefig(RESULTS_DIR / 'paired_density_and_scatterplot.png', dpi=600, bbox_inches='tight')
    #plt.close(g.figure)

    #g = correlation_heatmap(data_tex_short)
    #g.figure.savefig(RESULTS_DIR / 'correlation_heatmap.png', dpi=600, bbox_inches='tight')
