import os
import shelve

# Import the framework
from flask import Flask, g, render_template
from flask_restful import Resource, Api, reqparse

#reboot handler
reboot = False
# Create an instance of Flask
app = Flask(__name__)

# Create the API
api = Api(app)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = shelve.open("devices")
    return db

@app.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route("/")
def index():
    """Present some documentation"""

    return "<h1>Info page</h1>"


class DeviceList(Resource):
    def get(self):
        shelf = get_db()
        keys = list(shelf.keys())

        devices = []

        for key in keys:
            devices.append(shelf[key])

        return {'message': 'Success', 'data': devices}, 200

    def post(self):
        parser = reqparse.RequestParser()

        parser.add_argument('IOTUniversalID', required=True)
        parser.add_argument('DeviceNumber', required=True)
        parser.add_argument('IPAddress', required=True) 
        parser.add_argument('dataInterval', required=True)
        parser.add_argument('reboot', required=True)
        parser.add_argument('tempUnit', required=True)
        parser.add_argument('minTemp', required=True)
        parser.add_argument('maxTemp', required=True)
        parser.add_argument('minHum', required=True)
        parser.add_argument('maxHum', required=True)
        # Parse the arguments into an object
        args = parser.parse_args()

        shelf = get_db()
        shelf[args['IOTUniversalID']] = args

        return {'message': 'Device registered', 'data': args}, 201


class Device(Resource):
    def get(self, universal_id):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (universal_id in shelf):
            return {'message': 'Device not found', 'data': {}}, 404
        
        output_shelf = shelf[universal_id]
        if(shelf[universal_id]['reboot'] == '1'):
            updated_db = shelf[universal_id]
            updated_db['reboot'] = '0'
            shelf[universal_id] = updated_db

        return {'message': 'Device found', 'data': output_shelf}, 200


    def put(self, universal_id):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (universal_id in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        parser = reqparse.RequestParser()

        parser.add_argument('DeviceNumber', required=True)
        parser.add_argument('IPAddress', required=True)
        parser.add_argument('dataInterval', required=True)
        parser.add_argument('reboot', required=True)
        parser.add_argument('tempUnit', required=True)
        parser.add_argument('minTemp', required=True)
        parser.add_argument('maxTemp', required=True)
        parser.add_argument('minHum', required=True)
        parser.add_argument('maxHum', required=True)

        # Parse the arguments into an object
        args = parser.parse_args()
        args['IOTUniversalID'] = universal_id
        
        shelf[args['IOTUniversalID']] = args

        return {'message': 'Device updated', 'data': args}, 201        

    def delete(self, universal_id):
        shelf = get_db()

        # If the key does not exist in the data store, return a 404 error.
        if not (universal_id in shelf):
            return {'message': 'Device not found', 'data': {}}, 404

        del shelf[universal_id]
        return {'message': 'Device deleted'}, 204


api.add_resource(DeviceList, '/devices')
api.add_resource(Device, '/device/<string:universal_id>')

app.run(host='0.0.0.0', port=7777, debug=True)