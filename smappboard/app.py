'''
primary file with app logic
'''

import os
import re
import ast
import json
import locale
import tweepy
import pysmap
import pymongo
import humanize

from functools import wraps
from datetime import datetime, timedelta
from bson.json_util import dumps

import smappboard.models
import smappboard.views

from flask import g, session, abort, redirect, url_for, request, Flask, render_template, jsonify, flash
from flask_oauthlib.client import OAuth
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
oauth = OAuth(app)

# create a twitter api interface
twitter = oauth.remote_app(
    'twitter',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key=app.config['SMAPPBOARD_CONSUMER_KEY'],
    consumer_secret=app.config['SMAPPBOARD_CONSUMER_SECRET']
)

from smappboard.models import filter_criterion, permission, post_filter, tweet

#decorator for a function to only allow people who have logged into twitter
def twitter_logged_in(func):
    @wraps(func)

    def not_authorized_func():
        return render_template('error.html', error={'message': 'you are not an authorized user', 'code': 403, 'response_code': 403})

    def wrapper(*args, **kwargs):
        with open(app.config['PATH_TO_SMAPPBOARD_USERS']) as file:
            authed_users_list = json.load(file)
            print(authed_users_list)
            if current_user() in authed_users_list:
                return func(*args, **kwargs)
            else:
                return not_authorized_func()
    return wrapper

# the base route
@app.route('/')
def main_page():
    if session.get('twitter_token'):
        should_show_twitter_login = False
    else:
        should_show_twitter_login = True
    return render_template('smappboard.html', should_show_twitter_login=should_show_twitter_login)

# the route to get the list of datasets
@app.route('/datasets', methods=['GET'])
@twitter_logged_in
def datasets_list():
    # get db names from mongo
    mongo = pymongo.MongoClient(app.config['SMAPPBOARD_MONGO_HOST'], int(app.config['SMAPPBOARD_MONGO_PORT']))
    db_names = [db_name for i, db_name in enumerate(mongo.database_names()) if db_name not in app.config['IGNORE_DBS']]
    return render_template('datasets.html', datasets=db_names)

# the single dataset page
@app.route('/dataset/<string:data_set_name>', methods=['GET'])
@twitter_logged_in
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

# the route to manage access (need to have admin twitter id)
@app.route('/access/<string:data_set_name>', methods=['GET'])
@twitter_logged_in
def dataset_dashboard(data_set_name):
    return data_set_name

# the route to get to all datasets for getting a sample of recent tweet objects
@app.route('/samples', methods=['GET'])
@twitter_logged_in
def get_samples():
    # get db names from mongo
    mongo = pymongo.MongoClient(app.config['SMAPPBOARD_MONGO_HOST'], int(app.config['SMAPPBOARD_MONGO_PORT']))
    db_names = [db_name for i, db_name in enumerate(mongo.database_names()) if db_name not in app.config['IGNORE_DBS']]
    return render_template('samples.html', datasets=db_names)

# the sample for a single dataset
@app.route('/sample/<string:data_set_name>', methods=['GET'])
@twitter_logged_in
def get_sample_for_dataset(data_set_name):
    pysmap_dataset = pysmap.SmappDataset(['mongo', app.config['SMAPPBOARD_MONGO_HOST'], app.config['SMAPPBOARD_MONGO_PORT'], app.config['MONGO_READONLY_USER'], app.config['MONGO_READONLY_PASS'], data_set_name], collection_regex='(^data$|^tweets$|^tweets_\d+$)')
    tweet_sample = []
    for tweet in pysmap_dataset.limit_number_of_tweets(50):
        tweet_sample.append(dumps(tweet, sort_keys=True, indent=4, separators=(',', ': ')))
    return render_template('sample.html', tweet_sample=tweet_sample, dataset_name=data_set_name)

# the trending page which grabs 15 most recent twitter trends
# token there has 15 charges, if you, plug in your own token
@app.route('/trending', methods=['GET', 'POST'])
@twitter_logged_in
def get_current_worlwide_trends():
    # use the builtin token to get trends
    if request.method == 'GET':
        auth = tweepy.OAuthHandler(app.config['SMAPPBOARD_TRENDS_CONSUMER_KEY'], app.config['SMAPPBOARD_TRENDS_CONSUMER_SECRET'])
        auth.set_access_token(app.config['SMAPPBOARD_TRENDS_ACCESS_TOKEN'], app.config['SMAPPBOARD_TRENDS_ACCESS_TOKEN_SECRET'])
        api = tweepy.API(auth)

        try:
            # https://dev.twitter.com/rest/reference/get/trends/place
            global_trends = api.trends_place(1)[0]
            # for getting commas, did it dif elsewhere
            # for some reason jinja isnt working here
            locale.setlocale(locale.LC_ALL, 'en_US')
            return render_template('trending.html', global_trends=[{'url': trend.get('url'), 'name': trend.get('name'), 'tweet_volume': locale.format("%d", int(trend.get('tweet_volume')) if trend.get('tweet_volume') else 0, grouping=True)} for trend in global_trends['trends']])
        except tweepy.TweepError as e:
            # with single quotes, ast is the only thing that
            # reliably loads json responses from twitter with
            # single quotes
            error_object = ast.literal_eval(e.reason[1:-1])
            return render_template('error.html', error={'message': error_object['message'], 'code': error_object['code'], 'response_code': e.response.status_code})
    # use your own token to get trends
    elif request.method == 'POST':
        return jsonify({"message": "not implemented"}), 200

'''
oauth & 'login' routes
'''

@twitter.tokengetter
def get_twitter_token():
    return session.get('twitter_token')

@app.route('/login')
def login():
    return twitter.authorize(callback=url_for('authorized',  _external=True))

@app.route('/logout')
def logout():
    session.pop('twitter_token', None)
    return redirect(url_for('main_page'))

@app.route('/login/authorized')
def authorized():
    resp = twitter.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
    else:
        session['twitter_token'] = resp
    return redirect(url_for('main_page'))

def current_user():
    return session.get('twitter_token').get('screen_name')

if __name__ == '__main__':
    app.run()
