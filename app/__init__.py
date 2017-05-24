import json
import re
from flask_api import FlaskAPI, status
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify, abort, make_response, g, url_for, session
from instance.config import app_config
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
# initialize sql-alchemy
db = SQLAlchemy()


def create_app(config_name):
    from app.models import Bucketlist, BucketlistItem, User
    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)


    @app.route('/auth/register', methods=['POST', 'GET'])
    def new_user():
        user = User.query.filter_by(email=request.data['email']).first()
        if not user:
            try:
                post_data = request.data
                email = post_data['email']
                password = post_data['password']
                match = re.search(r'[\w.-]+@[\w.-]+.\w+', email)
                if email is None or password is None:
                    response = {'message': 'Invalid input. Check the email and password'}
                    return jsonify(response)
                if match:
                    user = User(email=email)
                    user.hash_password(password)
                    db.session.add(user)
                    db.session.commit()
                    return jsonify({'message':'User registration was succesful', 'email': user.email})
                else:
                    response = {'message': 'Invalid email provided.'}
                    return jsonify(response)
            except Exception as e:
                response = {
                    'message': str(e)
                    }
                return response
        else:
            response = {'message': 'User already exists. Please login.'}
            return response


    @app.route('/auth/login', methods=['POST', 'GET'])
    def login():
        user = User.query.filter_by(email=request.data['email']).first()
        try:
            if user and user.verify_password(request.data['password']):
                access_token = user.generate_token(user.id)
                if access_token:
                    response = jsonify({
                        'message': 'You logged in successfully.',
                        'access_token': access_token.decode()
                    })
                    return response
            else:
                response = jsonify({
                    'message': 'Invalid email or password, Please try again.'
                })
                return response
        except ValueError:
            response = jsonify({'error': 'Error!!'})
            return response


    @app.route('/bucketlist/', methods=['GET'])
    def buckelist_get():
        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                q = request.args.get('q')
                limit = request.args.get('limit')
                page = request.args.get('page')
                if q:
                    try:
                        bucketlists = Bucketlist.query.filter_by(name=q, user_id=user.id).one()
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
                    except:
                        response = jsonify({'message': 'item not found'})
                        response.status_code = 404
                        return response
                else:
                    bucketlists = Bucketlist.get_bucketlist(user_id)
                    results = []
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
                            'item id':bucketlist.bucketlist_id,
                            'name': bucketlist.name,
                            'items':bucketlistresults,
                            'date_created': bucketlist.date_created,
                            'date_modified': bucketlist.date_modified,
                            'Created By' : user_id,
                            }
                        results.append(obj)
                    response = jsonify(results)
                    response.status_code = 200
                    return response
            else:
                response = jsonify({'message': 'Invalid token or expired'})
                response.status_code = 401
                return response
        else:
            response = jsonify({'message': 'Invalid token or expired'})
            response.status_code = 401
            return response


    @app.route('/bucketlist/', methods=['POST'])
    def bucketlists_post():
        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                user = User.query.filter_by(id=user_id).first()
                user_buckelists_list = []
                user_buckelists = Bucketlist.query.filter_by(user_id=user_id).all()
                for user_buckelist in user_buckelists:
                    user_buckelists_list.append(user_buckelist)
                user_bucketlist_id = len(user_buckelists_list)+1
                if request.method == "POST":
                    name = str(request.data.get('name', ''))
                    if name:
                        items = Bucketlist.query.filter_by(user_id=user_id).all()
                        items_list = []
                        for item in items:
                            items_list.append(item.name)
                        if name in items_list:
                            response = jsonify({'message': 'The bucketlist already exists'})
                            response.status_code = 400
                            return response
                        else:
                            bucketlist = Bucketlist(bucketlist_id=user_bucketlist_id,
                                                    name=name, user_id=user.id)
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
                response = jsonify({'message': 'Invalid token'})
                response.status_code = 401
                return response


    @app.route('/bucketlist/', methods=['PUT', 'DELETE'])
    def bucketlists_main_manupilate():
        response = jsonify({
            'message': 'Invalid Method for this link'
            })
        return response


    @app.route('/bucketlist/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def bucketlist_manipulation(id):
        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user_id).first()
                if not bucketlist:
                    response = jsonify({'message': 'Bucketlist does not exist'})
                    response.status_code = 404
                    return response
                if request.method == 'DELETE':
                    bucketlistsitems = BucketlistItem.get_items(bucketlist.id)
                    all_user_bucketlists = Bucketlist.get_bucketlist(user_id)
                    for bucketlist_item in all_user_bucketlists:
                        if bucketlist_item.bucketlist_id > id:
                            bucketlist_item.rearange(bucketlist_item.id)
                    for item in bucketlistsitems:
                        item.delete()
                    bucketlist.delete()
                    response = jsonify({
                        "message": "bucketlist eleted successfully"})
                    response.status_code = 200
                    return response
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
            else:
                response = jsonify({'message': 'Invalid token'})
                response.status_code = 401
                return response


    @app.route('/bucketlist/<int:id>/items/', methods=['POST'])
    def bucketlistsitem_post(id):

        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                try:
                    user_bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user_id).one()
                    if not user_bucketlist:
                        response = jsonify({'message': 'Bucket list doe not exist'})
                        response.status_code = 404
                        return response
                    item_buckelists = BucketlistItem.query.filter_by(bucketlist_id=user_bucketlist.id).all()
                    items_in_bucketlist = []
                    item_list = []
                    for i in item_buckelists:
                        item_list.append(i)
                        items_in_bucketlist.append(i.name)
                    item_bucket_list_id = len(item_list)+1
                    if not user_bucketlist:
                        # Raise an HTTPException with a 404 not found status code
                        response = jsonify({'message': 'Bucketlist does not exist'})
                        response.status_code = 404
                        return response
                    else:
                        name = str(request.data.get('name', ''))
                        if name:
                            if name in items_in_bucketlist:
                                response = jsonify({'message': 'Item already exists in this bucketlist'})
                                response.status_code = 400
                                return response
                            else:
                                bucketlistitem = BucketlistItem(name=name,
                                                                item_id=item_bucket_list_id,
                                                                bucketlist_id=user_bucketlist.id)
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
                            response = jsonify({'message': 'Invalid Entry'})
                            response.status_code = 404
                            return response
                except:
                    response = jsonify({'message': 'Bucketlist does not exist'})
                    response.status_code = 404
                    return response

            else:
                response = jsonify({'message': 'Invalid token'})
                response.status_code = 401
                return response


    @app.route('/bucketlist/<int:id>/items/', methods=['GET'])
    def bucketlistsitem_get(id):

        auth_header = request.headers.get('Authorization')
        access_token = auth_header

        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                try:
                    user_bucketlist = Bucketlist.query.filter_by(bucketlist_id=id,
                                                                 user_id=user_id).one()
                    if not user_bucketlist:
                        # Raise an HTTPException with a 404 not found status code
                        response = jsonify({'message': 'Bucketlist does not exist'})
                        response.status_code = 404
                        return response
                    else:
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
                except:
                    response = jsonify({'message': 'Bucketlist does not exist'})
                    response.status_code = 404
                    return response
            else:
                response = jsonify({'message': 'Invalid token'})
                response.status_code = 401
                return response


    @app.route('/bucketlist/<int:id>/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
    def bucketlistitems_manipulation(id, item_id,  **kwargs):
        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user_id).first()
                if not bucketlist:
                    response = jsonify({'message': 'Bucketlist does not exist'})
                    response.status_code = 404
                    return response
                bucketlistitem = BucketlistItem.query.filter_by(bucketlist_id=bucketlist.id, item_id=item_id).first()
                if not bucketlistitem:
                    response = jsonify({'message': 'Bucketlist item does not exist'})
                    response.status_code = 404
                    return response
                if request.method == 'DELETE':
                    user_bucketlistitems = BucketlistItem.query.filter_by(bucketlist_id=bucketlist.id).all()
                    for bucketlist_item in user_bucketlistitems:
                        if bucketlist_item.item_id > item_id:
                            bucketlist_item.rearange(bucketlist_item.id)
                    bucketlistitem.delete()
                    return {
                        "message": "bucketlist item deleted successfully"
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
            else:
                response = jsonify({'message': 'Invalid token'})
                response.status_code = 401
                return response

    # @app.route('/bucketlist/', methods=['POST', 'GET'])
    # @auth.login_required
    # def bucketlists():

    #     if access_token:
    #         user_id = User.decode_token(access_token)
    #         if not isinstance(user_id, str):

    #             user = User.query.filter_by(id = user_id).first()
    #             user_buckelists_list = []
    #             user_buckelists = Bucketlist.query.filter_by(user_id = user.id).all()
        

    #             for user_buckelist in user_buckelists:
    #                 user_buckelists_list.append(user_buckelist)

    #             user_bucketlist_id = len(user_buckelists_list)+1

    #             if request.method == "POST":
    #                 name = str(request.data.get('name', ''))
    #                 if name:
    #                     bucketlist = Bucketlist(bucketlist_id=user_bucketlist_id, name=name, user_id=user.id)
    #                     bucketlist.save()
    #                     response = jsonify({
    #                         'id': bucketlist.id,
    #                         'bucketlist id':bucketlist.bucketlist_id,
    #                         'name': bucketlist.name,
    #                         'date_created': bucketlist.date_created,
    #                         'date_modified': bucketlist.date_modified,
    #                         })
    #                     response.status_code = 201
    #                     return response
    #             else:
    #                 # GET
    #                 q = request.args.get('q')
    #                 limit = request.args.get('limit')
    #                 page = request.args.get('page')
    #                 if q:
    #                     bucketlists = Bucketlist.query.filter_by(name=q, user_id=user.id)
    #                     results = []

    #                     for bucketlist in bucketlists:
    #                         obj = {
    #                             'id': bucketlist.id,
    #                             'bucketlist id':bucketlist.bucketlist_id,
    #                             'name': bucketlist.name,
    #                             'date_created': bucketlist.date_created,
    #                             'date_modified': bucketlist.date_modified,
    #                             'User id': g.user.email,
    #                             }
    #                         results.append(obj)
    #                     response = jsonify(results)
    #                     response.status_code = 200
    #                     return response

    #                 elif limit:
    #                     bucketlists = Bucketlist.query.filter_by(name=q, user_id=user.id)
    #                     results = []

    #                     for bucketlist in bucketlists:
    #                         obj = {
    #                             'id': bucketlist.id,
    #                             'bucketlist id':bucketlist.bucketlist_id,
    #                             'name': bucketlist.name,
    #                             'date_created': bucketlist.date_created,
    #                             'date_modified': bucketlist.date_modified,
    #                             'User id' : g.user.email,
    #                             }
    #                         results.append(obj)
    #                     if page:
    #                         if page.isdigit():
    #                             old_page = page - 1
    #                             old_limit = old_page * limit
    #                             next_limit = page * limit
    #                             if len(results) > next_limit:
    #                                 new_page = results[old_limit:next_limit]
    #                                 response = jsonify(new_page)
    #                                 response.status_code = 200
    #                                 return response
    #                             elif len(results) > old_limit and len(results) < next_limit:
    #                                 new_page = results[old_limit:]
    #                                 response = jsonify(new_page)
    #                                 response.status_code = 200
    #                                 return response
    #                             else:
    #                                 return 404
    #                         else:
    #                             return 404


    #                 else:
    #                     bucketlists = Bucketlist.get_bucketlist(user.id)
    #                     results = []
    #                     limit = 20

    #                     for bucketlist in bucketlists:
    #                         bucketlistresults = []
    #                         bucketlistsitems = BucketlistItem.get_items(bucketlist.id)
    #                         for bucketlistitem in bucketlistsitems:
    #                             obj = {
    #                                 'id': bucketlistitem.id,
    #                                 'name': bucketlistitem.name,
    #                                 'bucketlist' : bucketlistitem.bucketlist_id
    #                                 }
    #                             bucketlistresults.append(obj)
    #                         obj = {
    #                             'item id':bucketlist.bucketlist_id,
    #                             'name': bucketlist.name,
    #                             'items':bucketlistresults,
    #                             'date_created': bucketlist.date_created,
    #                             'date_modified': bucketlist.date_modified,
    #                             'Created By' : g.user.email,
    #                             }
    #                         results.append(obj)
    #                     if page:
    #                         if page.isdigit():
    #                             old_page = int(page) - 1
    #                             old_limit = old_page * limit
    #                             next_limit = int(page) * limit
    #                             if len(results) > next_limit:
    #                                 new_page = results[old_limit:next_limit]
    #                                 response = jsonify(new_page)
    #                                 response.status_code = 200
    #                                 return response
    #                             elif len(results) > old_limit and len(results) < next_limit:
    #                                 new_page = results[old_limit:]
    #                                 response = jsonify(new_page)
    #                                 response.status_code = 200
    #                                 return response
    #                             else:
    #                                 return 404
    #                         else:
    #                             return 404
    #                     else:
    #                         this_page = results[:limit]
    #                         response = jsonify(this_page)
    #                         response.status_code = 200
    #                         return response




    return app