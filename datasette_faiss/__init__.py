from datasette import hookimpl
import faiss
import json
import numpy as np
import struct

indexes = {}
index_ids = {}


@hookimpl
def startup(datasette):
    # Create indexes for configured tables
    async def inner():
        config = datasette.plugin_config("datasette-faiss")
        if not config:
            return
        tables = config.get("tables") or []
        for database, table in tables:
            await populate_index(datasette, database, table)

    return inner


def faiss_search_with_scores(database, table, embedding, k):
    index = indexes[(database, table)]
    ids = index_ids[(database, table)]
    D, I = index.search(np.array([decode(embedding)]), k)
    return json.dumps([(ids[i], d) for i, d in zip(I[0], D[0])], default=float)


def faiss_search(database, table, embedding, k):
    index = indexes[(database, table)]
    ids = index_ids[(database, table)]
    _, I = index.search(np.array([decode(embedding)]), k)
    return json.dumps([ids[i] for i in I[0]])


@hookimpl
def prepare_connection(conn):
    conn.create_function("faiss_search", 4, faiss_search)
    conn.create_function("faiss_search_with_scores", 4, faiss_search_with_scores)
    conn.create_function("faiss_encode", 1, lambda s: encode(json.loads(s)))
    conn.create_function("faiss_decode", 1, lambda b: json.dumps(decode(b)))


async def populate_index(datasette, database, table):
    db = datasette.get_database(database)
    # For the moment assumes id, embedding
    def _populate(conn):
        rows = conn.execute("select id, embedding from [{}]".format(table)).fetchall()
        ids = [row[0] for row in rows]
        embeddings = [decode(row[1]) for row in rows]
        index = faiss.IndexFlatL2(len(embeddings[0]))
        index.add(np.array(embeddings))
        indexes[(database, table)] = index
        index_ids[(database, table)] = ids

    await db.execute_fn(_populate)


def decode(blob):
    return struct.unpack("f" * (len(blob) // 4), blob)


def encode(vector):
    return struct.pack("f" * len(vector), *vector)
