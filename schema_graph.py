# -*- coding: utf-8 -*-
import sys
from db_connector import connect_postgres
class SchemaGraph:
    def __init__(self, configs):
        """
        config = {
            "host": "...",
            "port": 5432,
            "dbname": "...",
            "username": "...",
            "password": "..."
        }
        """
        self.configs = configs
        self.conn = None
        self.graph={}
    
    def connect(self):
        connection = connect_postgres(
            self.configs['host'],
            self.configs['port'],
            self.configs['dbname'],
            self.configs['username'],
            self.configs['password']
            )
        if connection is None:
            print("Connection to database failed... Exiting")
            sys.exit(1)
        else:
            self.conn = connection
        
    
    def build(self, schema='public'):
        """
        Build Dependency Graph for table based on foregin keys

        Parameters
        ----------
        schema : TYPE, optional
            DESCRIPTION. The default is 'public'.

        Returns
        -------
        Dict.

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
        rows=cursor.fetchall()
        
        graph={}
        
        for child_table, child_column, parent_table, parent_column in rows:
            if parent_table not in graph:
                graph[parent_table] = []
            graph[parent_table].append({
                "child_table": child_table,
                "child_column": child_column,
                "parent_column": parent_column
                })
            
            self.graph = graph
            cursor.close()
            return graph
        
    def print_graph(self):
        for parent, children in self.graph.items():
            print(f"{parent} →")
            for rel in children:
                print(f"   {rel['child_table']} ({rel['child_column']} → {rel['parent_column']})")
    
        
        

