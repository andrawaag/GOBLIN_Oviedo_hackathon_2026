# Browsing the SSSOM renderings with Comunica

[Comunica](https://comunica.dev/) is a modular, knowledge-graph query engine for JavaScript
that runs in **Node.js *and* the browser**. In this project it is the *query/presentation*
layer: it does not hold the 5 GB of RDF itself — it sends SPARQL to an
[Oxigraph](OXIGRAPH.md) endpoint and renders the results, and it can **federate** across
several endpoints at once (e.g. the local OLS store *and* the Wikidata SPARQL endpoint — the
basis for the planned Wikidata work).

## In the browser, fully self-contained ([`docs/demo.html`](docs/demo.html))

The demo page runs Comunica **entirely client-side** over a bundled sample — no SPARQL endpoint
needed. Because a static host labels `.trig`/`.ttls` as `application/octet-stream` (which Comunica
can't sniff), it fetches the file text and passes a **`serialized`** source with an explicit media
type:

```js
const text = await (await fetch('sample.trig')).text();
const engine = new Comunica.QueryEngine();
const stream = await engine.queryBindings(query, {
  sources: [{ type: 'serialized', value: text, mediaType: 'application/trig', baseIRI }]
});
```

The same page also runs **Oxigraph as WebAssembly** as an in-page store; you can switch engines.
For the RDF 1.2 / Turtle-star sample, Comunica's RDF-star support varies by query — prefer Oxigraph
if a query errors.

## Against a running endpoint

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
