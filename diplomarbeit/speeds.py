import pandas as pd
import csv
import os
from datetime import datetime, timedelta
import time

# Pfad zum GTFS-Datensatz angeben
# path_to_gtfs = "./data/wien/"

## FF: make functions callable
def calc_speeds(path_to_gtfs):

    # GTFS-Datensatz laden
    print(f"Daten einlesen...")
    routes = pd.read_csv(path_to_gtfs + "routes.txt")
    trips = pd.read_csv(path_to_gtfs + "trips.txt")
    stop_times = pd.read_csv(path_to_gtfs + "stop_times.txt")
    #stops = pd.read_csv(path_to_gtfs + "stops.txt")


    with open(file=path_to_gtfs + "stops.txt", mode='r') as stopfile:
        stops_dict = csv.reader(stopfile)
        stops = {row[0]:row[1] for row in stops_dict}

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
            shape_dist_traveled = float(row['shape_dist_traveled'])
            #stop_sequence = int(row['stop_sequence'])
            arrival_time_str = row['arrival_time']

            # Wenn die Stundenangabe größer als 23 ist, subtrahiere 24 und erhöhe den Tag um 1
            if int(arrival_time_str[:2]) > 23:
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
            trip_speed = (total_distance / total_time) * 3.6

            # Ausgangstation ermitteln
            first_stop_id = data[0][2]

            # Endstation ermitteln
            last_stop_id = data[-1][2]

            first_stop_name = stops[first_stop_id]
            last_stop_name = stops[last_stop_id]

            data_df.append([trip_id, trip_speed, first_stop_id, last_stop_id, first_stop_name, last_stop_name])

            # Füge trip_id und Durchschnittsgeschwindigkeit dem DataFrame hinzu
            # df = pd.concat([df, pd.DataFrame({'trip_id': [trip_id], 'trip_speed': [trip_speed]})], ignore_index=True)#, 'first_stop_id': [first_stop_id], 'last_stop_id': [last_stop_id]})], ignore_index=True)

        df = pd.DataFrame(data=data_df, columns=['trip_id', 'trip_speed', 'first_stop_id', 'last_stop_id', 'first_stop_name', 'last_stop_name'])


        # Füge die Spalte 'route_short_name' zum DataFrame hinzu
        df = pd.merge(stop_times_tram[['trip_id', 'route_short_name', 'direction_id']].drop_duplicates(), df, on='trip_id')


        # Ein leeres DataFrame erstellen
        # df1 = pd.DataFrame(columns=['route_short_name', 'direction_id', 'first_stop_name', 'last_stop_name','avg_speed'])

        # Gruppierung nach route_short_name und direction_id durchführen und Durchschnittsgeschwindigkeit berechnen
        print(f"Berechne die Durchschnittsgeschwindigkeiten pro route_short_name und direction_id...")

        grouped = df.groupby(['route_short_name', 'direction_id', 'first_stop_name', 'last_stop_name'])

        data_df=[]

        for name, group in grouped:
            # Berechne die Durchschnittsgeschwindigkeit für diese Gruppe
            avg_speed = group['trip_speed'].mean()
            number_trips = group['trip_speed'].count()

            # Füge die Informationen zu dieser Gruppe (route_short_name, direction_id und Durchschnittsgeschwindigkeit) dem DataFrame hinzu
            data_dict={'route_short_name': name[0],
                       'direction_id': name[1],
                       'avg_speed': avg_speed,
                       'first_stop_name':name[2],
                       'last_stop_name':name[3],
                       'number_trips': number_trips}
            #first_stop_name = stops[data_dict['first_stop_id']]
            #last_stop_name = stops[data_dict['last_stop_id']]
            data_df.append((data_dict['route_short_name'],data_dict['direction_id'],data_dict['avg_speed'], data_dict['first_stop_name'], data_dict['last_stop_name'], data_dict['number_trips']))

        df1 = pd.DataFrame(data=data_df, columns=['route_short_name','direction_id', 'trip_speed', 'first_stop_name', 'last_stop_name', 'number_trips'])

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
        if not os.path.exists(path_to_gtfs + 'results'):
            os.makedirs(path_to_gtfs + 'results')
        #df1_sorted.to_excel(path_to_gtfs + 'results/sorted_trip_speeds_route_direction' + str(datetime.now().strftime('_%d_%m_%Y')) + '.xlsx', index=False)
        #df1_sorted.to_latex(path_to_gtfs + 'results/trip_speeds_route_direction' + str(datetime.now().strftime('_%d_%m_%Y')) + '.tex', index=False)

        ### FF: Ergänzung um Export in csv, zur weiteren Verwendung, entfernung des Datumsstempels
        df1_sorted.to_csv(path_to_gtfs + 'results/trip_speeds_route_direction' + '.csv', index=False) #+ str(datetime.now().strftime('_%Y_%m_%d'))

### FF: Add function calls:
if __name__ == "__main__":
    start = time.time()
    gtfs_path = "./data/wien/timetable/"
    calc_speeds(path_to_gtfs= gtfs_path)
    stop = time.time()
    print(f"Took: %s to run" %(str(stop-start)))
