import numpy as np
import pandas as pd
import csv
import os
from datetime import datetime, timedelta
import time
import gtfs_kit as gk

# Pfad zum GTFS-Datensatz angeben
# path_to_gtfs = "./data/wien/"

## FF: make functions callable
def calc_speeds(path_to_gtfs):

    # GTFS-Datensatz laden
    print(f"Daten einlesen...")
    routes = pd.read_csv(path_to_gtfs + "routes.txt", dtype={
        "route_id": "string",
        "agency_id": "string",
        "route_short_name": "string",
        "route_long_name": "string",
        "route_desc": "string",
        "route_type": "Int64",
        "route_url": "string",
        "route_color": "string",
        "route_text_color": "string",
        "route_sort_order": "Int64",
        "continuous_pickup": "Int64",
        "continuous_drop_off": "Int64",
        "network_id": "string",
    })

    trips = pd.read_csv(path_to_gtfs + "trips.txt", dtype={
        "route_id": "string",
        "service_id": "string",
        "trip_id": "string",
        "trip_headsign": "string",
        "trip_short_name": "string",
        "trip_long_name": "string",
        "direction_id": "Int64",
        "block_id": "string",
        "shape_id": "string",
        "wheelchair_accessible": "Int64",
        "bikes_allowed": "Int64",
        "ext_id": "string",
        "brigade": "string",
        "fleet_type": "string",
    })

    stop_times_dtypes={
        "trip_id": "string",
        "arrival_time": "string",
        "departure_time": "string",
        "stop_id": "string",
        "stop_sequence": "Int64",
        "stop_headsign": "string",
        "pickup_type": "Int64",
        "drop_off_type": "Int64",
        "continuous_pickup": "Int64",
        "continuous_drop_off": "Int64",
        "shape_dist_traveled": "float64",
        "timepoint": "Int64",
    }

    # Überprüfung ob es eine verbesserte stop-times.txt gibt (Ergänzung von fehlenden shape_dist_traveled)

    # if os.path.exists(path_to_gtfs + "stop_times_with_shape_dist.txt"):
    #     stop_times_path = path_to_gtfs + "stop_times_with_shape_dist.txt"
    # else:
    #     stop_times_path = path_to_gtfs + "stop_times.txt"

    stop_times_path = path_to_gtfs + "stop_times.txt"
    stop_times = pd.read_csv(stop_times_path, dtype=stop_times_dtypes)

    if 'shape_dist_traveled' not in stop_times.columns or stop_times['shape_dist_traveled'].isnull().any() and os.path.exists(path= path_to_gtfs + 'shapes.txt'):
        print("""Berechnung von 'shape_dist_traveled'...""")
        feed = gk.read_feed(path_or_url = path_to_gtfs, dist_units= 'm')
        stop_times = feed.append_dist_to_stop_times().stop_times

    #FF: Einlesen der Stops-Datei
    stops = pd.read_csv(path_to_gtfs + "stops.txt", dtype={
        "stop_id": "string",
        "stop_code": "string",
        "stop_name": "string",
        "stop_desc": "string",
        "stop_lat": "float64",
        "stop_lon": "float64",
        "zone_id": "string",
        "stop_url": "string",
        "location_type": "Int64",
        "parent_station": "string",
        "stop_timezone": "string",
        "wheelchair_boarding": "Int64",
        "level_id": "string",
        "platform_code": "string",
    })
    stops = dict(stops[['stop_id', 'stop_name']].to_dict(orient='tight')['data'])


    # GTFS Daten bereinigen, sodass nur mehr Straßenbahn-Routen enthalten sind
    print(f"Bereinigen der Datensätze auf Straßenbahnen...")

    # Behalte nur route_type = 0 (Straba) in Routes
    ## FF: hinzufügen von Routentypen 900, 901, 902 gem. https://developers.google.com/transit/gtfs/reference/extended-route-types
    desired_types = [0, 900, 901, 902]
    routes_tram = routes.loc[routes['route_type'].isin(desired_types)]

    # Vergleiche route_id in Routes und Trips
    trips_tram = trips.loc[trips['route_id'].isin(routes_tram['route_id'])]
    # Vergleiche trip_id in Trips und Stop_Times
    stop_times_tram = stop_times.loc[stop_times['trip_id'].isin(trips_tram['trip_id'])]

    # Füge die route_short_name Spalte aus der routes.txt hinzu
    trips_tram = pd.merge(trips_tram, routes_tram[['route_id', 'route_short_name']], on='route_id')

    stop_times_tram = pd.merge(stop_times_tram, trips_tram[['trip_id', 'route_short_name', 'direction_id']], on='trip_id')

    # Erstelle neue bereinigte stop_times_tram.txt Datei
    stop_times_tram.to_csv(path_or_buf=path_to_gtfs+'stop_times_tram.txt',index=False)

    # Mit der neuen GTFS stop_times_tram.txt-Datei:
    ## FF: Speichern der stop_times_tram-Datei bei den GTFS-Daten, nicht im wdir
    with open(path_to_gtfs+'stop_times_tram.txt', 'r', encoding='utf8') as stop_times_file:
        stop_times_reader = csv.DictReader(stop_times_file)

        # Ein leeres Dictionary für die Berechnung der Durchschnittsgeschwindigkeiten erstellen
        trip_speeds = {}

        for row in stop_times_reader:
            trip_id = row['trip_id']
            try:
                shape_dist_traveled = float(row['shape_dist_traveled'])
            except ValueError:
                shape_dist_traveled = np.NaN
            #stop_sequence = int(row['stop_sequence'])
            arrival_time_str = row['arrival_time']

            # Wenn die Stundenangabe größer als 23 ist, subtrahiere 24 und erhöhe den Tag um 1
            # FF: Splitten am ':' um einstellige Stundenangaben abzufangen.
            if int(arrival_time_str.split(sep=':')[0]) > 23:
                arrival_time_str = f"{int(arrival_time_str[:2])-24}{arrival_time_str[2:]}"
                arrival_time = datetime.strptime(arrival_time_str, '%H:%M:%S') + timedelta(days=1)
            else:
                arrival_time = datetime.strptime(arrival_time_str, '%H:%M:%S')

            # FF Station-ID ermitteln
            stop_id = row['stop_id']

            # Wenn diese trip_id noch nicht im trip_speeds-Dictionary vorhanden ist, erstelle eine neue Liste
            if trip_id not in trip_speeds:
                trip_speeds[trip_id] = []

            # Füge die Entfernung und die Ankunftszeit am aktuellen Stop zur trip_speeds-Liste hinzu
            trip_speeds[trip_id].append((shape_dist_traveled, arrival_time, stop_id))

        # Ein leeres DataFrame erstellen
        # df = pd.DataFrame(columns=['trip_id', 'trip_speed', 'first_stop_id', 'last_stop_id'])


        # Berechne die Durchschnittsgeschwindigkeit für jede trip_id
        print(f"Berechne die Geschwindigkeiten...")

        data_df = []

        for trip_id, data in trip_speeds.items():
            # Sortiere die Liste der Entfernungen und Zeiten nach aufsteigenden Ankunftszeiten
            # nur notwendig wenn Reihenfolge nicht korrekt
            # data.sort(key=lambda x: x[1])

            # Berechne die Gesamtentfernung zwischen der ersten und letzten Haltestelle
            total_distance = data[-1][0] - data[0][0]

            # Berechne die Gesamtzeit zwischen der ersten und letzten Haltestelle
            total_time = (data[-1][1] - data[0][1]).total_seconds()

            # Berechne die Durchschnittsgeschwindigkeit (in km/h)
            # FF: Ergänzung um Erkennung der Distanz-Einheit
            if len(data) > 1:
                if data[1][0] < 20: # Für Fall, dass Distanzen in km angegeben sind. (Erkennung, wenn 1. Distanz < 20m)
                    total_distance = total_distance * 1000
            try:
                trip_speed = (total_distance / total_time) * 3.6
            except ZeroDivisionError:
                trip_speed = pd.NA

            # Ausgangstation ermitteln
            first_stop_id = data[0][2]

            # Endstation ermitteln
            last_stop_id = data[-1][2]

            first_stop_name = stops[first_stop_id]
            last_stop_name = stops[last_stop_id]

            #FF: Stationsabstände errechnen:
            delta_dist_list = []
            for i,j in enumerate(data):
                delta_dist_list.append(data[i][0]-data[i-1][0])
            del delta_dist_list[0] # Entferne 1. Stationsabstand (ist immer 0)
            delta_dist = pd.Series(delta_dist_list).mean()

            if len(data) > 1:
                if data[1][0] < 20: # Für Fall, dass Distanzen in km angegeben sind. (Erkennung, wenn 1. Distanz < 20m)
                    delta_dist = delta_dist * 1000

            data_df.append([trip_id, trip_speed, first_stop_id, last_stop_id, first_stop_name, last_stop_name, delta_dist, total_time])

            # Füge trip_id und Durchschnittsgeschwindigkeit dem DataFrame hinzu
            # df = pd.concat([df, pd.DataFrame({'trip_id': [trip_id], 'trip_speed': [trip_speed]})], ignore_index=True)#, 'first_stop_id': [first_stop_id], 'last_stop_id': [last_stop_id]})], ignore_index=True)

        df = pd.DataFrame(data=data_df, columns=['trip_id', 'trip_speed', 'first_stop_id', 'last_stop_id', 'first_stop_name', 'last_stop_name', 'delta_dist', 'total_time'])


        # Füge die Spalte 'route_short_name' zum DataFrame hinzu
        df = pd.merge(stop_times_tram[['trip_id', 'route_short_name', 'direction_id']].drop_duplicates(), df, on='trip_id')


        # Ein leeres DataFrame erstellen
        # df1 = pd.DataFrame(columns=['route_short_name', 'direction_id', 'first_stop_name', 'last_stop_name','avg_speed'])

        # Gruppierung nach route_short_name und direction_id durchführen und Durchschnittsgeschwindigkeit berechnen
        # FF Gruppierung außerdem nach 1. und letzter Station - dadurch Kurzführungen erkennbar
        # FF: Berechnung Haltestellenabstand
        print(f"Berechne die Durchschnittsgeschwindigkeiten und durchschnittlichen Haltestellenabstand pro route_short_name und direction_id...")

        grouped = df.groupby(['route_short_name', 'direction_id', 'first_stop_name', 'last_stop_name'])#,'first_stop_id', 'last_stop_id'])

        data_df=[]

        for name, group in grouped:
            # Berechne die Durchschnittsgeschwindigkeit für diese Gruppe
            avg_speed = group['trip_speed'].mean()

            # FF: Berechnung der Anzahl an Fahrten, welche bei der Durchschnittsgeschwindigkeit greifen
            number_trips = group['trip_speed'].count()

            # FF: Berechnung durchschnittlicher Haltestellenabstand
            avg_dist = group['delta_dist'].mean()

            # FF: Berechnung der durchschnittlichen Fahrzeit
            avg_time = group['total_time'].mean()

            # Füge die Informationen zu dieser Gruppe (route_short_name, direction_id und Durchschnittsgeschwindigkeit) dem DataFrame hinzu
            data_dict={'route_short_name': name[0],
                       'direction_id': name[1],
                       'avg_speed': avg_speed,
                       'first_stop_name':name[2],
                       #'first_stop_id': name[4],
                       'last_stop_name':name[3],
                       #'last_stop_id': name[5],
                       'number_trips': number_trips,
                       'avg_dist': avg_dist,
                       'avg_time': avg_time}

            #first_stop_name = stops[data_dict['first_stop_id']]
            #last_stop_name = stops[data_dict['last_stop_id']]
            data_df.append((data_dict['route_short_name'],
                            data_dict['direction_id'],
                            data_dict['avg_speed'],
                            data_dict['first_stop_name'],
                            #data_dict['first_stop_id'],
                            data_dict['last_stop_name'],
                            #data_dict['last_stop_id'],
                            data_dict['number_trips'],
                            data_dict['avg_dist'],
                            data_dict['avg_time']))

        df1 = pd.DataFrame(data=data_df, columns=['route_short_name','direction_id', 'trip_speed', 'first_stop_name', 'last_stop_name', 'number_trips', 'avg_dist', 'avg_time'])

        # Sortieren nach route_short_name
        ## FF Sortierung verbessert
        #num_df = df1[pd.to_numeric(df1['route_short_name'], errors='coerce').notnull()]  # wählt numerische Werte aus
        #str_df = df1[pd.to_numeric(df1['route_short_name'], errors='coerce').isnull()]  # wählt nicht-numerische Werte aus
        df1_sorted = df1.sort_values(
            by=['route_short_name', 'direction_id']).reset_index(
            drop=True)  # sortiert numerische Werte
        #df1_sorted.drop(columns=['trip_id'], inplace=True)

        #sorted_num_df = num_df.astype(float).sort_values(by=['route_short_name', 'direction_id']).reset_index(drop=True)  # sortiert numerische Werte
        #sorted_num_df['route_short_name'] = sorted_num_df['route_short_name'].astype(int)  # wandelt die Spalte "route_short_name" in den Integer-Datentyp um
        #sorted_num_df['direction_id'] = sorted_num_df['direction_id'].astype(int)  # wandelt die Spalte "direction_id" in den Integer-Datentyp um
        #sorted_str_df = str_df.sort_values(by='route_short_name')  # sortiert nicht-numerische Werte
        #df1_sorted = pd.concat([sorted_num_df, str_df])  # kombiniert sortierte DataFrames


        # Schreibe den DataFrame in eine Excel-Datei
        print(f"Schreibe Excel...")
        os.makedirs(path_to_gtfs + 'results', exist_ok=True)
        #df1_sorted.to_excel(path_to_gtfs + 'results/sorted_trip_speeds_route_direction' + str(datetime.now().strftime('_%d_%m_%Y')) + '.xlsx', index=False)
        #df1_sorted.to_latex(path_to_gtfs + 'results/trip_speeds_route_direction' + str(datetime.now().strftime('_%d_%m_%Y')) + '.tex', index=False)

        ### FF: Ergänzung um Export in csv, zur weiteren Verwendung, entfernung des Datumsstempels
        df1_sorted.to_csv(path_to_gtfs + 'results/trip_speeds_route_direction' + '.csv', index=False) #+ str(datetime.now().strftime('_%Y_%m_%d'))

### FF: Add function calls:
if __name__ == "__main__":
    start = time.time()
    gtfs_path = "./data/berlin/timetable/"
    calc_speeds(path_to_gtfs= gtfs_path)
    stop = time.time()
    print(f"Took: %s to run" %(str(stop-start)))
