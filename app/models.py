import os
from flask import Flask, abort, request, jsonify, g, url_for
from app import db, create_app
from flask_bcrypt import Bcrypt
import jwt
from flask import current_app
from datetime import datetime, timedelta
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)

class Bucketlist(db.Model):
    """This class represents the bucketlist table."""

    __tablename__ = 'bucketlists'

    id = db.Column(db.Integer, primary_key=True)
    bucketlist_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),onupdate=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, name, user_id, bucketlist_id):
        """initialize with name."""
        self.name = name
        self.user_id = user_id
        self.bucketlist_id = bucketlist_id

    def save(self):
        db.session.add(self)
        db.session.commit()

    def rearange(self, id):
        item = Bucketlist.query.filter_by(id=id).one()
        item.bucketlist_id -=1
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Bucketlist.query.all()

    def get_bucketlist(user_id):
        return Bucketlist.query.filter_by(user_id = user_id).all()


    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "<Bucketlist: {}>".format(self.name)


class BucketlistItem(db.Model):
    """This class represents the bucketlist items table."""

    __tablename__ = 'bucketlistsitems'

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(),onupdate=db.func.current_timestamp())
    bucketlist_id = db.Column(db.Integer, db.ForeignKey('bucketlists.id'))

    def __init__(self, item_id, name, bucketlist_id):
        """initialize with name."""
        self.name = name
        self.bucketlist_id = bucketlist_id
        self.item_id = item_id

    def save(self):
        db.session.add(self)
        db.session.commit()

    def rearange(self, id):
        item = BucketlistItem.query.filter_by(id=id).one()
        item.item_id -=1
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return BucketlistItem.query.all()

    def get_items(bucketlist_id ):
        return BucketlistItem.query.filter_by(bucketlist_id = bucketlist_id).all()

    def delete(self):
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
        self.password = pwd_context.encrypt(entered_password)

    def verify_password(self, entered_password):
        return pwd_context.verify(entered_password, self.password)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(os.getenv('SECRET'), expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        SECRET = os.getenv('SECRET')
        s = Serializer(SECRET)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user

    def password_is_valid(self, password):
        """
        Checks the password against it's hash to validates the user's password
        """
        return Bcrypt().check_password_hash(self.password, password)

    def generate_token(self, user_id):
        """Generates the access token to be used as the Authorization header"""
        try:
            # set up a payload with an expiration time
            payload = {
                'exp': datetime.utcnow() + timedelta(minutes=5),
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
        """Decode the access token from the Authorization header."""
        try:
            payload = jwt.decode(token, current_app.config.get('SECRET'))
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return "Expired token. Please log in to get a new token"
        except jwt.InvalidTokenError:
            return "Invalid token. Please register or login"


   