from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask import request, abort, json, jsonify
# local import
from instance.config import app_config

# initialize sql-alchemy
db = SQLAlchemy()

def create_app(config_name):
    from app.models import Bucketlist, BucketlistItem

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    @app.route('/bucketlist/', methods=['POST', 'GET'])
    def bucketlists():
        if request.method == "POST":
            name = str(request.data.get('name', ''))
            if name:
                bucketlist = Bucketlist(name=name)
                bucketlist.save()
                response = jsonify({
                    'id': bucketlist.id,
                    'name': bucketlist.name,
                    'date_created': bucketlist.date_created,
                    'date_modified': bucketlist.date_modified
                })
                response.status_code = 201
                return response
        else:
            # GET
            bucketlists = Bucketlist.get_all()
            results = []

            for bucketlist in bucketlists:
                obj = {
                    'id': bucketlist.id,
                    'name': bucketlist.name,
                    'date_created': bucketlist.date_created,
                    'date_modified': bucketlist.date_modified
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response

    @app.route('/bucketlist/<int:id>/items/', methods=['POST', 'GET'])
    def bucketlistsitem(id):
        bucketlist = Bucketlist.query.filter_by(id=id).first()
        if not bucketlist:
            # Raise an HTTPException with a 404 not found status code
            abort(404)
        if request.method == "POST":
            name = str(request.data.get('name', ''))
            if name:
                bucketlistitem = BucketlistItem(name=name, bucketlist_id=id)
                bucketlistitem.save()
                response = jsonify({
                    'id': bucketlistitem.id,
                    'name': bucketlistitem.name,
                    'date_created': bucketlistitem.date_created,
                    'date_modified': bucketlistitem.date_modified,
                    'bucketlist' : bucketlistitem.bucketlist_id
                })
                response.status_code = 201
                return response
        else:
            # GET
            bucketlistsitems = BucketlistItem.get_all()
            results = []

            for bucketlistitem in bucketlistsitems:
                obj = {
                    'id': bucketlistitem.id,
                    'name': bucketlistitem.name,
                    'date_created': bucketlistitem.date_created,
                    'date_modified': bucketlistitem.date_modified,
                    'bucketlist' : bucketlistitem.bucketlist_id
                }
                results.append(obj)
            response = jsonify(results)
            response.status_code = 200
            return response


    @app.route('/bucketlist/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def bucketlist_manipulation(id, **kwargs):
     # retrieve a buckelist using it's ID
        bucketlist = Bucketlist.query.filter_by(id=id).first()
        if not bucketlist:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            bucketlist.delete()
            return {
                "message": "bucketlist {} deleted successfully".format(bucketlist.id)
                }, 200

        elif request.method == 'PUT':
            name = str(request.data.get('name', ''))
            bucketlist.name = name
            bucketlist.save()
            response = jsonify({
                'id': bucketlist.id,
                'name': bucketlist.name,
                'date_created': bucketlist.date_created,
                'date_modified': bucketlist.date_modified
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': bucketlist.id,
                'name': bucketlist.name,
                'date_created': bucketlist.date_created,
                'date_modified': bucketlist.date_modified
            })
            response.status_code = 200
            return response


    @app.route('/bucketlist/<int:id>/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
    def bucketlistitems_manipulation(id, item_id,  **kwargs):
     # retrieve a buckelist using it's ID
        bucketlist = Bucketlist.query.filter_by(id=id).first()
        if not bucketlist:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        bucketlistitem = BucketlistItem.query.filter_by(id=item_id).first()
        if not bucketlistitem:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            bucketlistitem.delete()
            return {
                "message": "bucketlist item {} deleted successfully".format(bucketlistitem.id)
            }, 200

        elif request.method == 'PUT':
            name = str(request.data.get('name', ''))
            bucketlistitem.name = name
            bucketlistitem.save()
            response = jsonify({
                'id': bucketlistitem.id,
                'name': bucketlistitem.name,
                'date_created': bucketlistitem.date_created,
                'date_modified': bucketlistitem.date_modified,
                'bucketlist' : bucketlistitem.bucketlist_id
            })
            response.status_code = 200
            return response
        else:
            # GET
            response = jsonify({
                'id': bucketlistitem.id,
                'name': bucketlistitem.name,
                'date_created': bucketlistitem.date_created,
                'date_modified': bucketlistitem.date_modified,
                'bucketlist': bucketlistitem.bucketlist_id
            })
            response.status_code = 200
            return response


    return app