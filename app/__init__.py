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


    @app.route('/auth/login', methods = ['POST', 'GET'])
    @auth.login_required
    def get_auth_token():
        token = g.user.generate_auth_token(600)
        return jsonify({'token': token.decode('ascii'), 'duration': 600})


    @app.route('/bucketlist/', methods=['POST', 'GET'])
    @auth.login_required
    def bucketlists():
        user = User.query.filter_by(email = g.user.email).first()
        user_buckelists_list = []
        user_buckelists = Bucketlist.query.filter_by(user_id = user.id).all()
        

        for user_buckelist in user_buckelists:
            user_buckelists_list.append(user_buckelist)

        user_bucketlist_id = len(user_buckelists_list)+1

        if request.method == "POST":
            name = str(request.data.get('name', ''))
            if name:
                bucketlist = Bucketlist(bucketlist_id=user_bucketlist_id, name=name, user_id=user.id)
                bucketlist.save()
                response = jsonify({
                    'id': bucketlist.id,
                    'bucketlist id':bucketlist.bucketlist_id,
                    'name': bucketlist.name,
                    'date_created': bucketlist.date_created,
                    'date_modified': bucketlist.date_modified,
                    })
                response.status_code = 201
                return response
        else:
            # GET
            q = request.args.get('q')
            limit = request.args.get('limit')
            page = request.args.get('page')
            if q:
                bucketlists = Bucketlist.query.filter_by(name=q, user_id=user.id)
                results = []

                for bucketlist in bucketlists:
                    obj = {
                        'id': bucketlist.id,
                        'bucketlist id':bucketlist.bucketlist_id,
                        'name': bucketlist.name,
                        'date_created': bucketlist.date_created,
                        'date_modified': bucketlist.date_modified,
                        'User id': g.user.email,
                        }
                    results.append(obj)
                response = jsonify(results)
                response.status_code = 200
                return response

            elif limit:
                bucketlists = Bucketlist.query.filter_by(name=q, user_id=user.id)
                results = []

                for bucketlist in bucketlists:
                    obj = {
                        'id': bucketlist.id,
                        'bucketlist id':bucketlist.bucketlist_id,
                        'name': bucketlist.name,
                        'date_created': bucketlist.date_created,
                        'date_modified': bucketlist.date_modified,
                        'User id' : g.user.email,
                        }
                    results.append(obj)
                if page:
                    if page.isdigit():
                        old_page = page - 1
                        old_limit = old_page * limit
                        next_limit = page * limit
                        if len(results) > next_limit:
                            new_page = results[old_limit:next_limit]
                            response = jsonify(new_page)
                            response.status_code = 200
                            return response
                        elif len(results) > old_limit and len(results) < next_limit:
                            new_page = results[old_limit:]
                            response = jsonify(new_page)
                            response.status_code = 200
                            return response
                        else:
                            return 404
                    else:
                        return 404


            else:
                bucketlists = Bucketlist.get_bucketlist(user.id)
                results = []
                limit = 20

                for bucketlist in bucketlists:
                    bucketlistresults = []
                    bucketlistsitems = BucketlistItem.get_items(bucketlist.id)
                    for bucketlistitem in bucketlistsitems:
                        obj = {
                            'id': bucketlistitem.id,
                            'name': bucketlistitem.name,
                            'bucketlist' : bucketlistitem.bucketlist_id
                            }
                        bucketlistresults.append(obj)
                    obj = {
                        'bucketlist id':bucketlist.bucketlist_id,
                        'name': bucketlist.name,
                        'items':bucketlistresults,
                        'date_created': bucketlist.date_created,
                        'date_modified': bucketlist.date_modified,
                        'Created By' : g.user.email,
                        }
                    results.append(obj)
                if page:
                    if page.isdigit():
                        old_page = int(page) - 1
                        old_limit = old_page * limit
                        next_limit = int(page) * limit
                        if len(results) > next_limit:
                            new_page = results[old_limit:next_limit]
                            response = jsonify(new_page)
                            response.status_code = 200
                            return response
                        elif len(results) > old_limit and len(results) < next_limit:
                            new_page = results[old_limit:]
                            response = jsonify(new_page)
                            response.status_code = 200
                            return response
                        else:
                            return 404
                    else:
                        return 404
                else:
                    this_page = results[:limit]
                    response = jsonify(this_page)
                    response.status_code = 200
                    return response



    @app.route('/bucketlist/<int:id>/items/', methods=['POST', 'GET'])
    @auth.login_required
    def bucketlistsitem(id):

        user = User.query.filter_by(email = g.user.email).first()
        user_bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user.id).one()
        item_buckelists = BucketlistItem.query.filter_by(bucketlist_id=user_bucketlist.id).all()


        item_list = []

        for i in item_buckelists:
            item_list.append(i)

        item_bucket_list_id = len(item_list)+1

        if not user_bucketlist:
            # Raise an HTTPException with a 404 not found status code
            abort(404)
        if request.method == "POST":
            name = str(request.data.get('name', ''))

            if name:
                bucketlistitem = BucketlistItem(name=name, item_id=item_bucket_list_id, bucketlist_id=user_bucketlist.id)
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
            # bucketlistsitems = BucketlistItem.get_all()
            bucketlistsitems = BucketlistItem.get_items(user_bucketlist.id)
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
    @auth.login_required
    def bucketlist_manipulation(id, **kwargs):
     # retrieve a buckelist using it's ID
        user = User.query.filter_by(email = g.user.email).first()
        bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user.id).first()
        if not bucketlist:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            bucketlistsitems = BucketlistItem.get_items(bucketlist.id)
            all_user_bucketlists = Bucketlist.get_bucketlist(user.id)
            for bucketlist_item in all_user_bucketlists:
                if bucketlist_item.bucketlist_id > id:
                    bucketlist_item.rearange(bucketlist_item.id)
            for item in bucketlistsitems:
                item.delete()
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
    @auth.login_required
    def bucketlistitems_manipulation(id, item_id,  **kwargs):
     # retrieve a buckelist using it's ID
        user = User.query.filter_by(email = g.user.email).first()
        bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user.id).first()
        if not bucketlist:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        bucketlistitem = BucketlistItem.query.filter_by(bucketlist_id=bucketlist.id, item_id=item_id).first()
        if not bucketlistitem:
            # Raise an HTTPException with a 404 not found status code
            abort(404)

        if request.method == 'DELETE':
            user_bucketlistitems = BucketlistItem.query.filter_by(bucketlist_id=bucketlist.id).all()
            for bucketlist_item in user_bucketlistitems:
                if bucketlist_item.item_id > item_id:
                    bucketlist_item.rearange(bucketlist_item.id)

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