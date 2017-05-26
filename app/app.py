import json
import re
from flask_api import FlaskAPI, status
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify, abort, make_response, g, url_for, session
from instance.config import app_config
from passlib.apps import custom_app_context as pwd_context
from validate_email import validate_email

db = SQLAlchemy()


def create_app(config_name):
    '''
    Wraps the creation of a new Flask object, and returns it after it's loaded up
    with configuration settings using app.config and connected to the DB using
    '''
    from app.models import Bucketlist, BucketlistItem, User
    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)


    @app.route('/api/v1/auth/register', methods=['POST', 'GET'])
    def new_user():
        '''
        Function for registering user
        '''
        is_valid = validate_email(request.data['email'])
        if is_valid:
            user = User.query.filter_by(email=request.data['email']).first()
            if not user:
                try:
                    post_data = request.data
                    email = post_data['email']
                    password = post_data['password']
                    match = re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email)
                    if email is None or password is None:
                        response = {'message': 'Invalid input. Check the email and password'}
                        return jsonify(response)
                    if match:
                        user = User(email=email)
                        user.hash_password(password)
                        db.session.add(user)
                        db.session.commit()
                        return jsonify({'message':'User registration was succesful',
                                        'email': user.email})
                    else:
                        response = {'message': 'Invalid email input'}
                        return jsonify(response)
                except Exception as e:
                    response = {
                        'message': str(e)
                        }
                    return response
            else:
                response = {'message': 'User already exists. Please login.'}
                return response
        else:
            response = {'message': 'Invalid email'}
            return response


    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        '''
        Function for login user
        '''
        try:
            user = User.query.filter_by(email=request.data['email']).first()
            if user and user.verify_password(request.data['password']):
                access_token = user.generate_token(user.id)
                if access_token:
                    response = jsonify({
                        'message': 'You logged in successfully.',
                        'access_token': access_token.decode('ascii')
                    })
                    return response
            else:
                response = jsonify({
                    'message': 'Invalid email or password, Please try again.'
                })
                response.status_code = 401
                return response
        except:
            response = jsonify({'error': 'No email or password field!!'})
            response.status_code = 400
            return response


    @app.route('/api/v1/bucketlist/', methods=['GET'])
    def buckelist_get():
        '''
        Function for retrieving a users bucketlist
        '''
        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        current_limit = 0
        selected_page = 0
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                q = request.args.get('q')
                limit = request.args.get('limit')
                page = request.args.get('page')
                if limit:
                    if limit.isdigit():
                        current_limit = int(limit)
                    else:
                        response = jsonify({'message': 'Invalid limit'})
                        response.status_code = 400
                        return response
                else:
                    current_limit = 20
                if page:
                    if page.isdigit():
                        selected_page = int(page)
                    else:
                        response = jsonify({'message': 'Invalid page number'})
                        response.status_code = 400
                        return response
                else:
                    selected_page = 1
                if q:
                    # try:
                    bucketlists = Bucketlist.query.filter(Bucketlist.name.like(
                        '%{}%'.format(q))).filter_by(user_id=user_id).paginate(page=selected_page,
                                                                               per_page=current_limit,
                                                                               error_out=True)
                    results = []
                    for bucketlist in bucketlists.items:
                        obj = {
                            'bucketlist id':bucketlist.bucketlist_id,
                            'name': bucketlist.name,
                            'date_created': bucketlist.date_created,
                            'date_modified': bucketlist.date_modified,
                            'User id': user_id,
                            }
                        results.append(obj)
                    response = jsonify(results)
                    response.status_code = 200
                    return response

                bucketlists = Bucketlist.query.filter_by(user_id=user_id).paginate(page=selected_page,
                                                                                   per_page=current_limit,
                                                                                   error_out=True)
                results = []
                for bucketlist in bucketlists.items:
                    bucketlistresults = []
                    bucketlistsitems = BucketlistItem.get_items(bucketlist.id)
                    for bucketlistitem in bucketlistsitems:
                        obj = {
                            'id': bucketlistitem.id,
                            'item id': bucketlistitem.item_id,
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


    @app.route('/api/v1/bucketlist/', methods=['POST'])
    def bucketlists_post():
        '''
        Function for adding a users new bucketlist
        '''
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


    @app.route('/api/v1/bucketlist/', methods=['PUT', 'DELETE'])
    def bucketlists_main_modify():
        '''
        Function for catching unallowed methods for bucketlist
        '''
        response = jsonify({
            'message': 'Invalid Method for this link'
            })
        return response


    @app.route('/api/v1/bucketlist/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    def bucketlist_modify(id):
        '''
        Function for modifying a users bucketlist
        '''
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
                        "message": "bucketlist deleted successfully"})
                    response.status_code = 200
                    return response
                elif request.method == 'PUT':
                    name = str(request.data.get('name')) 
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


    @app.route('/api/v1/bucketlist/<int:id>/items/', methods=['POST'])
    def bucketlistsitem_post(id):
        '''
        Function for adding a users bucketlist item
        '''

        auth_header = request.headers.get('Authorization')
        access_token = auth_header
        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                try:
                    user_bucketlist = Bucketlist.query.filter_by(bucketlist_id=id, user_id=user_id).one()
                    if not user_bucketlist:
                        response = jsonify({'message': 'Bucket list does not exist'})
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
                        name = str(request.data.get('name'))
                        if name:
                            if name in items_in_bucketlist:
                                response = jsonify({'message': 'Item already exists in this bucketlist'})
                                response.status_code = 409
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


    @app.route('/api/v1/bucketlist/<int:id>/items/', methods=['GET'])
    def bucketlistsitem_get(id):
        '''
        Function for retireving a users bucketlist item
        '''

        auth_header = request.headers.get('Authorization')
        access_token = auth_header

        if access_token:
            user_id = User.decode_token(access_token)
            if not isinstance(user_id, str):
                try:
                    user_bucketlist = Bucketlist.query.filter_by(bucketlist_id=id,
                                                                 user_id=user_id).one()
                    if not user_bucketlist:
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


    @app.route('/api/v1/bucketlist/<int:id>/items/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
    def bucketlistitems_modify(id, item_id,  **kwargs):
        '''
        Function for modifying a users bucketlist item
        '''

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


    return app
