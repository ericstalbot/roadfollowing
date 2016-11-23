from flask import Flask, request, jsonify, json, render_template
from get_path import get_path

import os
import shelve

app = Flask(__name__)

db_path = os.environ['DB_PATH']




@app.route('/path', methods=['GET'])
def path():
    waypoints = request.args.get('waypoints')

    waypoints = json.loads(waypoints)

    path = get_path(waypoints)

    return jsonify(path)


@app.route('/ride/<string:ride_id>', methods=['GET', 'PUT'])
def route(ride_id):


    if request.method == 'PUT':
        db = shelve.open(db_path)
        db[ride_id] = request.get_json()
        db.close()
        return 'ok'
    elif request.method == 'GET':
        db = shelve.open(db_path)
        r = db[ride_id]
        db.close()
        return jsonify(r)



@app.route('/')
def main():
    return render_template('gtfsspatial.html')

