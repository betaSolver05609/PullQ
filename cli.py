# -*- coding: utf-8 -*-

import click
import json
import os
from db_connector import test_connection, get_connection
from schema_graph import SchemaGraph
from traversal_engine import TraversalEngine
from reverse_engineering import generate_insert_statements

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
    click.echo(f"[PullQ] Loaded config '{selected_name}'")
    return config


@cli.command()
@click.option("--table", prompt="Root table", help="Starting table for extraction")
@click.option("--column", prompt="Root column", help="Column in root table to filter on")
@click.option("--value", prompt="Root value", help="Value for the root column")
@click.option("--depth", default=2, help="Traversal depth (default=2)")
@click.option("--direction", type=click.Choice(["up", "down", "both"]), default="both", help="Traversal direction")
def extract(table, column, value, depth, direction):
    """Interactive flow: choose or setup a DB connection, then extract related data."""
    click.echo("[PullQ] Starting interactive extraction flow...")
    configs = load_configs()

    # Determine whether to use new or existing connection
    if not configs:
        click.echo("No saved configs found. Let's set up a new connection.")
        choice = "new"
    else:
        choice = click.prompt(
            "Do you want to (1) setup a new connection or (2) choose existing?",
            type=click.Choice(["1", "2"]),
            default="2"
        )

    # Setup new connection
    if choice == "1" or choice == "new":
        name = click.prompt("Connection Name")
        host = click.prompt("Host")
        port = click.prompt("Port", default=5432, type=int)
        dbname = click.prompt("Database Name")
        username = click.prompt("Username")
        password = click.prompt("Password", hide_input=True)

        if test_connection(host, port, dbname, username, password):
            click.echo("✅ Connection succeeded, saving config.")
            configs[name] = {
                "host": host,
                "port": port,
                "dbname": dbname,
                "username": username,
                "password": password
            }
            save_configs(configs)
            db_conf = configs[name]
        else:
            click.echo("❌ Connection failed. Exiting.")
            return

    # Load existing connection
    else:
        click.echo("Available saved connections:")
        names = list(configs.keys())
        for i, name in enumerate(names, 1):
            click.echo(f"{i}. {name}")

        selection = click.prompt("Select a connection", type=int)
        if selection < 1 or selection > len(names):
            click.echo("Invalid selection. Exiting.")
            return
        db_conf = configs[names[selection - 1]]
        click.echo(f"[PullQ] Loaded config '{names[selection - 1]}'")

    # Use context manager to get connection
    with get_connection(db_conf) as conn:
        # Build schema graph
        sg = SchemaGraph(db_conf)
        sg.connect()
        sg.build()

        # Traverse from root record
        te = TraversalEngine(conn, sg)
        results = te.traverse(
            root_table=table,
            root_column=column,
            root_value=value,
            direction=direction,
            depth=depth
        )

        # Generate INSERT statements
        inserts = generate_insert_statements(results, sg)
        click.echo("\n-- Generated INSERT statements --")
        for stmt in inserts:
            click.echo(stmt)


if __name__ == '__main__':
    cli()