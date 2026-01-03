import os.path
import numpy as np
import diplomarbeit as da
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import seaborn as sns
import pandas as pd
import geopandas as gpd

def make_whole_dataframe(data_dict: str, filename: str = 'cities.csv', calc_times: bool = False):
    cities = da.utils.load_csv_input(data_path= data_dict, filename=filename)

    full_data = pd.DataFrame()

    for city in cities:
        print("\n=============\nErfassung von %s" % cities[city]['name'])
        #city = ('wien')
        ignore_linenumber = cities[city]['ignore_linenumber']
        # try:
        #     da.speeds.calc_speeds(path_to_gtfs=data_dict+city+'/timetable/')
        # except (FileNotFoundError, KeyError, ValueError):
        #     continue

        # Aufruf Berechnung der Durchschnittsgeschwindigkeit, falls diese noch nicht berechnet ist und Fahrplandaten vorliegen.
        if not os.path.exists(path=data_dict + city + '/timetable/results/trip_speeds_route_direction.csv') or calc_times:
            if os.path.exists(path=data_dict + city + '/timetable/routes.txt'):
                try:
                    da.speeds.calc_speeds(path_to_gtfs=data_dict + city + '/timetable/')
                except KeyError as e:
                    if 'shape_dist_traveled' in e.args:
                        continue
                except ValueError as e:
                    if "could not convert string to float: ''" in e.args:
                        continue
            else:
                continue

        gdf = da.add_speeds_to_osm.main(data_dict, city, ignore_linenumber)
        gdf['city'] = city
        full_data = pd.concat([full_data, gdf])#.dropna(axis='rows')])


    cities = pd.read_csv(data_dict + 'cities.csv', sep=';')
    full_data = full_data.merge(right=cities, right_on=['machine_readable'], left_on=['city'])
    full_data.drop(axis='columns', inplace=True,
             labels=['Ost', 'West', 'Nord', 'Sued', 'RailModes', 'Geschwindigkeit', 'GTFS-Daten', 'Ignore_LineNumber'])

    return full_data

if __name__ == '__main__':
    data_dict = './data/'
    #da.utils.cleanup_input(data_dict)


    data = make_whole_dataframe(data_dict= data_dict, calc_times=False)
    data.to_csv(data_dict+'results.csv')
    data.to_file(filename=data_dict+'results.json')

    da.buildings.download_buildings_bbox(data_path=data_dict)
    da.buildings.calc_main(data_dict=data_dict)

    # data = pd.read_csv(data_dict+'results.csv') # Backuplösung, falls gpd nicht funktioniert

    data = gpd.read_file(data_dict+'building_data.json').dropna(axis='index')
    data.height_up = data.height_up.astype('float64')
    data.height_down = data.height_down.astype('float64')






    # g = sns.lmplot(
    #     data=data,
    #     x="curvature", y="trip_speed", hue="city",
    #     height=5
    # )
    # plt.show()

    sns.set_style('darkgrid')

    for i in data['city'].unique():
        city_data = data[data['city']==i]

        model = LinearRegression(fit_intercept=True)
        data_unabh = city_data[['curvature']]
        model.fit(X=data_unabh, y=city_data['trip_speed'])

        fig, ax = plt.subplots(nrows=1, ncols=2, sharey=True)
        ax[0].set_ylim(0,40)


        fig.suptitle(city_data['Stadt'].unique()[0], fontsize=16)

        city_data.dropna(axis='rows').plot.scatter(x='curvature', y='trip_speed', ax=ax[0])#, marker='x', s=10, c="navy")
        x = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
        fx = model.predict(X=x)
        ax[0].plot(x[:, 0], fx, c="red")
        ax[0].set_xlabel('Durchschnittliche\nKurvigkeit [gon/km]')
        ax[0].set_ylabel('Durchschnittliche\nLiniengeschwindigkeit [km/h]')

        data_unabh = city_data[['avg_dist']]
        model.fit(X=data_unabh, y=city_data['trip_speed'])

        city_data.dropna(axis='rows').plot.scatter(x='avg_dist', y='trip_speed', ax=ax[1])#, marker='x', s=10, c="navy")
        x = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
        fx = model.predict(X=x)
        ax[1].plot(x[:, 0], fx, c="red")
        ax[1].set_xlabel('Durchschnittlicher\nHaltestellenabstand [m]')
        plt.savefig(fname=data_dict+i+'/results/corr.png')
        plt.close()


    data.sort_values(by=['Stadt'], inplace=True)

    print("Anzahl Linien:", len(data))

    print("Corr curv/speed", data['curvature'].corr(data['trip_speed'], method='pearson'))
    print("Corr dist/speed", data['avg_dist'].corr(data['trip_speed'], method='pearson'))



    model = LinearRegression(fit_intercept=True)
    data_unabh = data[['curvature', 'avg_dist']]
    model.fit(X=data_unabh, y=data['trip_speed'])

    print('======\nKombiniertes Modell (Kurvigkeit & Haltestellenabstand)')
    print("k:", model.coef_)
    print("d:", model.intercept_)
    print("R²: ", model.score(X=data_unabh, y=data['trip_speed']))

    sns.set_style('darkgrid')

    fig, ax = plt.subplots(nrows=1, ncols=2)

    model = LinearRegression(fit_intercept=True)
    data_unabh = data[['curvature']]
    model.fit(X=data_unabh, y=data['trip_speed'])

    sns.scatterplot(data= data, x='curvature', y='trip_speed', ax=ax[0], hue="Stadt")
    x = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
    fx = model.predict(X=x)
    ax[0].plot(x[:, 0], fx, c="red")
    #data.dropna(axis='rows').plot.scatter(x='curvature', y='trip_speed', ax=ax[0], marker='x', s=10, c="city", grid=True)
    #x = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
    #fx = model.predict(X=x)
    #ax[0].plot(x[:, 0], fx, c="red")

    print('======\nKurvigkeit')
    print("k:", model.coef_)
    print("d:", model.intercept_)
    print("R²: ", model.score(X=data_unabh, y=data['trip_speed']))

    model = LinearRegression(fit_intercept=True)
    data_unabh = data[['avg_dist']]
    model.fit(X=data_unabh, y=data['trip_speed'])

    print('======\nHaltestellenabstand')
    print("k:", model.coef_)
    print("d:", model.intercept_)
    print("R²: ", model.score(X=data_unabh, y=data['trip_speed']))

    sns.scatterplot(data=data, x='avg_dist', y='trip_speed',  ax=ax[1], hue="Stadt")
    x = np.linspace(data_unabh.min(), data_unabh.max(), 1000)
    fx = model.predict(X=x)
    ax[1].plot(x[:, 0], fx, c="red")
    #data.dropna(axis='rows').plot.scatter(x='avg_dist', y='trip_speed', ax=ax[1], marker='x', s=10, c="city", grid=True)
    #ax[1].plot(x[:, 1], fx, c="red")

    ax[0].set_ylim(00, 40)
    ax[1].set_ylim(00, 40)
    ax[0].set_xlabel('Durchschnittliche\nKurvigkeit [gon/km]')
    ax[0].set_ylabel('Durchschnittliche\nLiniengeschwindigkeit [km/h]')
    ax[1].set_xlabel('Durchschnittlicher\nHaltestellenabstand [m]')
    plt.show()

    columns=['curvature', 'avg_dist', 'trip_speed', 'height_up', 'height_down', 'rho_b']
    df_draw = data.dropna(axis='rows', subset=columns)[columns]
    sns.set_style('darkgrid')

    g = sns.PairGrid(data=df_draw, diag_sharey=False)
    g.map_upper(sns.scatterplot, s=15)
    g.map_lower(sns.kdeplot)
    g.map_diag(sns.kdeplot, lw=2)
    plt.show()