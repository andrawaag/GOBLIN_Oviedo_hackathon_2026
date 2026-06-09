# GOBLIN · Oviedo BioHackathon 2026

**Rendering SSSOM ontology mappings as RDF — named graphs *and* RDF 1.2.**

This repository is the output of a GOBLIN track at the Oviedo BioHackathon 2026.
We take [SSSOM](https://mapping-commons.github.io/sssom/) mapping sets and render them
into two complementary RDF serializations, then serve them for SPARQL querying via
[Oxigraph](https://github.com/oxigraph/oxigraph) and browse them with
[Comunica](https://comunica.dev/).

👉 **Slide / demo:** [`docs/index.html`](docs/index.html) (open in a browser — includes a live Comunica query box).

---

## What is SSSOM?

SSSOM — the *Simple Standard for Sharing Ontological Mappings* — is a standard for
publishing mappings between ontology terms (e.g. `MONDO:0000001 ↔ DOID:4`). Its native
serialization is a **hybrid of TSV and YAML**: the mappings are a TSV table, and the
mapping-set metadata (provenance, confidence, the `curie_map` used to expand CURIEs) is a
**YAML block embedded in the TSV's leading `#` comment lines**.

```
# mapping_set_id: https://w3id.org/commons/ols/mappings/mondo.ols.sssom.tsv
# mapping_set_confidence: '0.7'
# curie_map:
#   MONDO: http://purl.obolibrary.org/obo/MONDO_
#   DOID:  http://purl.obolibrary.org/obo/DOID_
subject_id      predicate_id        object_id   mapping_justification       subject_label  object_label
MONDO:0000001   oboInOwl:hasDbXref  DOID:4      semapv:UnspecifiedMatching  disease        disease
```

## The two renderings — design choice

A mapping is, ontologically, *a statement about a statement*. The two approaches attach that
metadata at **different layers of the RDF stack**:

| | **Named graphs (TriG)** | **RDF 1.2 (Turtle-star)** |
|---|---|---|
| Layer | RDF 1.1 dataset / context → quads | abstract syntax → triple terms |
| Granularity | one graph per `mapping_set` | per mapping (`{\| … \|}` annotation) |
| Carries | set-level provenance on the graph | justification + labels per mapping (**lossless**) |
| Semantics | dataset semantics **undefined** by spec (convention) | **defined**; triple term opaque, non-asserting (`rdf:reifies`) |
| Tooling | universal — SPARQL 1.1 `GRAPH` | needs an RDF-star engine (rdflib can't parse it; Oxigraph can) |
| Cost | ~1 quad / mapping | ~5× statement blow-up (6.2M → 34M) |
| Models | `sssom:MappingSet` | `sssom:Mapping` |

**Key insight:** named graph ↔ `MappingSet`, triple term ↔ `Mapping`. They model *different
layers*, so they **compose** — the TriG file is the portable, partition-by-source view; the
Turtle-star file is the lossless, per-mapping master.

## Sources

- ✅ **EBI OLS** *(done)* — the [OLS4](https://www.ebi.ac.uk/ols4/) service publishes
  per-ontology SSSOM extracts. We rendered **271 mapping sets / 6,238,000 mappings** into both
  formats in ~91 s (TriG 1.5 GB, Turtle-star 3.7 GB).
- 🔭 **Wikidata** *(future work)* — we began extracting ontology cross-references from Wikidata
  (a natural mapping hub via external-ID properties) and emitting SSSOM, but did not finish
  within the hackathon. Comunica federation makes the eventual join natural: query the local
  Oxigraph endpoint *and* the Wikidata SPARQL endpoint together.

## Repository layout

```
docs/index.html        Slide + live Comunica demo
scripts/sssom_serialize.py   Streaming SSSOM-TSV → TriG + Turtle-star serializer
COMUNICA.md            How to query the renderings with Comunica
OXIGRAPH.md            How to load & serve the renderings with Oxigraph
data/README.md         Where to get the rendered RDF (Zenodo)
```

## Reproduce the renderings

```bash
# input_dir holds the *.sssom.tsv files; writes sssom_all.trig + sssom_all.ttls
python3 scripts/sssom_serialize.py <input_dir> <output_dir>
```

The serializer streams the TSV, parses the YAML header, expands every CURIE to a full IRI
(no prefix collisions across files), and percent-encodes CURIE local parts so SMILES/InChI
identifiers stay valid RFC 3987 IRIs. Both outputs validate with a strict RDF 1.2 parser.

## Data

The **gzipped** renderings are committed under [`data/`](data/) via **Git LFS**
(`sssom_all.trig.gz` 87 MB, `sssom_all.ttls.gz` 204 MB; ~5.2 GB uncompressed). Fetch with
`git lfs pull` then `gunzip`. A citable Zenodo copy is also planned — see
[`data/README.md`](data/README.md).

## Schemas

- [`docs/schema-named-graphs.md`](docs/schema-named-graphs.md) — mermaid diagram + ShEx
- [`docs/schema-rdf12.md`](docs/schema-rdf12.md) — mermaid diagram + ShEx-*style* pseudo-syntax
  (ShEx 2.1 has no RDF 1.2 triple-term support yet)

## License

Code: MIT. Rendered mappings inherit the licenses of their upstream sources (OLS / the
individual ontologies).
