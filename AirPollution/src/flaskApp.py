from flask import Flask,render_template, jsonify
import main

app = Flask(__name__)

@app.route('/')
def map_func():
    with open('api_key.txt', 'r') as file:
        api_key = file.read()

    df_json = main.data_to_json(main.get_data())
    return render_template('map.html', apikey = api_key, df_json = df_json)

if __name__ == '__main__':
    app.run(debug = True) 