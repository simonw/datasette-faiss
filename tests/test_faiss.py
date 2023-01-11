from datasette.app import Datasette
from datasette_faiss import encode
import pytest
import pytest_asyncio
import sqlite3
import urllib.parse


@pytest.fixture(scope="session")
def path(tmp_path_factory):
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = str(db_directory / "demo.db")
    conn = sqlite3.connect(db_path)
    with conn:
        conn.executescript(
            """
        create table documents (id integer primary key, title text);
        create table embeddings (id integer primary key, embedding blob);
        insert into documents (id, title) values (1, 'First document');
        insert into documents (id, title) values (2, 'Second document');
        """
        )
        # Now the embeddings
        conn.execute(
            "insert into embeddings (id, embedding) values (?, ?)",
            (1, encode([1, 2.5, 3])),
        )
        conn.execute(
            "insert into embeddings (id, embedding) values (?, ?)",
            (2, encode([4, 5.5, 6])),
        )
    conn.close()
    return db_path


@pytest.mark.asyncio
async def test_faiss(path):
    ds = Datasette(path)
    await ds.invoke_startup()
    response = await ds.client.get(
        "/demo.json?"
        + urllib.parse.urlencode(
            {
                "_shape": "array",
                "sql": "select faiss_search_with_scores('embeddings', faiss_encode('[1, 2, 3]'), 2) as results",
            }
        )
    )
    assert False
