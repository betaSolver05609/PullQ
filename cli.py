# -*- coding: utf-8 -*-

import click
import json
import os
from db_connector import test_connection
from schema_graph import SchemaGraph

CONFIG_PATH = os.path.expanduser("~/.pullq/config.json")


def load_configs():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_configs(configs):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
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
    configs = load_configs()
    configs[name] = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "username": username,
        "password": password
    }
    save_configs(configs)

    conn_test = test_connection(host, port, dbname, username, password)

    config = configs[name]
    sg = SchemaGraph(config)
    sg.build()
    sg.print_graph()

    click.echo(f"[PullQ] Testing connection to {host}:{port}/{dbname} ...")
    click.echo("Database Connection succeeded") if conn_test else click.echo("Database connection failed. Please check the details")


@cli.command()
def load():
    """Load a saved connection config"""
    configs = load_configs()
    if not configs:
        click.echo("No saved configs found. Run `setup` first.")
        return

    click.echo("Available saved connections:")
    names = list(configs.keys())
    for i, name in enumerate(names, 1):
        click.echo(f"{i}. {name}")

    choice = click.prompt("Select a connection", type=int)
    if choice < 1 or choice > len(names):
        click.echo("Invalid selection")
        return

    selected_name = names[choice - 1]
    config = configs[selected_name]
    
    print(config)

    conn_test = test_connection(config["host"], config["port"], config["dbName"], config["username"], config["password"])

    sg = SchemaGraph(config)
    sg.build()
    sg.print_graph()

    click.echo(f"[PullQ] Testing connection to {config['host']}:{config['port']}/{config['dbName']} ...")
    click.echo("Database Connection succeeded") if conn_test else click.echo("Database connection failed. Please check the details")


@cli.command()
def start():
    """Start PullQ CLI: choose between new setup or loading existing config"""
    choice = click.prompt("Do you want to use an existing config? (y/n)", type=str)
    if choice.lower().startswith("y"):
        cli(["load"])  # calls the load command
    else:
        cli(["setup"])  # calls the setup command


if __name__ == '__main__':
    cli()
