import unittest
import json
from app import create_app, db


class AuthTestCase(unittest.TestCase):
    '''
    Test case for the authentication blueprint.
    '''

    def setUp(self):
        '''
        Set up test variables.
        '''
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.user_data = {'email': 'user@email.com','password': 'password'}

        with self.app.app_context():
            # create all tables
            db.session.close()
            db.drop_all()
            db.create_all()


    def test_user_registration(self):
        '''
        Test user registration works correcty.
        '''
        new_registration = self.client().post('/auth/register', data=self.user_data)
        self.assertEqual(new_registration.status_code, 201)


    def test_user_registration_existing_user(self):
        '''
        Test that a user cannot be registered twice.
        '''
        self.client().post('/auth/register', data=self.user_data)
        user_multiple_registration = self.client().post('/auth/register', data=self.user_data)
        self.assertEqual(user_multiple_registration.status_code, 202)


    def test_user_login(self):
        """Test registered user can login."""
        self.client().post('/auth/register', data=self.user_data)
        login_res= self.client().post('/auth/login', data=self.user_data)
        self.assertEqual(login_res.status_code, 200)


    def test_non_registered_user_login(self):
        """Test non registered users cannot login."""
        not_a_user = {'email': 'not_a_user@example.com','password': 'nope'}
        res = self.client().post('/api/token')
        self.assertEqual(res.status_code, 401)

    def test_no_password_registered_user_login(self):
        """Test registered user can login."""
        self.user_data = {'email': 'user@email.com','password': ''}
        self.client().post('/auth/register', data=self.user_data)
        login_res= self.client().post('/auth/login', data=self.user_data)
        self.assertEqual(login_res.status_code, 200)


    # def test_unsuccesfull_registrationemail(self):
    #     '''
    #     Test for checking for user registration with invalid email. Invalid email user registration
    #     should return status |202| and a |wromg email format| message.
    #     '''
    #     new_user = {'username':'', 'password':"testingpassword"}
    #     new_registration = self.client().post('/users/registration/', data=new_user)
    #     self.assertEqual(new_registration.status_code, 202)

    # def test_unsuccesfull_regpassword(self):
    #     '''
    #     Test for checking for user registration with invalid password. Invalid password user
    #     registration should return status |202| and a |wrong password format| message.
    #     '''
    #     new_user = {'username':'newuser@email.com', 'password':""}
    #     new_registration = self.client().post('/users/registration/', data=new_user)
    #     self.assertEqual(new_registration.status_code, 202)

    # def test_login_succesfull(self):
    #     '''
    #     Test for checking for succesfull user login. Succesfull login should return status |200|
    #     and a |login was succesfull| message.
    #     '''
    #     new_login = self.client().post('/users/login/', data=self.user)
    #     self.assertEqual(new_login.status_code, 200)


    # def test_login_unregistered_email(self):
    #     '''
    #     Test for checking for user login with non-existsing email. Non-existsing email user login
    #     should return status |202| and a |user does not exist| message.
    #     '''
    #     unregistered_user = {'username':'username@email.com', 'password':"testingpassword"}
    #     new_login = self.client().post('/users/login/', data=unregistered_user)
    #     self.assertEqual(new_login.status_code, 202)

    # def test_login_wrongpassword(self):
    #     '''
    #     Test for checking for user login with wrong password. Wrong password email user login should
    #     return status |202| and a |wrong password entered| message.
    #     '''
    #     user_credentials = {'username':'username@email.com', 'password':""}
    #     new_login = self.client().post('/users/login/', data=user_credentials)
    #     self.assertEqual(new_login.status_code, 202)