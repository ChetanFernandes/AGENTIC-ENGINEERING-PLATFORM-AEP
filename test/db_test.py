import pytest
from langgraph.store.postgres import PostgresStore
from database_config import DB_URI

def test_postgres_store_setup():
    with PostgresStore.from_conn_string(DB_URI) as store:
        store.setup()

    print("PostgresStore setup successful")


# pytest test\db_test.py -v -s