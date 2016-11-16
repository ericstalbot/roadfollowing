from flask import Flask, request, jsonify, json, render_template
from get_path import get_path


app = Flask(__name__)

@app.route('/path', methods=['GET'])
def path():
    waypoints = request.args.get('waypoints')

    waypoints = json.loads(waypoints)

    path = get_path(waypoints)

    return jsonify(path)


@app.route('/ride/<string:ride_id>', methods=['GET', 'PUT'])
def route(ride_id):
    if request




@app.route('/')
def main():
    return render_template('gtfsspatial.html')

