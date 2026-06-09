# Querying the SSSOM renderings with Oxigraph

[Oxigraph](https://github.com/oxigraph/oxigraph) is a fast, embeddable RDF database written in
Rust. It is the store of choice for this project because:

1. **It natively parses *and* queries RDF 1.2 / RDF-star.** The Turtle-star rendering
   (`sssom_all.ttls`) uses triple-term reification (`{| … |}` → `rdf:reifies`). Many stores —
   and Python's rdflib — cannot even parse this; Oxigraph can, and exposes it through SPARQL 1.2.
2. **It scales to the multi-GB renderings** without a JVM or external services.
3. **It serves a standard, CORS-enabled SPARQL endpoint** that the browser-based
   [Comunica](COMUNICA.md) demo (and any SPARQL client) can query.

## Install

Pick one:

```bash
cargo install oxigraph-cli                 # Rust toolchain
pip  install pyoxigraph                     # Python (library + `pyoxigraph` server module)
docker pull ghcr.io/oxigraph/oxigraph       # container
```

## Get the data

The gzipped renderings are in [`data/`](data/) (Git LFS) — see [`data/README.md`](data/README.md).
Fetch and unzip:

```bash
git lfs pull                       # if files are LFS pointers after clone
gunzip -k data/sssom_all.trig.gz   # → sssom_all.trig  (named graphs, 1.5 GB)
gunzip -k data/sssom_all.ttls.gz   # → sssom_all.ttls  (RDF 1.2 / Turtle-star, 3.7 GB)
```

## Load

Keep the two renderings in **separate stores** — they are two representations of the same
mappings, not data to be merged.

```bash
# Named-graph rendering (quads → a dataset with one graph per mapping_set)
oxigraph load  --location ./store-graphs --file sssom_all.trig

# RDF 1.2 rendering (Oxigraph preserves the triple terms / reifiers)
oxigraph load  --location ./store-star   --file sssom_all.ttls
```

> With Docker: `docker run --rm -v "$PWD:/data" ghcr.io/oxigraph/oxigraph \
> load --location /data/store-graphs --file /data/sssom_all.trig`

## Serve a SPARQL endpoint

```bash
oxigraph serve --location ./store-graphs --bind 127.0.0.1:7878
# SPARQL query endpoint:  http://localhost:7878/query
# (point a second instance at ./store-star on another port for the RDF 1.2 view)
```

Oxigraph's server sends permissive CORS headers, so the `docs/index.html` slide (even opened
from `file://`) can query `http://localhost:7878/query` directly.

## Example queries

**Named-graph store** — mappings grouped by their source graph:

```sparql
SELECT ?graph ?subject ?predicate ?object WHERE {
  GRAPH ?graph { ?subject ?predicate ?object }
} LIMIT 25
```

List the mapping sets and their confidence (asserted in the default graph):

```sparql
PREFIX sssom: <https://w3id.org/sssom/>
SELECT ?set ?confidence ?source WHERE {
  ?set a sssom:MappingSet .
  OPTIONAL { ?set sssom:mapping_set_confidence ?confidence }
  OPTIONAL { ?set sssom:mapping_set_source     ?source }
} LIMIT 50
```

**RDF 1.2 store** — each mapping with its per-mapping justification (SPARQL-star):

```sparql
PREFIX sssom: <https://w3id.org/sssom/>
SELECT ?subject ?predicate ?object ?justification WHERE {
  ?subject ?predicate ?object .
  ?r rdf:reifies <<( ?subject ?predicate ?object )>> .
  ?r sssom:mapping_justification ?justification .
} LIMIT 25
```

## Query from the command line

```bash
curl -s http://localhost:7878/query \
  --data-urlencode 'query=SELECT (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } }' \
  -H 'Accept: application/sparql-results+json'
```
