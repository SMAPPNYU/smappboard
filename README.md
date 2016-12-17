```
                                 _                         _ 
 ___ _ __ ___   __ _ _ __  _ __ | |__   ___   __ _ _ __ __| |
/ __| '_ ` _ \ / _` | '_ \| '_ \| '_ \ / _ \ / _` | '__/ _` |
\__ \ | | | | | (_| | |_) | |_) | |_) | (_) | (_| | | | (_| |
|___/_| |_| |_|\__,_| .__/| .__/|_.__/ \___/ \__,_|_|  \__,_|
                    |_|   |_|
```
:flower_playing_cards: smappboard is a flask app for the smapp dashboard, previously smapp-twitter-admin.

##how to setup nginx (the http server) and gunicorn (the app server):

there are a 100 different ways to configure nginx. this is the way that works well for flask apps and is modular.

http://alexandersimoes.com/hints/2015/10/28/deploying-flask-with-nginx-gunicorn-supervisor-virtualenv-on-ubuntu.html

1 - install and setup nginx

`sudo apt-get install nginx`

2- remove nginx default site

`sudo rm /etc/nginx/sites-enabled/default`

3 - setup an nginx config file for your server in `/etc/nginx/sites-available/YOUR_APP_NAME`

```
server {
    listen 80;
    server_name DOMAIN_OR_IP_FOR_SITE;

    root /path/to/folder/containing/your/app/file/;

    access_log /path/to/where/you/want/your/access/logs/nginx/access.log;
    error_log /path/to/where/you/want/your/error/logs/nginx/access.log;

    location / {
        proxy_set_header X-Forward-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        if (!-f $request_filename) {
            proxy_pass http://127.0.0.1:8000;
            break;
        }
    }

    location /static {
        alias  /path/to/folder/containing/your/static/files/folder;
        autoindex on;
    }
}
```

note `proxy_pass` is the bind address of your gunicorn deamon / porgram, i've left it on 127.0.0.1 (localhost) port 8000 as that is gunicorn's default port binding.

4 - setup log filer declared in nginx and also for gunicorn

`mkdir -p  ~/path/to/where/you/want/your/access/logs/nginx ~/path/to/where/you/want/your/access/logs/gunicorn`

5 - link the site you declared

`sudo ln -s /etc/nginx/sites-available/YOUR_APP_NAME /etc/nginx/sites-enabled/`

6 - restart nginx 

`sudo service nginx restart`

7 - run gunicorn app sever

`/path/to/python /path/to/gunicorn smapp_twitter_admin:app -w 4 -t 120 -D --access-logfile logs/gunicorn/gunicorn_access_log.log --error-logfile logs/gunicorn/gunicorn_error_log.log`

`gunicorn -h` to see what these flags do

8 - load site

http://DOMAIN_OR_IP_FOR_SITE

resources:

[nginx docs](http://nginx.org/en/docs/)

[how to deploy on digital ocean](http://blog.marksteve.com/deploy-a-flask-application-inside-a-digitalocean-droplet)

[built on this standard specification](http://code.tutsplus.com/tutorials/creating-a-web-app-from-scratch-using-python-flask-and-mysql--cms-22972)

[this flask app](https://github.com/imwilsonxu/fbone/tree/master/fbone)

[python packages and modules](https://docs.python.org/2/tutorial/modules.html)

[pymongo docs](http://api.mongodb.org/python/current/api/)

[werkzeug docs](http://werkzeug.pocoo.org/docs/0.11/)

[flask docs](http://flask.pocoo.org/docs/0.10/)

[app.route in flask] (http://ains.co/blog/things-which-arent-magic-flask-part-1.html)

[explanation of decorators] (http://stackoverflow.com/questions/17330160/how-does-the-property-decorator-work)

[deploy flask app to digital ocean with gunicorn] (http://blog.marksteve.com/deploy-a-flask-application-inside-a-digitalocean-droplet)

[nginx tutorial](https://www.digitalocean.com/community/tutorials/understanding-the-nginx-configuration-file-structure-and-configuration-contexts)

#requirements.txt

dependencies to run this flask app

install with:

```bash
pip install -r requirements.txt
```

#app.py

core app logic file with all routes

#models

data models for the app

#static

static files for css, bootstrap, themes, etc

#templates

jinja2 templates for displaying the pages of our flask app

#tests 

tests for the flask app

#/smappboard

takes you to the main dashboard where you can start, stop, and pause collections. primary dashboard 

#structure

#/datasets

lists all collections that should be running

#/dataset/collection_name

get the page for an individual dataset, this is where you can do things related to that dataset

#/access

takes you to a page that cna be used to manage permissions for each collection, remove a user from all collections, etc.

#/trends

takes you to a page that has the current top global twitter trends, feulued by an a twitter api 4 token set in config.py

#development

if you try to run the oauth routes for twitter (specifically the /login route) it will complain at you with [this issue](http://stackoverflow.com/questions/37950999/twitter-oauth-with-flask-oauthlib-failed-to-generate-request-token):

```
flask_oauthlib.client.OAuthException: Failed to generate request token
```

this is caused by lacking a callback url setting on your app's page. if you are working on localhost this is a pain. you can put a placeholder url there until you get the real one.

everytime you go to develop run these steps:

create anaconda environment `conda env create`

load environment vars with `source env.sh` (needs to be done everytime you restart your commandline)

export a flask secret wih `export FLASK_SECRET_KEY=YOUR_SECRET` read aobut how to generate a secret [here](https://gist.github.com/geoffalday/2021517) (save this secret because you'll need to use it for future setups)

then type `make run` or `gunicorn smappboard.app:app`


#how to connect to olympus

1 - map a port from a machine with scratch to the machine running the flask app

2 - mount sshfs over this port mapping.

3 - you can map a port from where we run our collector tunnels, or any other place with access to hpc /scratch/olympus/

in practice:

sudo mkdir -p /mnt/olympus/

[setup hpctunnel as here](https://github.com/SMAPPNYU/smapphowto/blob/master/howto_get_started_on_the_hpc_cluster.md#5--moving-data-to-your-computer).

ssh hpctunnel

bash sshfs_mount.sh yns207 8023 /home/yvan/.ssh/id_rsa (enter your hpc password when prompted).

to run sshfs you will need fuse and sshfs from [here](https://osxfuse.github.io/): https://osxfuse.github.io/

to unmount the fs:

sudo umount /mnt/olympus

there may be two password prompts that look the same, first is your computers sudo password, the second i you hpc password.

you can edit the script to mount /scratch/olympus (more performant but gets purged) or to mount /archive/smapp/olympus, but there are some concerns about the performance of the archive

#author

[yvan](https://github.com/yvan)
