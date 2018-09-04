# Flaskick

Simple frontend to fetch results from kicker.cool.

## Prerequisites
You'll need a working installation of python2.7 with virtualenv, and [bower](https://bower.io/).

## Installation
Clone this repo, then set up a python2 virtualenv:
``` sh
cd flaskick
virtualenv2 .
./bin/pip install -r requirements.txt
./bin/pip install -e .
```

Install the frontend dependencies as well:
``` sh
bower install
```

## Starting the frontend with the development web server
``` sh
./bin/flaskick serve
```
To fetch the data from kicker.cool, press the refresh button in the upper right corner.
