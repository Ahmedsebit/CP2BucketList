import json
from flask_api import FlaskAPI, status
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify, abort, make_response, g, url_for, session
from instance.config import app_config
from flask_bcrypt import Bcrypt
import jwt
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
# initialize sql-alchemy
db = SQLAlchemy()

auth = HTTPBasicAuth()

def create_app(config_name):
    from app.models import Bucketlist, BucketlistItem, User
    app = FlaskAPI(__name__, instance_relative_config=True)
    bcrypt = Bcrypt(app)
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)


    @app.route('/auth/register', methods = ['POST', 'GET'])
    def new_user():
        user = User.query.filter_by(email=request.data['email']).first()
        if not user:
            try:
                post_data = request.data
                email = post_data['email']
                password = post_data['password']
                if email is None or password is None:
                    abort(400) # missing arguments
                if User.query.filter_by(email = email).first() is not None:
                    abort(400) # existing user
                user = User(email = email)
                user.hash_password(password)
                db.session.add(user)
                db.session.commit()
                return jsonify({ 'email': user.email }), 201

            except Exception as e:
                    response = {
                        'message': str(e)
                    }
                    return response, 401
        else:
            response = {
                'message': 'User already exists. Please login.'
            }
            return response, 202


    @app.route('/auth/login', methods = ['POST', 'GET'])
    def login():
        post_data = request.data
        email = post_data['email']
        password = post_data['password']
        user = User.query.filter_by(email = email).first()
        
        if user:
            try:
                user_access = verify_password(email,password)
                if user_access:
                    token = g.user.generate_auth_token(600)
                    response = {
                        'message':'You logged in succesfully',
                        'token': token.decode('ascii')
                        }
                    return response, 200
                else:
                    response = {'status_code' : 401}
                    return response, 401
            except Exception as e:
                response = {'status_code' : 401}
                return response, 200
        else:
            response = {'status_code' : 401}
            return response, 401



    @auth.verify_password
    def verify_password(email_or_token, password):
        # first try to authenticate by token
        user = User.verify_auth_token(email_or_token)
        if not user:
            # try to authenticate with username/password
            user = User.query.filter_by(email = email_or_token).first()
            if not user or not user.verify_password(password):
                return False
        g.user = user
        return True


    @app.route('/api/token', methods=['POST', 'GET'])
    @auth.login_required
    def get_auth_token():
        token = g.user.generate_auth_token(600)
        return jsonify({'token': token.decode('ascii'), 'duration': 600})


    @app.route('/bucketlist/', methods=['POST', 'GET'])
    @auth.login_required
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
                         'date_modified': bucketlist.date_modified,
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