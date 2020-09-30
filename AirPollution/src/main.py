import requests
import pandas as pd
import sqlite3
import datetime

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
    
    df = df[['timestamp', 'SensorID', 'latitude', 'longitude', 'P1', 'P2']]
    df.columns = ['timestamp', 'sensor_id', 'latitude', 'longitude', 'PM10', 'PM2_5']
    df.reset_index(inplace = True, drop = True)
    
    return df

def create_temp_DB():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()
    #if (c.execute('SELECT name FROM sensor.db WHERE type = "table" AND name = "tempData"')):
    c.execute('DROP TABLE tempData')
    df = get_data()
    df.to_sql(name = 'tempData', con = conn)

def read_temp_DB():
    conn = sqlite3.connect('sensor.db')
    df = pd.read_sql_query('SELECT * FROM tempData', con = conn, index_col = 'index')
    return df

def create_sensorList():
    df = get_data()
    sensorList = set(df['SensorID'])
    print(len(sensorList))

    with open('SensorList.txt', 'w') as f:
        for i in sensorList:
            f.writelines('%s\n' %i)

def create_DB():
    conn = sqlite3.connect('sensor.db')

    sensorList = [line.rstrip('\n') for line in open("SensorList.txt")]

    sensorData = pd.DataFrame()
    for sensor in sensorList:
        print(sensor)
        date = datetime.datetime.strptime('2020-09-23', '%Y-%m-%d').date()
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

    sensorData.drop(['sensor_type', 'location', 'durP1', 'ratioP1', 'durP2', 'ratioP2'], axis = 1, inplace = True)

    sensorData = sensorData[['timestamp', 'sensor_id', 'lat', 'lon', 'P1', 'P2']]
    sensorData.columns = ['timestamp', 'sensor_id', 'latitude', 'longitude', 'PM10', 'PM2_5']
    sensorData.reset_index(inplace = True, drop = True)

    sensorData.to_sql(name = 'sensorData', con = conn)

def update_DB():
    conn = sqlite3.connect('sensor.db')
    df = read_temp_DB()
    df.to_sql(name = 'sensorData', con = conn, if_exists = 'append')

def read_DB():
    conn = sqlite3.connect('sensor.db')
    df = pd.read_sql_query('SELECT * FROM sensorData', conn, index_col='index')
    df.timestamp = pd.to_datetime(df.timestamp)
    return df

def read_sensor_from_DB(sensorID):
    conn = sqlite3.connect('sensor.db')
    df = pd.read_sql_query(f'SELECT * FROM sensorData WHERE sensor_id = {sensorID}', conn, index_col = 'index')
    df.timestamp = pd.to_datetime(df.timestamp)
    return df

def data_to_json(df):
    return df.to_dict('index')


if __name__ == '__main__':
    read_DB()
