To run this application it is necessary to:
	Install the required libraries: python, python-pip, libpq-dev, python-dev, libjpeg-dev
	Install virtualenv, create and activate an environment. 
	Install the app libraries in the requirements.txt file. Using pip: 'pip install -r requirements.txt'
	Install and configure elasticsearch 1.7.4.
	Create a postgres database named sundog_db and update postgres credentials inside the settings.py file.
	Create a file named sundog.log and django.log inside a 'log' folder.
	Copy local_config.template file as local_config.py and update the variables values to your local configuration:
	    - Set DEBUG="false" for Production environments, is not necessary on develop.
	    - Set a value for ALLOWED_HOSTS variable for Production environments, is not necessary on develop.
    Run 'python manage.py makemigrations' to create the migrations for the database.
	Run 'python manage.py migrate' to create the tables inside the database.
	Run 'python manage.py createsuperuser' to create the superuser account.
	Install and configure uwsgi and nginx.
	Run 'python manage.py crontab add' to configure the cron jobs.
	Enter the CMS Admin and create the custom pages
