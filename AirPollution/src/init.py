import pandas as pd
import requests
import time
import sqlite3
import datetime

def get_sensorList():
    # longitudes
    longitude_min = 8.3255
    longitude_max = 9.5537

    # latitudes
    latitude_max = 52.2396
    latitude_min = 51.4762

    url = 'http://api.luftdaten.info/static/v1/data.json'
    i = 0
    sensor_json = requests.get(url).json()
    df = pd.DataFrame(sensor_json)
    while(i < 2):
        time.sleep(2 * 60)
        sensor_json = requests.get(url).json()
        temp_df = pd.DataFrame(sensor_json)
        df = pd.concat([df, temp_df], axis = 0)
        i+=1

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

    df.reset_index(inplace = True, drop = True)
    df['SensorID'] = df['sensor'].apply(lambda x: x.get('id'))

    sensorList = set(df['SensorID'])
    print(len(sensorList))

    with open('SensorList.txt', 'w') as f:
        for i in sensorList:
            f.writelines('%s\n' %i)


def create_DB():
    conn = sqlite3.connect('sensor.db')
    c = conn.cursor()

    #c.execute('''CREATE TABLE sensorData
    #            (id int, date datetime, sensor_id int, latitude decimal, longitude decimal, pm10 real, pm2_5 real)''')

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

#get_sensorList()
create_DB()
