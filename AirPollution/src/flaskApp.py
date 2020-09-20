from flask import Flask,render_template

app = Flask(__name__)

@app.route('/')
def map_func():
    with open('api_key.txt', 'r') as file:
        api_key = file.read()

    return render_template('map.html', apikey = api_key)
if __name__ == '__main__':
    app.run(debug = True) 