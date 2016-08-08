'''
primary file with app logic
'''

import os
import re
import pysmap
import pymongo
import humanize

import smappboard.models
import smappboard.views

from flask import g, abort, redirect, url_for, request, Flask, render_template, jsonify
from flask_bootstrap import Bootstrap 

from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

from smappboard.models import filter_criterion, permission, post_filter, tweet

@app.route('/')
def main_page():
    return render_template('smappboard.html')

@app.route('/datasets', methods=['GET'])
def datasets_list():
    # get db names from mongo
    mongo = pymongo.MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
    db_names = [db_name for i, db_name in enumerate(mongo.database_names()) if db_name not in app.config['IGNORE_DBS']]
    return render_template('datasets.html', datasets=db_names)

@app.route('/dataset/<string:data_set_name>', methods=['GET'])
def single_dataset(data_set_name):
    mongo = pymongo.MongoClient(app.config['MONGO_HOST'], app.config['MONGO_PORT'])
    db_size = mongo[data_set_name].command("dbstats")
    db_size_gb = humanize.naturalsize(int(db_size['dataSize']))
    metadata = mongo[data_set_name]['metadata'].find_one({})
    data_type = metadata['data_type'] if metadata else 'tweets'
    dataset_platform = metadata['platform'] if metadata else 'twitter'
    pysmap_dataset = pysmap.SmappDataset(['mongo', app.config['MONGO_HOST'], app.config['MONGO_PORT'], app.config['MONGO_READONLY_USER'], app.config['MONGO_READONLY_PASS'], data_set_name], collection_regex='(^data$|^tweets$|^tweets_\d+$)')
    num_tweets = sum([smappdragon_col.mongo_collection.count() for smappdragon_col in pysmap_dataset.collections])   
    return render_template('dataset.html', dataset_name=data_set_name, dataset_size=db_size_gb, dataset_platform=dataset_platform, data_type=data_type, num_tweets=num_tweets)

# a password protected page 
@app.route('/access/<string:data_set_name>')
def dataset_dashboard(data_set_name):
    return data_set_name

@app.route('/samples')
def get_samples():
    return datasets_list()

@app.route('/sample/<string:data_set_name>')
def get_sample_for_dataset(data_set_name):
    pysmap_dataset = pysmap.SmappDataset(['mongo', app.config['MONGO_HOST'], app.config['MONGO_PORT'], app.config['MONGO_READONLY_USER'], app.config['MONGO_READONLY_PASS'], data_set_name], collection_regex='(^data$|^tweets$|^tweets_\d+$)')

if __name__ == '__main__':
    app.run()