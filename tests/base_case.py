import unittest
import os
from flask import json, jsonify
from app.app import create_app, db

class BucketlistTestCase(unittest.TestCase):
    '''
    This class represents the bucketlist test case
    '''

    def setUp(self):
        '''
        Define test variables and initialize app.
        '''
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        with self.app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()
        


    def register_user(self, email="user@test.com", password="test1234"):
        user_data = {'email': email, 'password': password}
        return self.client().post('/api/v1/auth/register', data=user_data)


    def login_user(self, email="user@test.com", password="test1234"):
        user_data = {'email': email,'password': password}
        return self.client().post('/api/v1/auth/login', data=user_data)


    def post_bucketlist(self, name="new_item"):
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        self.auth_token = response_data['access_token']

        name = name
        return self.client().post('/api/v1/bucketlist/', data=json.dumps({"name": name}),
                                  content_type='application/json',
                                  headers={'Authorization': self.auth_token})

    def post_item_bucketlist(self, name="new_bucketlist_item"):
        self.post_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        self.auth_token = response_data['access_token']

        name = name
        return self.client().post('/api/v1/bucketlist/1/items/', data=json.dumps({"name": name}),
                                  content_type='application/json',
                                  headers={'Authorization': self.auth_token})

    def post_item_nonexistingbucketlist(self, name="new_bucketlist_item"):
        self.post_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        self.auth_token = response_data['access_token']

        name = name
        return self.client().post('/api/v1/bucketlist/2/items/', data=json.dumps({"name": name}),
                                  content_type='application/json',
                                  headers={'Authorization': self.auth_token})