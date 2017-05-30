import os
from flask import Flask, abort, request, jsonify, url_for
from app.app import db, create_app
import jwt
from flask import current_app
from datetime import datetime, timedelta
from passlib.apps import custom_app_context as pwd_context

class Bucketlist(db.Model):
    '''
    This class represents the bucketlist table.
    '''

    __tablename__ = 'bucketlists'

    id = db.Column(db.Integer, primary_key=True)
    bucketlist_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime,
                              default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, name, user_id, bucketlist_id):
        '''
        initialize with name, user_id and backetlis_id
        '''
        self.name = name
        self.user_id = user_id
        self.bucketlist_id = bucketlist_id

    def save(self):
        '''
        Saving new bucketlist
        '''
        db.session.add(self)
        db.session.commit()

    def rearange(self, id):
        '''
        rearanging bucketlist after deletion
        '''
        item = Bucketlist.query.filter_by(id=id).one()
        item.bucketlist_id -= 1
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        '''
        retrieving all bucketlist
        '''
        return Bucketlist.query.all()

    def get_bucketlist(user_id):
        '''
        retrieving all bucketlist
        '''
        return Bucketlist.query.filter_by(user_id = user_id).all()


    def delete(self):
        '''
        deleting bucketlist
        '''
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<Bucketlist: {}>".format(self.name)


class BucketlistItem(db.Model):
    '''
    This class represents the bucketlist items table.
    '''

    __tablename__ = 'bucketlistsitems'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime,
                              default=db.func.current_timestamp(),
                              onupdate=db.func.current_timestamp())
    bucketlist_id = db.Column(db.Integer, db.ForeignKey('bucketlists.id'))

    def __init__(self, item_id, name, bucketlist_id):
        '''
        initialize with name.
        '''
        self.name = name
        self.bucketlist_id = bucketlist_id
        self.item_id = item_id

    def save(self):
        '''
        saving bucketlist item
        '''
        db.session.add(self)
        db.session.commit()

    def rearange(self, id):
        '''
        rearanging bucketlist item
        '''
        item = BucketlistItem.query.filter_by(id=id).one()
        item.item_id -= 1
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        '''
        retrieving bucketlist item
        '''
        return BucketlistItem.query.all()

    def get_items(bucketlist_id):
        '''
        getting bucketlist item
        '''
        return BucketlistItem.query.filter_by(bucketlist_id=bucketlist_id).all()

    def delete(self):
        '''
        deleting bucketlist item for a bucketlist
        '''
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<Bucketlistitem: {}>".format(self.name)


class User(db.Model):
    """This class defines the users table """

    __tablename__ = 'users'

    # Define the columns of the users table, starting with the primary key
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    bucketlists = db.relationship(
        'Bucketlist', order_by='Bucketlist.id', cascade="all, delete-orphan")

    def hash_password(self, entered_password):
        '''
        function for hashing a password
        '''
        self.password = pwd_context.encrypt(entered_password)

    def verify_password(self, entered_password):
        '''
        function for verifying a hashed a password
        '''
        return pwd_context.verify(entered_password, self.password)

    def generate_token(self, user_id):
        '''
        Generates the access token to be used as the Authorization header
        '''
        try:
            # set up a payload with an expiration time
            payload = {
                'exp': datetime.utcnow() + timedelta(minutes=10),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            # encode the payload to get an byte string token
            jwt_string = jwt.encode(
                payload,
                current_app.config.get('SECRET'),
                algorithm='HS256'
            )
            return jwt_string

        except Exception as e:
            # return an error in string format if an exception occurs
            return str(e)

    @staticmethod
    def decode_token(token):
        '''
        Decode the access token from the Authorization header
        '''
        try:
            payload = jwt.decode(token, current_app.config.get('SECRET'))
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return "Expired token. Please log in to get a new token"
        except jwt.InvalidTokenError:
            return "Invalid token. Please register or login"


   