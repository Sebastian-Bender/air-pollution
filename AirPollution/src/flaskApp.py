from flask import Flask, render_template
from flask import request, jsonify
import main

app = Flask(__name__)

@app.route('/')
def map_func():
    with open('api_key.txt', 'r') as file:
        api_key = file.read()

    df_json = main.data_to_json(main.get_data())

    sensor = main.read_DB()
    sensor = sensor.resample('60min', on = 'timestamp').mean()
    sensor.reset_index(inplace = True)
    sensor.dropna(inplace = True)
    return render_template('map.html', apikey = api_key, df_json = df_json, sensor = sensor.to_dict(orient = 'list'))

@app.route("/get_df", methods=['GET'])
def get_df():
    jsdata = request.args.get('jdata')
    df = main.read_sensor_from_DB(int(jsdata))
    df = df.resample('60min', on = 'timestamp').mean()
    df.dropna(inplace = True)
    df.reset_index(inplace = True)
    return jsonify(df.to_dict('list'))

if __name__ == '__main__':
    app.run(debug = True) 