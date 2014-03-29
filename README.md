capomastro [![Build Status](https://travis-ci.org/capomastro/capomastro.svg)](https://travis-ci.org/capomastro/capomastro)
==========
Master builder

Capomastro manages build dependencies built using Jenkins.

Multiple "Projects" can share common dependencies, and the artifact details are
pulled into the database where they can easily be download, or archived.

To get started...

1. `mkvirtualenv <name>`

2. `pip install -r requirements.txt` (or dev-requirements.txt if you're going
   to run the tests)

3. Copy the `capomastro/local_settings.py.example` to `capomastro/local_settings.py`
   and fixup the database entry

4. You'll need to setup the database `./manage.py syncdb --migrate` - you'll be
   prompted to create a superuser.

Steps 1 and 2 can be replaced with `tox -e devenv`. Then either activate the
virtualenv manually with `source devenv/bin/activate` or explicitly call
Python from the virtualenv with `devenv/bin/python`.

You can do the next steps through the /admin/ interface, so go to
http://localhost:8000/admin/ login and continue.

I'd recommend installing gunicorn, but you can use the default ./manage.py
runserver.

You'll need a celery worker running as well as rabbitmq.

$ gunicorn -b 0.0.0.0:8000 capomastro.wsgi:application
$ celery -A capomastro worker -l info

5. You'll need an initial jenkins.JenkinsServer object, with the correct credentials,
   and the REMOTE_ADDR setup correctly, so that it can receive callbacks.

7. Create a DependencyType, and Dependency for that DependencyType, the
   Dependency should be hooked up to your Job model.


You should have...


     Dependency -> DependencyType
         |
        Job
         |
    JenkinsServer

You can create several dependencies, with different jobs.

Your Jenkins Server requires the "notifications" plugin installed.

And the jobs that are created must have a parameter "BUILD_ID" and they must
have a notification setup, type http/json and with a callback address of
http://hostname/jenkins/notifications/.

8. Now you can create a Project, associated with your dependencies, at
   localhost:8000/projects/create/ "auto track" means that the project will use
   the latest version of any dependencies automatically.

9. Now, you can build your project, this will create a project build, and
   trigger the tasks to build your project.

Testing
-------

Assuming you have [tox](https://testrun.org/tox/latest/) installed, run:

    $ tox
