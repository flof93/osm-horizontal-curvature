from pathlib import Path

DATA_DIR = Path('~/Documents/Diplomarbeit/osm-horizontal-curvature/data').expanduser()
RESULTS_DIR = Path('~/Documents/Diplomarbeit/osm-horizontal-curvature/results').expanduser()
STADIA_API = 'ccf6fac2-c284-43e8-b9f2-83716f034ba2' #for using stadia when creating maps

REGION_DICT = {'NL':'Westeuropa',
               'BE':'Westeuropa',
               'DE':'DACH',
               'FR':'Westeuropa',
               'HU':'Zentraleuropa',
               'RO':'Süd- und Südosteuropa',
               'SE':'Nordeuropa',
               'AT':'DACH',
               'FI':'Nordeuropa',
               'PL':'Zentraleuropa',
               'UA':'Osteuropa',
               'IT':'Süd- und Südosteuropa',
               'UK':'Westeuropa',
               'AU':'Außereuropäisch',
               'US':'Außereuropäisch',
               'CZ':'Zentraleuropa',
               'LV':'Osteuropa',
               'RU':'Osteuropa',
               'BG':'Süd- und Südosteuropa',
               'CA':'Außereuropäisch',
               'HR':'Süd- und Südosteuropa',
               'CH':'DACH',
               'NO':'Nordeuropa'}

COLUMN_NAMES_DE = {'curvature': 'Kurvigkeit [gon/km]',
                   'avg_dist': 'Durchschnittlicher Haltestellenabstand [m]',
                   'trip_speed': 'Durchschnittsgeschwindigkeit [km/h]',
                   'height_up': 'Aufstieg [m/km]',
                   'height_down': 'Abstieg [m/km]',
                   'rho_b': 'Bebauungsdichte [%]',
                   'gauge': 'Spurweite [mm]',
                   'Buffer_Width': 'Bufferbreite [m]'}

COLUMN_NAMES_TEX_TWO_LINES = {'curvature': r'$\bar\gamma$' + '\n' + r'[gon/km]',
                    'avg_dist': r'$\bar l_{\text{Hst}}$' + '\n' + r'[m]',
                    'trip_speed': r'$\bar V$' + '\n' + r'[km/h]',
                    'height_up': r'$\bar s^{\uparrow}$' + '\n' + r'[\textperthousand]',
                    'height_down': r'$\bar s^{\downarrow}$' + '\n' + r'[\textperthousand]',
                    'rho_b': r'$\rho_\text{B}$' + '\n' + r'[\%]',
                    'gauge': r'$G$' + '\n' + r'[mm]',
                    'Buffer_Width': r'$b_{\text{Buf}}$' +'\n'+r'[m]'}

COLUMN_NAMES_TEX = {'curvature': r'$\bar\gamma$ [gon/km]',
                    'avg_dist': r'$\bar l_{\text{Hst}}$ [m]',
                    'trip_speed': r'$\bar V$ [km/h]',
                    'height_up': r'$\bar s^{\uparrow}$ [\textperthousand]',
                    'height_down': r'$\bar s^{\downarrow}$ [\textperthousand]',
                    'rho_b': r'$\rho_\text{B}$ [\%]',
                    'gauge': r'$G$ $[mm]$',
                    'Buffer_Width': r'$b_{\text{Buf}}$ [m]',
                    'phi_tram': r'$\phi_{\text{Tram}}$',
                    'phi_street': r'$\phi_{\text{Straße}}$'
                    }

COLUMN_NAMES_TEX_SHORT = {'curvature': r'$\bar\gamma$',
                          'avg_dist': r'$\bar l_{\text{Hst}}$',
                          'trip_speed': r'$\bar V$',
                          'height_up': r'$\bar s^{\uparrow}$',
                          'height_down': r'$\bar s^{\downarrow}$',
                          'rho_b': r'$\rho_\text{B}$',
                          'gauge': r'$G$',
                          'Buffer_Width': r'$b_{\text{Buf}}$',
                          'distance': r'$l_{\text{Rel}}$',
                          'phi_tram': r'$\phi_{\text{Tram}}$',
                          'phi_street': r'$\phi_{\text{Straße}}$'}

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