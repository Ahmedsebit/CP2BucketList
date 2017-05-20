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
        self.bucketlist = {'name': 'Go to Borabora for vacation'}
        with self.app.app_context():
            db.create_all()

    def test_post_bucketlist(self):
        '''
        Bucketlist (POST request) API functionality test. The test checks if the a new item can be
        created as a new bucketlist. The test returns 201 for succesful creation.
        '''
        new_entry = self.client().post('/bucketlist/', data=self.bucketlist)
        self.assertEqual(new_entry.status_code, 201)

    def test_post_bucketlist_unauth(self):
        '''
        Test for checking unauthorized user creating a main list called bucketlists. The function
        should return status [401].
        '''
        self.client().post('user/logout')
        item = {'name': 'Start a business'}
        new_entry = self.client().post('/bucketlist/', data=item)
        self.assertEqual(new_entry.status_code, 401)


    def test_post_bucketlist_existing(self):
        '''
        Test for unauthorized user creating an existing item that already exitsts. The function
        should return status [202] and a [item already exists] message.
        '''
        item = {'name': 'Learn Martial Arts'}
        first_entry = self.client().post('/bucketlist/', data=item)
        repeated_entry = self.client().post('/bucketlist/', data=item)
        self.assertEqual(repeated_entry.status_code, 404)


    def test_post_bucketlist_item(self):
        '''
        Test for authorized user posting a new items into bucketlists. The function should return
        status [201] and a [item has ben added] message.
        '''
        new_entry = self.client().post('/bucketlist/', data=self.bucketlist)
        item = {'name': 'Learn Jujitsu'}
        new_item_entry = self.client().post('/bucketlist/1/items/', data=item)
        self.assertEqual(new_item_entry.status_code, 201)


    def test_post_bucketlist_item_unauth(self):
        '''
        Test for unauthorized user posting a new item into bucketlists. The function should return
        status [401] and a [Unauthorized user] message.
        '''
        new_entry = self.client().post('/bucketlist/', data=self.bucketlist)
        item = {'name': 'Learn Karate'}
        self.client().post('user/logout')
        new_item_entry = self.client().post('/bucketlist/1/items/', data=item)
        self.assertEqual(new_item_entry.status_code, 401)


    def test_post_bucketlist_item_nonexistingbucketlist(self):
        '''
        Test for authorized user posting a new items into bucketlist which does not exist.
        The function should return status [404] and a [bucketlist does not exist] message.
        '''
        item = {'name': 'Learn Karate'}
        new_item = self.client().post('/bucketlist/143/items/', data=item)
        self.assertEqual(new_item.status_code, 404)


    def test_post_bucketlist_item_existing(self):
        '''
        Test for authorized user posting a existing items into bucketlists. The function should
        return status [202] and a [Item already exists] message.
        '''
        item = {'name': 'Learn Jujitsu'}
        self.client().post('/bucketlist/1/', data=item)
        new_item = self.client().post('/bucketlist/1/items/', data=item)
        self.assertEqual(new_item.status_code, 202)



    def test_get_bucketlists(self):
        '''
        Test API can get a bucketlist (GET request).
        '''
        res = self.client().post('/bucketlist/', data=self.bucketlist)
        self.assertEqual(res.status_code, 201)
        res = self.client().get('/bucketlist/')
        self.assertEqual(res.status_code, 200)

    def test_get_bucketlist_unauth(self):
        '''
        Test for unauthorized user getting main list bucketlists which has items. The
        function should return status |401| and a [Unathorized User] message.
        '''
        self.client().post('user/logout')
        results = self.client().get('/bucketlist/')
        self.assertEqual(results.status_code, 401)


    def test_get_bucketlist_item(self):
        """
        Bucketlist item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        new_item = {'name': 'Start Charity'}
        new_item_results = self.client().post('/bucketlist/', data=new_item)
        result = self.client().get('/bucketlist/1')
        self.assertEqual(result.status_code, 200)


    def test_get_bucketlist_item_unauth(self):
        """
        Bucketlist item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        new_item = {'name': 'Start Charity'}
        new_item_results = self.client().post('/bucketlist/', data=new_item)
        self.assertEqual(new_item_results.status_code, 201)
        self.client().post('user/logout')
        result = self.client().get('/bucketlist/1')
        self.assertEqual(result.status_code, 401)


    def test_get_bucketlist_item_notfound(self):
        """
        Bucketlist item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        new_item = {'name': 'Start Charity'}
        new_item_results = self.client().post('/bucketlists/', data=new_item)
        self.client().post('user/logout')
        result = self.client().get('/bucketlist/120')
        self.assertEqual(result.status_code, 404)


    def test_get_bucketlistitem_item(self):
        """
        Bucketlistitemitem item GET request API functionality test. The test checks if an item in
        the bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/items/', data=new_item)
        result = self.client().get('/bucketlist/1/items/1')
        self.assertEqual(result.status_code, 200)


    def test_get_bucketlistitem_item_unauth(self):
        """
        Bucketlistitem item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/items/', data=new_item)
        self.client().post('user/logout')
        result = self.client().get('/bucketlist/1/items/1')
        self.assertEqual(result.status_code, 401)


    def test_get_bucketlistitem_item_notfound(self):
        """
        Bucketlistitem item GET request API functionality test. The test checks if an item in the
        bucketlist can be retrieved by its id through the GET request. The test returns 200
        for succesful retrieveing.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/items/', data=new_item)
        result = self.client().get('/bucketlist/1/items/153')
        self.assertEqual(result.status_code, 404)


    def test_put_bucketlist(self):
        '''
        Test API can edit an existing bucketlist. (PUT request)
        '''
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/items/', data=new_item)
        edited_item = self.client().put('/bucketlist/1', data=new_item)
        self.assertEqual(edited_item.status_code, 200)


    def test_put_bucketlist_unauth(self):
        """
        Bucketlist item PUT request API functionality test. The test checks if an item in the
        bucketlist can be edited by its id through the PUT request. The test returns 200
        for succesful edited.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('user/logout')
        edited_item = self.client().put('/bucketlist/1', data=new_item)
        self.assertEqual(edited_item.status_code, 401)


    def test_put_bucketlist_notfound(self):
        """
        Bucketlist item PUT request API functionality test. The test checks if an item in the
        bucketlist can be edited by its id through the PUT request. The test returns 200
        for succesful edited.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        edited_item = self.client().put('/bucketlist/143', data=new_item)
        self.assertEqual(edited_item.status_code, 404)


    def test_put_bucketlist_item(self):
        """
        Bucketlistitem item PUT request API functionality test. The test checks if an item in the
        bucketlist can be edited by its id through the PUT request. The test returns 200
        for succesful edited.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/', data=new_item)
        self.client().post('/bucketlist/1/items/', data={"name": "Learn Self Defence"})
        edited_item = self.client().put('/bucketlist/1/items/1', data={"name": "Learn Kungfu"})
        self.assertEqual(edited_item.status_code, 200)


    def test_put_bucketlist_item_unauth(self):
        """
        Bucketlistitem item PUT request API functionality test. The test checks if an item in the
        bucketlist can be edited by its id through the PUT request. The test returns 200
        for succesful edited.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/', data=new_item)
        self.client().post('/bucketlist/1/items/', data={"name": "Learn Self Defence"})
        self.client().post('user/logout')
        edited_item = self.client().put('/bucketlist/1/items/1', data={"name": "Learn Kungfu"})
        self.assertEqual(edited_item.status_code, 401)


    def test_put_bucketlist_item_notfound(self):
        '''
        Test for authorized user updating a non-existing item into bucketlists item. The function should 
        return status [202] and a [Item does not exists] message.
        '''
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/', data=new_item)
        self.client().post('/bucketlist/1/items/', data={"name": "Learn Self Defence"})
        edited_item = self.client().put('/bucketlist/1/items/143', data={"name": "Learn Kungfu"})
        self.assertEqual(edited_item.status_code, 404)


    def test_put_bucketlist_item_bucketlistnotfound(self):
        """
        Bucketlistitem item PUT request API functionality test. The test checks if an item in the
        bucketlist can be edited by its id through the PUT request. The test returns 200
        for succesful edited.
        """
        new_bucketlist = {'name': 'Start Charity'}
        new_item = {'name': 'Open a foundation'}
        self.client().post('/bucketlist/', data=new_bucketlist)
        self.client().post('/bucketlist/1/', data=new_item)
        self.client().post('/bucketlist/1/items/', data={"name": "Learn Self Defence"})
        edited_item = self.client().put('/bucketlist/431/items/1', data={"name": "Learn Kungfu"})
        self.assertEqual(edited_item.status_code, 404)


    def test_delete_bucketlist(self):
        '''
        Test API can delete an existing bucketlist. (DELETE request).
        '''
        rv = self.client().post('/bucketlist/',data={'name': 'Eat, pray and love'})
        res = self.client().delete('/bucketlist/1')
        self.assertEqual(res.status_code, 200)


    def test_delete_bucketlist_unauth(self):
        '''
        Test for unauthorized user deleting main list bucketlists. The function should
        return status [401] and a [Unauthorized User] message.
        '''
        rv = self.client().post('/bucketlist/',data={'name': 'Eat, pray and love'})
        self.client().post('user/logout')
        res = self.client().delete('/bucketlist/1')
        self.assertEqual(res.status_code, 401)


    def test_delete_bucketlist_notfound(self):
        '''
        Test for authorized user deleting non existing main list bucketlists. The function
        should return status [401] and a [Unauthorized User] message.
        '''
        rv = self.client().post('/bucketlist/',data={'name': 'Eat, pray and love'})
        deleted_item = self.client().delete('/bucketlist/143')
        self.assertEqual(deleted_item.status_code, 404)


    def test_delete_bucketlistitem(self):
        '''
        Test for authorized user deleting main list bucketlists. The function should
        return status [200] and a [bucketList deleted] message.
        '''
        self.client().post('/bucketlist/',data={'name': 'Start Charity'})
        rv = self.client().post('/bucketlist/1/items/',data={'name': 'Start a foundation'})
        deleted_item = self.client().delete('/bucketlist/1/items/1')
        self.assertEqual(deleted_item.status_code, 200)


    def test_delete_bucketlistitem_unauth(self):
        '''
        Test for unauthorized user deleting main list bucketlists. The function should
        return status [401] and a [Unauthorized User] message.
        '''
        self.client().post('/bucketlist/',data={'name': 'Start Charity'})
        rv = self.client().post('/bucketlist/1/items/',data={'name': 'Start a foundation'})
        self.client().post('user/logout')
        deleted_item = self.client().delete('/bucketlist/1/items/1')
        self.assertEqual(deleted_item.status_code, 401)


    def test_delete_bucketlistitem_notfound(self):
        '''
        Test for authorized user deleting non existing main list bucketlists. The function
        should return status [401] and a [Unauthorized User] message.
        '''
        self.client().post('/bucketlist/',data={'name': 'Start Charity'})
        rv = self.client().post('/bucketlist/1/items/',data={'name': 'Start a foundation'})
        self.client().post('user/logout')
        deleted_item = self.client().delete('/bucketlist/1/items/143')
        self.assertEqual(deleted_item.status_code, 404)


    def test_delete_bucketlistitem_backetlistnotfound(self):
        '''
        Test for authorized user deleting non existing main list bucketlists. The function
        should return status [401] and a [Unauthorized User] message.
        '''
        self.client().post('/bucketlist/',data={'name': 'Start Charity'})
        rv = self.client().post('/bucketlist/1/items/',data={'name': 'Start a foundation'})
        self.client().post('user/logout')
        deleted_item = self.client().delete('/bucketlist/143/items/1')
        self.assertEqual(deleted_item.status_code, 404)


    def tearDown(self):
        """teardown all initialized variables."""
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()