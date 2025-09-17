import diplomarbeit as da
import matplotlib.pyplot as plt

if __name__ == '__main__':
    data_dict = './data/'
    city = 'portland' #TODO: Get Portland to Work
    ignore_linenumber = False
    da.speeds.calc_speeds(path_to_gtfs=data_dict+city+'/timetable/')
    data = da.add_speeds_to_osm.main(data_dict, city, ignore_linenumber)
    print(data.dropna(axis='rows'))
    data.dropna(axis='rows').plot.scatter(x='curvature', y='trip_speed')
    plt.show()


