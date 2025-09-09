# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import sys
import json
from db_connector import connect_postgres


class Relation:
    """Represents a foreign key relation between two tables."""
    def __init__(self, parent_table, parent_column, child_table, child_column):
        self.parent_table = parent_table
        self.parent_column = parent_column
        self.child_table = child_table
        self.child_column = child_column

    def as_dict(self):
        return {
            "parent_table": self.parent_table,
            "parent_column": self.parent_column,
            "child_table": self.child_table,
            "child_column": self.child_column,
        }

    def __repr__(self):
        return f"{self.child_table}({self.child_column} → {self.parent_table}.{self.parent_column})"


class SchemaGraph:
    def __init__(self, configs):
        """
        config = {
            "host": "...",
            "port": 5432,
            "dbName": "...",
            "username": "...",
            "password": "..."
        }
        """
        self.configs = configs
        self.conn = None
        self.graph = {}  # table → list of Relation

    def connect(self):
        connection = connect_postgres(self.configs)
        if connection is None:
            print("Connection to database failed... Exiting")
            sys.exit(1)
        else:
            self.conn = connection

    def build(self, schema='public'):
        """
        Build Dependency Graph for tables based on foreign keys.
        Returns
        -------
        Dict: table → list of Relation
        """
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        query = """
        SELECT
            tc.table_name AS child_table,
            kcu.column_name AS child_column,
            ccu.table_name AS parent_table,
            ccu.column_name AS parent_column
        FROM
            information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
             AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
             AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_schema = %s;
        """
        cursor.execute(query, (schema,))
        rows = cursor.fetchall()

        graph = {}
        for child_table, child_column, parent_table, parent_column in rows:
            rel = Relation(parent_table, parent_column, child_table, child_column)

            # Add parent → child
            if parent_table not in graph:
                graph[parent_table] = []
            graph[parent_table].append(rel)

            # Add child → parent (reverse edge)
            if child_table not in graph:
                graph[child_table] = []
            graph[child_table].append(rel)

        self.graph = graph
        cursor.close()
        return graph

    def get_children(self, table):
        """Return all child relations for a table."""
        return [rel for rel in self.graph.get(table, []) if rel.parent_table == table]

    def get_parents(self, table):
        """Return all parent relations for a table."""
        return [rel for rel in self.graph.get(table, []) if rel.child_table == table]

    def print_graph(self):
        for table, relations in self.graph.items():
            print(f"{table} →")
            for rel in relations:
                if rel.parent_table == table:  # parent → child edge
                    print(f"   {rel.child_table} ({rel.child_column} → {rel.parent_column})")
                elif rel.child_table == table:  # child → parent edge
                    print(f"   depends on {rel.parent_table} ({rel.child_column} → {rel.parent_column})")

    def to_json(self, filepath="schema_graph.json"):
        with open(filepath, "w") as f:
            json.dump(
                {t: [r.as_dict() for r in rels] for t, rels in self.graph.items()},
                f,
                indent=4
            )

    def load_json(self, filepath="schema_graph.json"):
        with open(filepath, "r") as f:
            raw = json.load(f)
            graph = {}
            for table, rels in raw.items():
                graph[table] = [
                    Relation(
                        r["parent_table"],
                        r["parent_column"],
                        r["child_table"],
                        r["child_column"],
                    )
                    for r in rels
                ]
            self.graph = graph
