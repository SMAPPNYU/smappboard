'''
primary file with app logic
'''

import os
import re
import ast
import glob
import json
import locale
import pytz
import tweepy
import pysmap

from functools import wraps
from datetime import datetime, timedelta
from bson.json_util import dumps

import smappboard.models
from smappboard.forms import add_term

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

#decorator for a function to only allow people who have logged into twitter
def twitter_logged_in(func):
    def not_authorized_func():
        return render_template('error.html', error={'message': 'you are not an authorized user', 'code': 403, 'response_code': 403})

    @wraps(func)
    def wrapper(*args, **kwargs):
        with open(os.path.dirname(os.path.abspath(__file__))+'/'+app.config['PATH_TO_SMAPPBOARD_USERS'], 'r') as file:
            authed_users_list = json.load(file)
            authed_users_list = [v.lower() for v in authed_users_list]
            if current_user() in authed_users_list:
                return func(*args, **kwargs)
            else:
                return not_authorized_func()
    return wrapper

# the base route
@app.route('/')
def main_page():
    return render_template('smappboard.html',
     should_show_twitter_login=(not current_user()),
     user_logged_in=current_user())

# the route to get the list of datasets
@app.route('/datasets', methods=['GET'])
@twitter_logged_in
def datasets_list():
    #list folders on olympus
    dirs = os.listdir(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'])
    return render_template('datasets.html', datasets=dirs, user_logged_in=current_user())

# the single dataset page
@app.route('/dataset/<string:data_set_name>', methods=['GET'])
@twitter_logged_in
def single_dataset(data_set_name):
    add_term_form = add_term.AddTerm()
    start_path = os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'], data_set_name)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    paths = sorted([path.replace(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'],data_set_name,'data/'),'') for path in glob.glob(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'], data_set_name, 'data', '*'))])
    metadata = json.load(open(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'], data_set_name, 'metadata', 'metadata.json')))
    filters = [json.loads(line) for line in open(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'],data_set_name, 'filters', 'filters.json'))]
    user_screen_names = [permission[0] for permission in metadata['authorized_twitter_handles']]

    if current_user() in user_screen_names:
        return render_template('dataset.html', 
            dataset_name=data_set_name, 
            file_paths=paths,
            users_access=metadata['authorized_twitter_handles'],
            metadata=metadata,
            dataset_size=total_size/1000000000,
            filter_list=filters,
            user_logged_in=current_user(),
            form=add_term_form)
    else:
        return render_template('error.html', error={'message': 'you are not an authorized user for this dataset', 'code': 403, 'response_code': 403}, user_logged_in=current_user())

# the route to manage access (need to have admin twitter id)
@app.route('/access', methods=['GET'])
@twitter_logged_in
def access_list():
    users = json.load(open(os.path.dirname(os.path.abspath(__file__))+'/'+app.config['PATH_TO_SMAPPBOARD_USERS'],'r'))
    return render_template('datasets_access.html', users=users, user_logged_in=current_user())

# the route to manage access (need to have admin twitter id)
@app.route('/single_access/<string:user_name>', methods=['GET'])
@twitter_logged_in
def single_access(user_name):
    metadatas = glob.glob(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'], '*', 'metadata', 'metadata.json'))
    datasets_for_user = []
    for metadata in metadatas:
        m = re.search('/mnt/olympus/(.*)/metadata/metadata.json', metadata)
        om = open(metadata,'r')
        metadata = json.load(om)
        permission = 'nil'
        for handle,permission in metadata['authorized_twitter_handles']:
            if handle == user_name:
                permission = permission
        datasets_for_user.append([m.group(1), permission])
        om.close()
    return render_template('single_access.html',
        user_screen_name=user_name,
        user_datasets=datasets_for_user,
        user_logged_in=current_user())

# the route to get to all datasets for getting a sample of recent tweet objects
@app.route('/samples', methods=['GET'])
@twitter_logged_in
def get_samples():
    #list folders on olympus
    dirs = os.listdir(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'])
    return render_template('samples.html', datasets=dirs, user_logged_in=current_user())

# the sample for a single dataset, will only work if mounting 
# scratch and not archive, it needs a .json file amoung the
# .json.bz2, to pull tweets from
@app.route('/sample/<string:data_set_name>', methods=['GET'])
@twitter_logged_in
def get_sample_for_dataset(data_set_name):
    pysmap_dataset = pysmap.SmappDataset(['json', 'file_pattern', os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'], data_set_name, 'data','*.json')])
    tweet_sample = []
    for tweet in pysmap_dataset.limit_number_of_tweets(50):
        tweet_sample.append(dumps(tweet, sort_keys=True, indent=4, separators=(',', ': ')))
    if len(tweet_sample) == 0:
        return render_template('error.html', error={'message': 'there are no sample tweets', 'code': 404, 'response_code': 404}, user_logged_in=current_user())
    else:
        return render_template('sample.html', tweet_sample=tweet_sample, dataset_name=data_set_name, user_logged_in=current_user())

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
            tweet_volume = [
                {
                'url': trend.get('url'), 'name': trend.get('name'),
                'tweet_volume': locale.format("%d", int(trend.get('tweet_volume')) if trend.get('tweet_volume') else 0, grouping=True)
                } 
                for trend in global_trends['trends']
            ]
            return render_template('trending.html',
            global_trends=tweet_volume,
            user_logged_in=current_user())
        except tweepy.TweepError as e:
            # with single quotes, ast is the only thing that
            # reliably loads json responses from twitter with
            # single quotes
            error_object = ast.literal_eval(e.reason[1:-1])
            return render_template('error.html', error={'message': error_object['message'], 'code': error_object['code'], 'response_code': e.response.status_code}, user_logged_in=current_user())
    # use your own token to get trends
    elif request.method == 'POST':
        return jsonify({"message": "not implemented"}), 200

'''
form responses
'''

@app.route('/internal/form_add_term/<string:dataset_name>', methods=['POST'])
def form_add_links_to_hex(dataset_name):
    term_add = add_term.AddTerm(request.form)
    if request.form and term_add.validate_on_submit():
        value = request.form['value']
        filter_type = request.form['filter_type']

        if filter_type == 'location':
            value = [float(x) for x in list(filter(None, value.split(' ')))]
        elif filter_type == 'follow':
            value = int(value)

        # open filter file and update it
        with open(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'],dataset_name,'filters/filters.json'), 'r') as f:
            list_of_json = []
            for line in f:
                line.strip()
                list_of_json.append(line.strip())
            line = {"value": value, "date_added": datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%a %b %d %H:%M:%S +0000 %Y"), "date_removed": None, "filter_type": filter_type, "turnoff_date": None, "active": True}
            list_of_json.append(json.dumps(line))
        with open(os.path.join(app.config['SMAPPBOARD_SSHFS_MOUNT_POINT'],dataset_name,'filters/filters.json'), 'w') as f:
            for line in list_of_json:
                f.write(line)
                f.write('\n')
        return redirect(url_for('single_dataset', data_set_name=dataset_name))
    else:
        return render_template('error.html', error={'message': 'you are not an authorized user for this dataset', 'code': 403, 'response_code': 403}, user_logged_in=current_user())

'''
oauth & 'login' routes
'''

@twitter.tokengetter
def get_twitter_token(token=None):
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
    token = session.get('twitter_token')
    if token:
        return token.get('screen_name').lower()
    return None

if __name__ == '__main__':
    app.run()
