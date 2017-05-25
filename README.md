# CP2BucketList
# Bucketlist API

Description

This is an Bucketliast API application.

Requirements

Python 3.6
postgresql9.6
postman

# Installation

1)Clone the repo from GitHub:

git clone https://github.com/nzaujk/Bucketlist-API.git

2) Create a virtual environment and install the necessary packages with:

3) cd to the root of the api

cd CP2BucketList
In the command promt run to get the enviroment configurations
4) source .env

$ pip install -r requirements.txt
Launching the program

# Create a database

$ python manage.py createdb

Make migrations
$ python manage.py db init
$ python manage.py db migrate
$ python manage.py db upgrade

# Runserver and add the endpoints to postman

$ python manage.py runserver

# Endpoints
| Endpoints  | Request | command |
| ------------- | ------------- | ------------- |
| `/api/v1/auth/register`                    |`POST` | Register a new user|
|  `/api/v1/auth/login`                      |`POST` | Login and retrieve token|
| `/api/v1/bucketlist/`                      |`POST` | Create a new Bucketlist |
| `/api/v1/bucketlist/`                      | `GET` | Retrieve all bucketlists for user |
| `/api/v1/bucketlist?limit=2&page=1`        | `GET` | Retrieve one bucketlist per page |
| `/api/v1/bucketlist/<id>/`                 | `GET` |  Retrieve bucket list details |
| `/api/v1/bucketlist/<id>/`                 | `PUT` | Update bucket list details |
| `/api/v1/bucketlist/<id>/`                 | `DELETE` | Delete a bucket list |
| `/api/v1/bucketlist/<id>/items/`           | `POST` |  Create items in a bucket list |
| `/api/v1/bucketlist/<id>/items/<item_id>/` | `DELETE`| Delete a item in a bucket list|
| `/api/v1/bucketlist/<id>/items/<item_id>/` | `PUT`| update a bucket list item details|


# Running the tests

 $ nosetests
