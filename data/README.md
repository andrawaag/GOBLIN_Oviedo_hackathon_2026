# Rendered SSSOM data

The rendered RDF is too large to store in git (TriG 1.5 GB + Turtle-star 3.7 GB), so it is
**deposited on Zenodo** and downloaded from there.

| File | Format | Uncompressed | Gzipped |
|---|---|---|---|
| `sssom_all.trig` | Named graphs (TriG) — one graph per `mapping_set` | 1.5 GB | 87 MB |
| `sssom_all.ttls` | RDF 1.2 / Turtle-star — per-mapping annotations | 3.7 GB | 204 MB |

Both cover the same **271 EBI OLS mapping sets / 6,238,000 mappings**.

## Download

> **Zenodo DOI:** `10.5281/zenodo.XXXXXXXX` — _TODO: replace with the real DOI once the
> deposit is published._

```bash
# example once the record exists:
curl -L -o sssom_all.trig.gz "https://zenodo.org/records/XXXXXXXX/files/sssom_all.trig.gz"
curl -L -o sssom_all.ttls.gz "https://zenodo.org/records/XXXXXXXX/files/sssom_all.ttls.gz"
gunzip sssom_all.trig.gz sssom_all.ttls.gz
```

Then load them into Oxigraph — see [`../OXIGRAPH.md`](../OXIGRAPH.md).

## Depositing to Zenodo (maintainers)

1. Create a new record at <https://zenodo.org/uploads/new>.
2. Upload `sssom_all.trig.gz` and `sssom_all.ttls.gz` (already gzipped locally).
3. Suggested metadata:
   - **Title:** SSSOM (EBI OLS) rendered as RDF named graphs and RDF 1.2
   - **Upload type:** Dataset
   - **Keywords:** SSSOM, ontology mappings, RDF-star, RDF 1.2, named graphs, OLS, GOBLIN
   - **Related identifier:** *is supplement to* `https://github.com/andrawaag/GOBLIN_Oviedo_hackathon_2026`
4. Publish, then replace the placeholder DOI above and the URLs in this file.

## Regenerate from source instead

If you'd rather not download, regenerate from the OLS SSSOM TSV extracts:

```bash
python3 ../scripts/sssom_serialize.py <dir-with-*.sssom.tsv> .
```
