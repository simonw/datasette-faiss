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
@pytest.mark.parametrize(
    "sql,expected",
    (
        (
            "select faiss_search('demo', 'embeddings', faiss_encode('[1, 2, 3]'), 2) as results",
            "[1, 2]",
        ),
        (
            "select faiss_search_with_scores('demo', 'embeddings', faiss_encode('[1, 2, 3]'), 2) as results",
            "[[1, 0.25], [2, 30.25]]",
        ),
        (
            "select faiss_encode('[1, 2, 3]') as results",
            {"$base64": True, "encoded": "AACAPwAAAEAAAEBA"},
        ),
        (
            "select faiss_decode(faiss_encode('[1, 2, 3]')) as results",
            "[1.0, 2.0, 3.0]",
        ),
    ),
)
async def test_faiss(path, sql, expected):
    ds = Datasette(
        [path],
        metadata={"plugins": {"datasette-faiss": {"tables": [["demo", "embeddings"]]}}},
    )
    await ds.invoke_startup()
    response = await ds.client.get(
        "/demo.json?"
        + urllib.parse.urlencode(
            {
                "_shape": "array",
                "sql": sql,
            }
        )
    )
    assert response.json()[0]["results"] == expected
