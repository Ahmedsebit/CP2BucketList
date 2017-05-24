import unittest
import os
from flask import json, jsonify
from app import create_app, db

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


    def test_user_registration(self):
        '''
        Test user registration works correctly.
        '''
        user_multiple_registration = self.register_user()
        self.assertEqual(user_multiple_registration.status_code, 200)


    def test_user_registration_existing_user(self):
        '''
        Test that a user cannot be registered twice.
        '''
        self.register_user()
        user_data = {'email':"user@test.com", 'password':"test1234"}
        user_multiple_registration = self.client().post('/api/v1/auth/register',
                                                        data=json.dumps(user_data),
                                                        content_type='application/json')
        self.assertEqual(user_multiple_registration.status_code, 200)


    def test_user_login(self):
        '''
        Test registered user can login.
        '''
        login_res = self.login_user()
        self.assertEqual(login_res.status_code, 200)


    def test_non_registered_user_login(self):
        """Test non registered users cannot login."""
        not_a_user = {'email': 'not_a_user@example.com', 'password': 'nope'}
        self.register_user()
        res = self.client().post('/api/v1/auth/login', data=json.dumps(not_a_user))
        self.assertEqual(res.status_code, 401)


    def test_post_bucketlist(self):
        '''
        Bucketlist (POST request) API functionality test. The test checks if the a new item can be
        created as a new bucketlist. The test returns 201 for succesful creation.
        '''
        post_response = self.client().post('/api/v1/bucketlist/',
                                           data=json.dumps({"name": "new stuff"}),
                                           content_type='application/json',
                                           headers={'Authorization': self.auth_token})
        self.assertEqual(post_response.status_code, 201)


    def test_post_bucketlist_unauth(self):
        '''
        Test for checking unauthorized user creating a main list called bucketlists. The function
        should return status [401].
        '''
        item = {'name': 'Start a business'}
        new_entry = self.client().post('/api/v1/bucketlist/',
                                       data=item,
                                       content_type='application/json',
                                       headers={'Authorization': 'self.auth_token'})
        self.assertEqual(new_entry.status_code, 401)


    def test_post_bucketlist_existing(self):
        '''
        Test for unauthorized user creating an existing item that already exitsts. The function
        should return status [400] and a [item already exists] message.
        '''
        self.post_bucketlist()
        response = self.post_bucketlist()
        self.assertEqual(response.status_code, 400)


    def test_post_bucketlist_item(self):
        '''
        Test for authorized user posting a new items into bucketlists. The function should return
        status [201] and a [item has ben added] message.
        '''
        response = self.post_item_bucketlist()
        self.assertEqual(response.status_code, 201)


    def test_post_bucketlist_item_unauthorised(self):
        '''
        Test for unauthorized user posting a new item into bucketlists. The function should return
        status [401] and a [Unauthorized user] message.
        '''
        name = 'item'
        response = self.client().post('/api/v1/bucketlist/1/items/', data=json.dumps({"name": name}),
                                      content_type='application/json',
                                      headers={'Authorization': 'self.auth_token'})
        self.assertEqual(response.status_code, 401)



    def test_post_bucketlist_item_nonexistingbucketlist(self):
        '''
        Test for authorized user posting a new items into bucketlist which does not exist.
        The function should return status [404] and a [bucketlist does not exist] message.
        '''
        response = self.post_item_nonexistingbucketlist()
        self.assertEqual(response.status_code, 404)


    def test_post_bucketlist_item_existing(self):
        '''
        Test for authorized user posting a existing items into bucketlists. The function should
        return status [202] and a [Item already exists] message.
        '''
        self.post_item_bucketlist()
        response = self.post_item_bucketlist()
        self.assertEqual(response.status_code, 400)


    def test_get_bucketlists(self):
        '''
        Test API can get a bucketlist (GET request).
        '''
        self.post_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        response = self.client().get('/api/v1/bucketlist/',
                                     content_type='application/json',
                                     headers={'Authorization': auth_token})
        self.assertEqual(response.status_code, 200)


    def test_get_bucketlist_unauth(self):
        '''
        Test for unauthorized user getting main list bucketlists which has items. The
        function should return status |401| and a [Unathorized User] message.
        '''
        results = self.client().get('/api/v1/bucketlist/',
                                    content_type='application/json',
                                    headers={'Authorization': 'auth_token'})
        self.assertEqual(results.status_code, 401)


    def test_get_bucketlist_item(self):
        """
        Bucketlist item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/1',
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_get_bucketlist_item_unauth(self):
        """
        Bucketlist item unauth GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 401
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/1',
                                   content_type='application/json',
                                   headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_get_bucketlist_item_notfound(self):
        """
        Bucketlist item not found GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 404
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/56',
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_get_bucketlistitem_item(self):
        """
        Bucketlist item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/1/items/1',
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_get_bucketlistitem_item_unauthorised(self):
        """
        Bucketlist unauth item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 401
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/1/items/1',
                                   content_type='application/json',
                                   headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_get_bucketlistitem_item_notfound(self):
        """
        Bucketlist item not found GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 404.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/1/items/21',
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)

    def test_get_bucketlistitem_item_bucketlistnotfound(self):
        """
        Bucketlist not found item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 404
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/13/items/1',
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_put_bucketlist(self):
        """
        Bucketlist item PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the PUT request. The test returns 200
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/1',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_put_bucketlist_unauth(self):
        """
        Bucketlist unauth PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the PUT request. The test returns 401
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/1',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_put_bucketlist_notfound(self):
        """
        Bucketlist not found PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 404
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/5',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_put_bucketlist_item(self):
        """
        Bucketlist item PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the PUT request. The test returns 200
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/1/items/1',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_put_bucketlist_item_unauth(self):
        """
        Bucketlist unauth item PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the PUT request. The test returns 200
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/1/items/1',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_put_bucketlist_item_notfound(self):
        """
        Bucketlist item not found PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the PUT request. The test returns 200
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/1/items/3',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_put_bucketlist_item_bucketlistnotfound(self):
        """
        Bucketlist not found item PUT request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns PUT
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().put('/api/v1/bucketlist/3/items/1',
                                   data=json.dumps({"name": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_delete_bucketlist(self):
        """
        Bucketlist DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 200
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/1',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_delete_bucketlist_unauth(self):
        """
        Bucketlist DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 401
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/1',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_delete_bucketlist_notfound(self):
        """
        Bucketlist not found DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 404
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/3',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_delete_bucketlist_item(self):
        """
        Bucketlist item DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 200
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/1/items/1',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_delete_bucketlist_item_unauth(self):
        """
        Bucketlist unauth item DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 401
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/1/items/1',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_delete_bucketlist_item_notfound(self):
        """
        Bucketlist item not found DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 404
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/1/items/5',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_delete_bucketlist_item_backetlistnotfound(self):
        """
        Bucketlist not found item DELETE request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the DELETE request. The test returns 404
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/45/items/1',
                                      data=json.dumps({"q": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)


    def test_find_bucketlist(self):
        """
        Bucketlist FIND request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/',
                                   data=json.dumps({"q": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 200)


    def test_find_bucketlist_unauth(self):
        """
        Bucketlist item unauth FIND request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 401
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().get('/api/v1/bucketlist/',
                                   data=json.dumps({"q": edited_item}),
                                   content_type='application/json',
                                   headers={'Authorization': 'auth_token'})
        self.assertEqual(result.status_code, 401)


    def test_find_bucketlist_notfound(self):
        """
        Bucketlist item not found FIND request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        self.post_bucketlist()
        self.post_item_bucketlist()
        self.register_user()
        edited_item = 'edited item'
        response = self.login_user()
        response_data = json.loads(response.data.decode())
        auth_token = response_data['access_token']
        result = self.client().delete('/api/v1/bucketlist/3',
                                      data=json.dumps({"name": edited_item}),
                                      content_type='application/json',
                                      headers={'Authorization': auth_token})
        self.assertEqual(result.status_code, 404)




    def tearDown(self):
        """teardown all initialized variables."""
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
