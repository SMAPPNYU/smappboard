import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ['FLASK_SECRET_KEY']
    MONGO_READONLY_USER = os.environ['SMAPPBOARD_MONGO_READONLY_USER']
    MONGO_READONLY_PASS = os.environ['SMAPPBOARD_MONGO_READONLY_PASS']
    
class ProductionConfig(Config):
    DEVELOPMENT = False
    DEBUG = False
    MONGO_HOST = 'localhost'
    MONGO_PORT = 49999

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    MONGO_HOST = os.environ['SMAPPBOARD_MONGO_HOST']
    MONGO_PORT = os.environ['MONGO_PORT']
    IGNORE_DBS = ['admin', 'FilterCriteriaAdmin', 'test', 'config']

class TestingConfig(Config):
    TESTING = True

'''
    author @yvan
    configuration file for flask
    put sensitive info in instance/config.py
    read https://exploreflask.com/configuration.html
    read http://flask.pocoo.org/docs/0.10/config/
'''