# -*- coding: utf-8 -*-

import click
import json
import os

CONFIG_PATH = os.path.expanduser("~/.pullq/config.json")


def load_configs():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_configs(configs):
    os.makedirs(os.path.dirname(CONFIG_PATH), exists_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(configs, f, indent=4)

@click.group()
def cli():
    """PullQ: Rapidly reproduces issues in test using production data"""
    pass

@cli.command()
@click.option('--name', prompt="Connection Name", help="A name to identify a database connection")
@click.option('--host', prompt='Host')
@click.option('--port', prompt='Port', default=5432)
@click.option('--dbname', prompt='Database Name')
@click.option('--username', prompt="Username")
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=False, help="Password for the DB USER")
def setup(name, host, port, dbname, username, password):
    click.echo(f"[PullQ] Testing connection to {host}:{port}/{dbname} ...")
    
    
if __name__ == '__main__':
    cli()