from __future__ import absolute_import, division, print_function

import click

from flaskick.app import app, db
from flaskick.models import import_matches
from flaskick.views import index
from flaskick.api import api

@click.group()
def cli():
    pass


@cli.command()
def test():
    pass


GAMES_YAML_PATH = '/home/dm/code/kicker-scraper/data'


@cli.command("import")
@click.argument("data-path")
def import_matches_cli(data_path):
    db.create_all()
    import_matches(data_path)


@cli.command()
def serve():
    db.create_all()
    app.run()


if __name__ == '__main__':
    cli()
