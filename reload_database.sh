#!/bin/sh

# Bash script

dropdb linguistics
createdb linguistics
python manage.py syncdb
