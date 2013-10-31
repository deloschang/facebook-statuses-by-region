#!/bin/sh

dropdb linguistics
createdb linguistics
python manage.py syncdb
