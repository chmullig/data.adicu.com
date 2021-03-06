import os
import momoko
import psycopg2
import functools
import logging

pg_host  = os.getenv('PG_HOST')
pg_port  = int(os.getenv('PG_PORT'))
pg_db    = os.getenv('PG_DB')
pg_user  = os.getenv('PG_USER')
pg_pass  = os.getenv('PG_PASSWORD')
pg_limit = int(os.getenv('PG_LIMIT'))
dsn = 'dbname=%s user=%s password=%s host=%s port=%s' % (
            pg_db, pg_user, pg_pass, pg_host, pg_port)


def pg_aync():
    return momoko.AsyncClient({
            'host': pg_host,
            'database': pg_db,
            'port': pg_port,
            'user': pg_user,
            'password': pg_pass,
            'min_conn': 1,
            'max_conn': 20,
            'cleanup_timeout': 5
        })

def pg_sync():
    return psycopg2.connect(database=pg_db, user=pg_user,
            password=pg_pass, host=pg_host, port=pg_port)

class PGQuery:
    def __init__(self, model=None, model_functions=None):
        self.pg = pg_aync()
        self.model = model
        self.model_functions = model_functions
    
    def execute(self, args, page=0, limit=0, callback=None):
        internal_callback = functools.partial(self._on_sql_response, callback=callback)
        query, arguments = self.build_sql_query(args)
        
        if limit and limit < pg_limit:
            arguments["limit"] = limit
        else:
            arguments["limit"] = pg_limit
        arguments["page"] = page * arguments["limit"]

        logging.info("Making SQL Query: %s %s" % (query, str(arguments)))
        self.pg.execute(query, arguments, callback=internal_callback)

    def build_sql_query(self, arguments):
        # We have a dict of query keys and values and call getattr with the key,
        # which returns a function pointer with the name of "key", which we call, which
        # provides a query fragment that function makes
        model = self.model
        # slug is a list, each with (key, value, query_fragment)
        slug = [self.attr_func_wrap(key, value) for key, value in
                arguments.iteritems()]
        query_fragments = [fragment for _, _, fragment in slug]
        modified_arguments = {key: value for key, value, _ in slug}
        sql_query_fragments = {
                "select_body": ", ".join(model.SELECT),
                "table": model.TABLE,
                "query_fragments": " AND ".join(query_fragments),
                "limit": "%(limit)s",
                "page": "%(page)s",
                "order_by" : model.ORDERBY,
        }

        query = "SELECT %(select_body)s FROM %(table)s WHERE %(query_fragments)s ORDER BY %(order_by)s LIMIT %(limit)s OFFSET %(page)s;" % sql_query_fragments
        
        return query, modified_arguments
    
    def attr_func_wrap(self, key, value):
        func = getattr(self.model_functions, key)
        value, fragment = func(value)
        return key, value, fragment

    def _on_sql_response(self, cursor, callback=None):
        response = [self.model.build_response_dict(row) for row in cursor.fetchall()]
        # We call back to tornado to respond to the client
        callback(response)
