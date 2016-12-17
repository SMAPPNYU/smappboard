import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = os.environ['FLASK_SECRET_KEY']
    SMAPPBOARD_TRENDS_CONSUMER_KEY = os.environ['SMAPPBOARD_TRENDS_CONSUMER_KEY']
    SMAPPBOARD_TRENDS_CONSUMER_SECRET = os.environ['SMAPPBOARD_TRENDS_CONSUMER_SECRET']
    SMAPPBOARD_TRENDS_ACCESS_TOKEN = os.environ['SMAPPBOARD_TRENDS_ACCESS_TOKEN']
    SMAPPBOARD_TRENDS_ACCESS_TOKEN_SECRET = os.environ['SMAPPBOARD_TRENDS_ACCESS_TOKEN_SECRET']
    SMAPPBOARD_CONSUMER_KEY = os.environ['SMAPPBOARD_CONSUMER_KEY']
    SMAPPBOARD_CONSUMER_SECRET = os.environ['SMAPPBOARD_CONSUMER_SECRET']
    PATH_TO_SMAPPBOARD_USERS = os.environ['PATH_TO_SMAPPBOARD_USERS']
    SMAPPBOARD_SSHFS_MOUNT_POINT = os.environ['SMAPPBOARD_SSHFS_MOUNT_POINT'] 
    
class ProductionConfig(Config):
    DEVELOPMENT = False
    DEBUG = False
    SMAPPBOARD_SSHFS_MOUNT_POINT = os.environ['SMAPPBOARD_SSHFS_MOUNT_POINT'] 

class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    IGNORE_DBS = ['admin', 'FilterCriteriaAdmin', 'test', 'config']
    SMAPPBOARD_SSHFS_MOUNT_POINT = os.environ['SMAPPBOARD_SSHFS_MOUNT_POINT'] 

class TestingConfig(Config):
    TESTING = True
    SMAPPBOARD_SSHFS_MOUNT_POINT = os.environ['SMAPPBOARD_SSHFS_MOUNT_POINT'] 

'''
    author @yvan
    configuration file for flask
    put sensitive info in instance/config.py
    read https://exploreflask.com/configuration.html
    read http://flask.pocoo.org/docs/0.10/config/
'''