.PHONY: run

run:
	source env.sh && gunicorn smappboard.app:app
rundev:
	source env.sh && gunicorn smappboard.app:app --reload
runprod:
	source env.sh && gunicorn smappboard.app:app -w 4 -t 120 -D --access-logfile /home/yvan/pylogs/gunicorn_access.log --error-logfile /home/yvan/pylogs/gunicorn_error.log