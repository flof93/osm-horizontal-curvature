from pathlib import Path

DATA_DIR = Path('~/Documents/Diplomarbeit/osm-horizontal-curvature/data').expanduser()

STADIA_API = 'ccf6fac2-c284-43e8-b9f2-83716f034ba2'

REGION_DICT = {'NL':'BeNeLux',
               'BE':'BeNeLux',
               'DE':'DACH',
               'FR':'Westeuropa',
               'HU':'SEE',
               'RO':'SEE',
               'SE':'Skandinavien',
               'AT':'DACH',
               'FI':'Skandinavien',
               'PL':'Osteuropa',
               'UA':'Osteuropa',
               'IT':'SEE',
               'UK':'Westeuropa',
               'AU':'Ozeanien',
               'US':'Nordamerika',
               'CZ':'Osteuropa',
               'LV':'Osteuropa',
               'RU':'Osteuropa',
               'BG':'SEE',
               'CA':'Nordamerika',
               'HR':'SEE',
               'CH':'DACH'}

COLUMN_NAMES_DE = {'curvature': 'Kurvigkeit [gon/km]',
                   'avg_dist': 'Durchschnittlicher Haltestellenabstand [m]',
                   'trip_speed': 'Durchschnittsgeschwindigkeit [km/h]',
                   'height_up': 'Aufstieg [m/km]',
                   'height_down': 'Abstieg [m/km]',
                   'rho_b': 'Bebauungsdichte [-]',
                   'gauge': 'Spurweite [mm]',
                   'Buffer_Width': 'Bufferbreite [m]'}

COLUMN_NAMES_TEX_TWO_LINES = {'curvature': r'$\bar\gamma$' + '\n' + r'[gon/km]',
                    'avg_dist': r'$\bar l_{Hst}$' + '\n' + r'[m]',
                    'trip_speed': r'$\bar V$' + '\n' + r'[km/h]',
                    'height_up': r'$\bar s^{\uparrow}$' + '\n' + r'[\textperthousand]',
                    'height_down': r'$\bar s^{\downarrow}$' + '\n' + r'[\textperthousand]',
                    'rho_b': r'$\rho_B$' + '\n' + r'[1]',
                    'gauge': r'$G$' + '\n' + r'[mm]',
                    'Buffer_Width': r'$b_{Buf}$' +'\n'+r'[m]'}

COLUMN_NAMES_TEX = {'curvature': r'$\bar\gamma$ [gon/km]',
                    'avg_dist': r'$\bar l_{Hst}$ [m]',
                    'trip_speed': r'$\bar V$ [km/h]',
                    'height_up': r'$\bar s^{\uparrow}$ [\textperthousand]',
                    'height_down': r'$\bar s^{\downarrow}$ [\textperthousand]',
                    'rho_b': r'$\rho_B$ [1]',
                    'gauge': r'$G$ [mm]',
                    'Buffer_Width': r'$b_{Buf}$ [m]'}

COLUMN_NAMES_TEX_SHORT = {'curvature': r'$\bar\gamma$',
                          'avg_dist': r'$\bar l_{Hst}$',
                          'trip_speed': r'$\bar V$',
                          'height_up': r'$\bar s^{\uparrow}$',
                          'height_down': r'$\bar s^{\downarrow}$',
                          'rho_b': r'$\rho_B$',
                          'gauge': r'$G$',
                          'Buffer_Width': r'$b_{Buf}$'}

DATAFIELD_VARIABLENAME = {'region': 'varRegion',
                          'gauge': 'varGauge',
                          'trip_speeds_new': 'varTripSpeed',
                          'avg_dist': 'varAvgDist',
                          'Buffer_Width': 'varBbuf',
                          'Stadt': 'varStadt',
                          'Country': 'varCountry',
                          'GTFS-Daten': 'varGTFSLink',
                          'GTFS-Provider': 'varGTFSProvider',
                          'Nord': 'varNord',
                          'Sued': 'varSued',
                          'Ost': 'varOst',
                          'West': 'varWest',
                          'Anzahl Relationen': 'varnLinien',
                          }