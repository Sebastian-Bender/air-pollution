import requests
import pandas as pd
import sqlite3
import datetime
import reverse_geocoder as rg

# longitudes
longitude_min = 8.3255
longitude_max = 9.5537

# latitudes
latitude_max = 52.2396
latitude_min = 51.4762

def get_current_data():
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
    
    df = df[['timestamp', 'SensorID', 'latitude', 'longitude', 'P1', 'P2']]
    df.columns = ['timestamp', 'sensor_id', 'latitude', 'longitude', 'PM10', 'PM2_5']
    df.reset_index(inplace = True, drop = True)
    
    return df

def create_sensorList():
    df = get_current_data()

    sensorList = set(df['sensor_id'])
    print(len(sensorList))

    with open('SensorList.txt', 'w') as f:
        for i in sensorList:
            f.writelines('%s\n' %i)
    

def create_locationList():
    df = get_current_data()
    df = df.drop_duplicates(['sensor_id'])
    locations = {}
    for index, row in df.iterrows():
        locations[row.sensor_id] = rg.search((row.latitude, row.longitude))[0]['name']

    with open('LocationList.txt', 'w') as f:
        f.write(str(locations))

def create_DB(start = '2020-07-31'):
    conn = sqlite3.connect('sensor.db')

    sensorList = [line.rstrip('\n') for line in open("SensorList.txt")]

    sensorData = pd.DataFrame()
    start = datetime.datetime.strptime(start, '%Y-%m-%d').date() + datetime.timedelta(days = 1)
    if start >= datetime.datetime.now().date():
        return ""
    for sensor in sensorList:
        print(sensor)
        date = start
        temp = []
        comp = []
        while date < datetime.datetime.now().date():
            d = date.strftime('%Y-%m-%d')
            try:
                temp.append(pd.read_csv(f'https://archive.sensor.community/{d}/{d}_sds011_sensor_{sensor}.csv', sep = ';'))
            except:
                print(f"{d}\tdoes not exist")
            date += datetime.timedelta(days = 1)
        try:
            comp = temp[0]
            for i in range(1, len(temp)):
                comp = pd.concat([comp, temp[i]], axis = 0)
            comp['timestamp'] = pd.to_datetime(comp['timestamp'])
        except:
            print("\tno data")
            continue
        
        sensorData = pd.concat([sensorData, comp], axis = 0)

    sensorData = sensorData[['timestamp', 'sensor_id', 'lat', 'lon', 'P1', 'P2']]
    sensorData.columns = ['timestamp', 'sensor_id', 'latitude', 'longitude', 'PM10', 'PM2_5']
    sensorData.reset_index(inplace = True, drop = True)
    
    sensorData = sensorData.groupby('sensor_id', group_keys = False).resample('60min', on = 'timestamp').mean()
    sensorData.dropna(inplace = True)
    sensorData.sensor_id = sensorData.sensor_id.astype('int64')
    sensorData.reset_index(inplace = True)
    sensorData = sensorData.round({'PM10': 2, 'PM2_5': 2})

    # Add location column
    with open('LocationList.txt', 'r') as f:
        s = f.read()
        locations = eval(s)
    sensorData['location'] = ""
    sensorData['location'] = sensorData['sensor_id'].apply(lambda x: locations[x])

    sensorData.to_sql(name = 'sensorData', con = conn, if_exists='append')

def update_DB():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    c.execute('SELECT MAX (timestamp) FROM sensorData')
    t = c.fetchone()[0].split(" ")[0]
    print('last update from: ' + t)
    create_DB(t)


def read_DB():
    conn = sqlite3.connect('sensor.db')
    df = pd.read_sql_query('SELECT * FROM sensorData', conn, index_col='index')
    df.timestamp = pd.to_datetime(df.timestamp)
    return df

def read_last_day_mean_sensorData():
    df = read_DB()
    df = df.groupby('sensor_id', group_keys = False).resample('D', on = 'timestamp').mean()
    df.dropna(inplace = True)
    df.sensor_id = df.sensor_id.astype('int64')
    df.reset_index(inplace = True)
    df = df.round({'PM10': 2, 'PM2_5': 2})
    # Add location column

    with open('LocationList.txt', 'r') as f:
        s = f.read()
        locations = eval(s)
    df['location'] = ""
    df['location'] = df['sensor_id'].apply(lambda x: locations[x])

    return df.loc[df.groupby('sensor_id').timestamp.idxmax()].reset_index(drop = True)

def read_sensor_from_DB(sensorID):
    conn = sqlite3.connect('sensor.db')
    df = pd.read_sql_query(f'SELECT * FROM sensorData WHERE sensor_id = {sensorID}', conn, index_col = 'index')
    df.timestamp = pd.to_datetime(df.timestamp)
    return df

def read_location_from_DB(location):
    conn = sqlite3.connect('sensor.db')
    df = pd.read_sql_query(f'SELECT * FROM sensorData WHERE location = "{location}"', conn, index_col = 'index')
    df.timestamp = pd.to_datetime(df.timestamp)
    return df

def data_to_json(df):
    return df.to_dict('index')


if __name__ == '__main__':
    read_DB()
