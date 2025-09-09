# -*- coding: utf-8 -*-

import psycopg2
from collections import deque
from schema_graph import SchemaGraph, Relation


class TraversalEngine:
    def __init__(self, connection, schema_graph: SchemaGraph):
        """
        connection : psycopg2 connection
        schema_graph : SchemaGraph instance
        """
        self.conn = connection
        self.schema_graph = schema_graph

    def traverse(self, root_table, root_column, root_value,
                 direction='both', depth=2, filters=None):
        """
        Traverse the schema graph and collect related rows.
        Eliminates duplicate rows per table.

        Args:
            root_table (str): starting table
            root_column (str): column name in root_table
            root_value (any): value to filter root table
            direction (str): "up", "down", or "both"
            depth (int): max traversal depth
            filters (dict): optional filters {table: "SQL condition"}

        Returns:
            dict of {table: [rows]} where rows = dicts
        """
        visited = set()
        results = {}
        added_rows = {}  # table -> set of seen row tuples

        queue = deque([(root_table, root_column, root_value, 0)])

        with self.conn.cursor() as cur:
            while queue:
                table, column, value, level = queue.popleft()

                if (table, column, value) in visited:
                    continue
                visited.add((table, column, value))

                # Build query
                query = f"SELECT * FROM {table} WHERE {column} = %s"
                if filters and table in filters:
                    query += f" AND {filters[table]}"

                cur.execute(query, (value,))
                rows = [
                    dict(zip([desc[0] for desc in cur.description], row))
                    for row in cur.fetchall()
                ]

                if not rows:
                    continue

                # Initialize table tracking
                if table not in results:
                    results[table] = []
                    added_rows[table] = set()

                # Add row if unique
                for r in rows:
                    row_tuple = tuple(r.items())  # tuple of (col, val)
                    if row_tuple not in added_rows[table]:
                        added_rows[table].add(row_tuple)
                        results[table].append(r)

                if level < depth:
                    # Traverse children (downwards)
                    if direction in ("down", "both"):
                        for rel in self.schema_graph.get_children(table):
                            for r in rows:
                                fk_val = r.get(rel.parent_column)
                                if fk_val is not None:
                                    queue.append(
                                        (rel.child_table, rel.child_column, fk_val, level + 1)
                                    )

                    # Traverse parents (upwards)
                    if direction in ("up", "both"):
                        for rel in self.schema_graph.get_parents(table):
                            for r in rows:
                                fk_val = r.get(rel.child_column)
                                if fk_val is not None:
                                    queue.append(
                                        (rel.parent_table, rel.parent_column, fk_val, level + 1)
                                    )

        return results
