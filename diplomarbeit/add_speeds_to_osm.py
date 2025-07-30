import diplomarbeit
import pandas as pd

def exctract_lines(network: pd.DataFrame) -> pd.DataFrame:

    grouped = network.groupby(['Linie'])
    data_df =[]

    for name, group in grouped:
        distance = group['Distanz'].max()/1000
        curvature = group['Winkel'].max() / distance

        data_df.append([name[0],
                        group['Nummer'].unique()[0],
                        group['From'].unique()[0],
                        group['To'].unique()[0],
                        distance,
                   curvature
                   #group['Gauge'].unique()[0],
                   ])

    columns=['line_name', 'line_number', 'from','to','distance','curvature']
    df_lines = pd.DataFrame(data=data_df, columns=columns)

    return df_lines

    # for j in network.railway_lines:
    #     try:
    #         curv = max(j.gamma) / (max(j.s) / 1000) #TODO: Muss in Auswertung korrigiert werden!
    #         curvature_angular.append(curv)
    #         dist.append(max(j.s) / 1000)
    #
    #     except ValueError:
    #         logger.warning(
    #             "Ignoring %s %s, no values for curvature or change of angle available" % (str(city), str(j)))
    #         curvature_angular.append(np.nan)
    #         dist.append((np.nan))
    #
    #     stadt.append(city)
    #     linie.append(j.ref if hasattr(j, 'ref') else '')
    #     richtung.append(str(j))
    #
    #     try:
    #         gauge.append(int(j.ways[0].tags['gauge']))
    #     except (KeyError, IndexError, ValueError):
    #         gauge.append(np.nan)
    #         logger.warning("No Gauge data for line %s in %s available" % (str(j), str(city)))
    #     # except TypeError: # könnte relevant sein, wenn die Linie im Dreischienengleis startet
    #
    #     ele = da_utils.get_heights_for_line(j)
    #     if ele:
    #         elevation_min.append(min(ele))
    #         elevation_max.append(max(ele))
    #     else:
    #         elevation_min.append(np.nan)
    #         elevation_max.append(np.nan)