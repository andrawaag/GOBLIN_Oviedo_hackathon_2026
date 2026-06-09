# Browsing the SSSOM renderings with Comunica

[Comunica](https://comunica.dev/) is a modular, knowledge-graph query engine for JavaScript
that runs in **Node.js *and* the browser**. In this project it is the *query/presentation*
layer: it does not hold the 5 GB of RDF itself — it sends SPARQL to an
[Oxigraph](OXIGRAPH.md) endpoint and renders the results, and it can **federate** across
several endpoints at once (e.g. the local OLS store *and* the Wikidata SPARQL endpoint — the
basis for the planned Wikidata work).

## In the browser (the slide)

[`docs/index.html`](docs/index.html) embeds the Comunica browser build from a CDN:

```html
<script src="https://rdf.js.org/comunica-browser/versions/latest/engines/query-sparql/comunica-browser.js"></script>
<script>
  const engine = new Comunica.QueryEngine();
  const stream = await engine.queryBindings(query, {
    sources: [{ type: 'sparql', value: 'http://localhost:7878/query' }]
  });
  stream.on('data', b => console.log(b.get('subject').value));
</script>
```

Start Oxigraph (see [OXIGRAPH.md](OXIGRAPH.md)), open the slide, and hit **Run query**.

## From the command line

```bash
npm install -g @comunica/query-sparql

comunica-sparql http://localhost:7878/query \
  "SELECT * WHERE { GRAPH ?g { ?s ?p ?o } } LIMIT 10"
```

## Federation (future: OLS + Wikidata)

Comunica queries multiple sources transparently — list them all under `sources`:

```bash
comunica-sparql \
  http://localhost:7878/query \
  https://query.wikidata.org/sparql \
  "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
```

This is why Comunica pairs well with the Wikidata extraction that remains as future work: the
local OLS mappings and Wikidata cross-references can be joined in a single federated query
without first materialising them into one store.

## RDF 1.2 / SPARQL-star note

The Turtle-star rendering needs SPARQL-star pattern support (the `<<( … )>>` / `rdf:reifies`
forms). When querying it, prefer letting Oxigraph do the heavy lifting (`type: 'sparql'`
source pointing at the RDF 1.2 store) rather than asking Comunica to dereference the raw file.
