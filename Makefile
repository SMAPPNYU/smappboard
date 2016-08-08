.PHONY: run

run:
	gunicorn smappboard.app:app
rundev:
	gunicorn smappboard.app:app --reload