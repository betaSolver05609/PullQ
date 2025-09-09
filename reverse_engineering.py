# -*- coding: utf-8 -*-

from collections import defaultdict, deque
from schema_graph import SchemaGraph, Relation


def generate_insert_statements(data, schema_graph: SchemaGraph):
    """
    Convert traversal results into INSERT statements.

    Args:
        data (dict): {table: [rows]} from TraversalEngine
        schema_graph (SchemaGraph): schema graph instance

    Returns:
        list of SQL INSERT statements (strings) in correct order
    """
    # Compute insertion order based on FK deps
    order = resolve_dependency_order(data.keys(), schema_graph)

    statements = []
    for table in order:
        rows = data.get(table, [])
        if not rows:
            continue

        columns = list(rows[0].keys())
        col_list = ", ".join(columns)

        for row in rows:
            values = []
            for col in columns:
                val = row[col]
                if val is None:
                    values.append("NULL")
                elif isinstance(val, str):
                    escaped_val = val.replace("'", "''")
                    values.append(f"'{escaped_val}'")
                else:
                    values.append(str(val))
            val_list = ", ".join(values)
            sql = f"INSERT INTO {table} ({col_list}) VALUES ({val_list});"
            statements.append(sql)

    return statements


def resolve_dependency_order(tables, schema_graph: SchemaGraph):
    indegree = {t: 0 for t in tables}
    graph = defaultdict(list)

    for table in tables:
        for rel in schema_graph.get_children(table):
            if rel.child_table in tables:
                graph[table].append(rel.child_table)
                indegree[rel.child_table] += 1

    # topological sort
    queue = deque([t for t in indegree if indegree[t] == 0])
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nei in graph[node]:
            indegree[nei] -= 1
            if indegree[nei] == 0:
                queue.append(nei)
    return order

