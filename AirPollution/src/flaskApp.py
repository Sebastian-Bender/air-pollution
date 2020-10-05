from flask import Flask, render_template
from flask import request, jsonify
import main

app = Flask(__name__)

@app.route('/')
def map_func():
    with open('api_key.txt', 'r') as file:
        api_key = file.read()

    df_json = main.read_last_day_mean_sensorData().to_dict('index')

    owl = main.read_DB()
    owl = owl.resample('D', on = 'timestamp').mean()
    owl.reset_index(inplace = True)
    owl.dropna(inplace = True)

    bielefeld = main.read_location_from_DB('Bielefeld')
    bielefeld = bielefeld.resample('D', on = 'timestamp').mean()
    bielefeld.reset_index(inplace = True)
    bielefeld.dropna(inplace = True)

    paderborn = main.read_location_from_DB('Paderborn')
    paderborn = paderborn.resample('D', on = 'timestamp').mean()
    paderborn.reset_index(inplace = True)
    paderborn.dropna(inplace = True)


    return render_template(
        'map.html', 
        apikey = api_key, 
        df_json = df_json, 
        owl = owl.to_dict(orient = 'list'), 
        bielefeld = bielefeld.to_dict(orient = 'list'), 
        paderborn = paderborn.to_dict(orient = 'list'))

@app.route("/get_df", methods=['GET'])
def get_df():
    jsdata = request.args.get('jdata')
    df = main.read_sensor_from_DB(int(jsdata))
    df = df.resample('60min', on = 'timestamp').mean()
    df.dropna(inplace = True)
    df.reset_index(inplace = True)
    return jsonify(df.to_dict('list'))

@app.route("/get_location", methods=['GET'])
def get_location():
    jsdata = request.args.get('jdata')
    jsdata = jsdata[1:-1]
    print(jsdata)
    df = main.read_location_from_DB(jsdata)
    df = df.resample('D', on = 'timestamp').mean()
    df.dropna(inplace = True)
    df.reset_index(inplace = True)
    return jsonify(df.to_dict('list'))

if __name__ == '__main__':
    app.run(debug = True) 