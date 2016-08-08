'''
primary file with app logic
'''

import os
import re
import json
import pysmap
import pymongo
import humanize

import smappboard.models
import smappboard.views

from flask import g, abort, redirect, url_for, request, Flask, render_template, jsonify
from flask_bootstrap import Bootstrap 

from datetime import datetime, timedelta
from bson.json_util import dumps

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])

from smappboard.models import filter_criterion, permission, post_filter, tweet

@app.route('/')
def main_page():
    return render_template('smappboard.html')

@app.route('/datasets', methods=['GET'])
def datasets_list():
    # get db names from mongo
    mongo = pymongo.MongoClient(app.config['SMAPPBOARD_MONGO_HOST'], int(app.config['SMAPPBOARD_MONGO_PORT']))
    db_names = [db_name for i, db_name in enumerate(mongo.database_names()) if db_name not in app.config['IGNORE_DBS']]
    return render_template('datasets.html', datasets=db_names)

@app.route('/dataset/<string:data_set_name>', methods=['GET'])
def single_dataset(data_set_name):
    mongo = pymongo.MongoClient(app.config['SMAPPBOARD_MONGO_HOST'], int(app.config['SMAPPBOARD_MONGO_PORT']))
    db_size = mongo[data_set_name].command("dbstats")
    db_size_gb = humanize.naturalsize(int(db_size['dataSize']))

    metadata = mongo[data_set_name]['metadata'].find_one({})
    data_type = metadata['data_type'] if metadata else 'tweets'
    dataset_platform = metadata['platform'] if metadata else 'twitter'
    filter_list = [{"filter_type": filt['filter_type'], "filter":filt['value']} for filt in mongo[data_set_name]['tweets_filter_criteria'].find({})]
    # if new format  does not work
    # check for old format
    if len(filter_list) == 0:
        filter_list = [{"filter_type": filt['filter_type'], "filter":filt['value']} for filt in mongo[data_set_name]['tweets_filter_criteria'].find({})]

    pysmap_dataset = pysmap.SmappDataset(['mongo', app.config['SMAPPBOARD_MONGO_HOST'], app.config['SMAPPBOARD_MONGO_PORT'], app.config['MONGO_READONLY_USER'], app.config['MONGO_READONLY_PASS'], data_set_name], collection_regex='(^data$|^tweets$|^tweets_\d+$)')
    num_tweets = sum([smappdragon_col.mongo_collection.count() for smappdragon_col in pysmap_dataset.collections])   
    return render_template('dataset.html', dataset_name=data_set_name, dataset_size=db_size_gb, dataset_platform=dataset_platform, data_type=data_type, num_tweets=num_tweets, filter_list=filter_list)

@app.route('/access/<string:data_set_name>')
def dataset_dashboard(data_set_name):
    return data_set_name

@app.route('/samples')
def get_samples():
    # get db names from mongo
    mongo = pymongo.MongoClient(app.config['SMAPPBOARD_MONGO_HOST'], int(app.config['SMAPPBOARD_MONGO_PORT']))
    db_names = [db_name for i, db_name in enumerate(mongo.database_names()) if db_name not in app.config['IGNORE_DBS']]
    return render_template('samples.html', datasets=db_names)

@app.route('/sample/<string:data_set_name>')
def get_sample_for_dataset(data_set_name):
    pysmap_dataset = pysmap.SmappDataset(['mongo', app.config['SMAPPBOARD_MONGO_HOST'], app.config['SMAPPBOARD_MONGO_PORT'], app.config['MONGO_READONLY_USER'], app.config['MONGO_READONLY_PASS'], data_set_name], collection_regex='(^data$|^tweets$|^tweets_\d+$)')
    tweet_sample = []
    for tweet in pysmap_dataset.limit_number_of_tweets(50):
        tweet_sample.append(dumps(tweet, sort_keys=True, indent=4, separators=(',', ': ')))
    return render_template('sample.html', tweet_sample=tweet_sample, dataset_name=data_set_name)

if __name__ == '__main__':
    app.run()