# datasette-faiss

[![PyPI](https://img.shields.io/pypi/v/datasette-faiss.svg)](https://pypi.org/project/datasette-faiss/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-faiss?include_prereleases&label=changelog)](https://github.com/simonw/datasette-faiss/releases)
[![Tests](https://github.com/simonw/datasette-faiss/workflows/Test/badge.svg)](https://github.com/simonw/datasette-faiss/actions?query=workflow%3ATest)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-faiss/blob/main/LICENSE)

Maintain a FAISS index for specified Datasette tables

## Installation

Install this plugin in the same environment as Datasette.

    datasette install datasette-faiss

## Usage

This plugin creates in-memory FAISS indexes for specified tables on startup.

If the tables are modified after the server has started the indexes will not (yet) pick up those changes.

### Configuration

The tables to be indexed must have `id` and `embedding` columns. The `embedding` column must be a `blob` containing embeddings that are arrays of floating point numbers that have been encoded using the following Python function:

```python
def encode(vector):
    return struct.pack("f" * len(vector), *vector)
```
You can import that function from this package like so:
```python
from datasette_faiss import encode
```
You can specify which tables should have indexes created for them by adding this to `metadata.json`:
```json
{
    "plugins": {
        "datasette-faiss": {
            "tables": [
                ["blog", "embeddings"]
            ]
        }
    }
}
```
Each table is an array listing the database name and the table name.

If you are using `metadata.yml` the configuration should look like this:

```yaml
plugins:
  datasette-faiss:
    tables:
    - ["blog", "embeddings"]
```

### SQL functions

The plugin makes four new SQL functions available within Datasette:

#### faiss_search(database, table, embedding, k)
  
Returns the `k` nearest neighbors to the `embedding` found in the specified database and table. For example:
```sql
select faiss_search('blog', 'embeddings', (select embedding from embeddings where id = 3), 5)
```
This will return a JSON array of the five IDs of the records in the `embeddings` table in the `blog` database that are closest to the specified embedding. The returned value looks like this:

```json
["1", "1249", "1011", "5", "10"]
```
You can use the SQLite `json_each()` function to turn that into a table-like sequence that you can join against.

Here's an example query that does that:

```sql
with related as (
  select value from json_each(
    faiss_search(
      'blog',
      'embeddings',
      (select embedding from embeddings limit 1),
      5
    )
  )
)
select * from blog_entry, related
where id = value
```
#### faiss_search_with_scores(database, table, embedding, k)

Takes the same arguments as above, but the return value is a JSON array of pairs, each with an ID and a score - something like this:

```json
[
    ["1", 0.0],
    ["1249", 0.21042244136333466],
    ["1011", 0.29391372203826904],
    ["5", 0.29505783319473267],
    ["10", 0.31554925441741943]
]
```

#### faiss_encode(json_vector)

Given a JSON array of floats, returns the binary embedding blob that can be used with the other functions:

```sql
select faiss_encode('[2.4, 4.1, 1.8]')
-- Returns a 12 byte blob
select hex(faiss_encode('[2.4, 4.1, 1.8]'))
-- Returns 9A991940333383406666E63F
```

#### faiss_decode(vector_blob)

The opposite of `faiss_encode()`.

```sql
select faiss_decode(X'9A991940333383406666E63F')
```
Returns:
```json
[2.4000000953674316, 4.099999904632568, 1.7999999523162842]
```
Note that floating point arithmetic results in numbers that don't quite round-trip to the exact same expected value.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-faiss
    python3 -m venv venv
    source venv/bin/activate

Now install the dependencies and test dependencies:

    pip install -e '.[test]'

To run the tests:

    pytest
