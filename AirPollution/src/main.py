import requests
import pandas as pd

# longitudes
longitude_min = 8.3255 
longitude_max = 9.5537

# latitudes
latitude_max = 52.2396 
latitude_min = 51.4762

def get_data():
    # returns a dataframe containing p10 and p2.5 values of sensors in OWL and the longitude latitude values of these sensors
    url = 'http://api.luftdaten.info/static/v1/data.json'
    r = requests.get(url)
    rdata = r.json()
    df = pd.DataFrame(rdata)

    df = df[df['location'].map(lambda x: 'DE' in x.values())]
    df = df[df['sensor'].map(lambda x: 'SDS011' in x['sensor_type'].values())]

    longitude = df['location'].apply(lambda x: x.get('longitude'))
    latitude = df['location'].apply(lambda x: x.get('latitude'))

    df = df.assign(longitude = longitude.values)
    df = df.assign(latitude = latitude.values)
    df.drop(['location', 'sampling_rate', 'id'], axis = 1, inplace = True)

    df['longitude'] = pd.to_numeric(df.longitude)
    df['latitude'] = pd.to_numeric(df.latitude)

    df = df[df.longitude <= longitude_max]
    df = df[df.longitude >= longitude_min]
    df = df[df.latitude <= latitude_max]
    df = df[df.latitude >= latitude_min]


    df['SensorID'] = df['sensor'].apply(lambda x: x.get('id'))

    p1 = df['sensordatavalues'].apply(lambda x: x[0]).apply(lambda x: x.get('value'))
    p2 = df['sensordatavalues'].apply(lambda x: x[1]).apply(lambda x: x.get('value'))
    df['P1'] = p1
    df['P2'] = p2

    df.drop(['sensor', 'sensordatavalues'], axis = 1, inplace = True)

    # only keep the newest value for sensors with multiple values
    df.sort_values(by = ['SensorID', 'timestamp'], ascending = False, inplace = True)
    df.drop_duplicates(subset='SensorID', keep="first", inplace = True)
    
    df.reset_index(inplace = True, drop = True)
    
    return df

def get_historical_data():
    return ""

def data_to_json(df):
    return df.to_dict('index')


if __name__ == '__main__':
    df = get_data()
    print(df)
