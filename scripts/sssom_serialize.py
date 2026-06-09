#!/usr/bin/env python3
"""Serialize a directory of SSSOM .tsv files to RDF.

Two combined outputs are written:

  * TriG  (RDF 1.1 named graphs) -- one named graph per mapping set, graph IRI =
    mapping_set_id. The core `subject predicate object` triples live inside the
    graph; set-level provenance (confidence, source, group) is asserted about the
    graph IRI in the default graph. Per-mapping metadata (justification, labels)
    is NOT carried here -- named graphs can't hold it without reification.

  * Turtle-star (RDF 1.2) -- each `subject predicate object` triple is annotated
    inline ({| ... |}) with its mapping_justification, subject/object labels, and
    a link back to its mapping_set. Full fidelity; needs an RDF-1.2-aware parser.

CURIEs are expanded to full IRIs using each file's own curie_map, so no @prefix
declarations are needed in the body and prefixes can't collide across files.

Usage:
    python3 sssom_serialize.py <input_dir> <output_dir>
"""
import sys
import os
import glob

# ---- vocabulary we author -------------------------------------------------
SSSOM   = "https://w3id.org/sssom/"
RDF     = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS    = "http://www.w3.org/2000/01/rdf-schema#"

P_JUST  = SSSOM + "mapping_justification"
P_SLAB  = SSSOM + "subject_label"
P_OLAB  = SSSOM + "object_label"
P_SET   = SSSOM + "mapping_set"          # convenience link mapping -> set
P_CONF  = SSSOM + "mapping_set_confidence"
P_SRC   = SSSOM + "mapping_set_source"
P_GROUP = SSSOM + "mapping_set_group"
C_MSET  = SSSOM + "MappingSet"
C_MAP   = SSSOM + "Mapping"
A_TYPE  = RDF + "type"

# chars illegal in an RFC 3987 IRI -> percent-encode them. This is a superset of
# the Turtle IRIREF exclusions: Turtle permits [ ] but RFC 3987 (enforced by
# strict parsers like oxigraph/Jena) does not, and SMILES/InChI object_ids use them.
_BAD = {ord(c): "%{:02X}".format(ord(c)) for c in ' <>"{}|^`\\[]'}
for _i in range(0x21):
    _BAD.setdefault(_i, "%{:02X}".format(_i))


def iri_escape(s):
    return s.translate(_BAD)


# RFC 3986 unreserved set; the local part of a CURIE is opaque identifier data
# (SMILES, InChI, free text), so anything outside this set is percent-encoded.
_SAFE = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")


def pct_local(s):
    if all(c in _SAFE for c in s):
        return s                       # fast path: ordinary numeric/word ids
    return "".join(c if c in _SAFE else "%{:02X}".format(b)
                   for b in s.encode("utf-8") for c in (chr(b),))


def lit_escape(s):
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"))


def unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        v = v[1:-1]
    return v


def parse_header(fh):
    """Read leading comment lines AND the column-header line via readline().
    Returns (meta, curie_map); fh is left positioned at the first data row."""
    meta = {"other": {}}
    curie = {}
    section = None
    while True:
        line = fh.readline()
        if not line or not line.startswith("#"):
            break  # consumes the column-header (first non-# line)
        body = line[1:]
        if body.startswith(" "):
            body = body[1:]
        body = body.rstrip("\n")
        if not body.strip():
            continue
        indent = len(body) - len(body.lstrip(" "))
        key, _, val = body.strip().partition(":")
        val = val.strip()
        if indent == 0:
            if val == "":
                section = key          # 'curie_map' or 'other'
            else:
                meta[key] = unquote(val)
                section = None
        else:
            if section == "curie_map":
                curie[key] = unquote(val)
            elif section == "other":
                meta["other"][key] = unquote(val)
    return meta, curie


def make_expand(curie, unresolved):
    def expand(curie_str):
        pfx, sep, local = curie_str.partition(":")
        if sep and pfx in curie:
            return iri_escape(curie[pfx]) + pct_local(local)
        if curie_str.startswith(("http://", "https://", "urn:")):
            return iri_escape(curie_str)
        unresolved[pfx] = unresolved.get(pfx, 0) + 1
        return ("https://w3id.org/sssom/.well-known/curie/"
                + pct_local(pfx) + "/" + pct_local(local))
    return expand


PREAMBLE = (
    "@prefix sssom: <{sssom}> .\n"
    "@prefix rdf: <{rdf}> .\n"
    "@prefix rdfs: <{rdfs}> .\n\n"
).format(sssom=SSSOM, rdf=RDF, rdfs=RDFS)


def set_metadata_lines(set_iri, meta):
    """Lines describing the mapping set (used in both outputs' default graph)."""
    parts = ["<{}> a <{}>".format(set_iri, C_MSET)]
    if meta.get("mapping_set_group"):
        parts.append('  <{}> "{}"'.format(P_GROUP, lit_escape(meta["mapping_set_group"])))
    conf = meta.get("mapping_set_confidence")
    if conf:
        try:
            float(conf)
            parts.append("  <{}> {}".format(P_CONF, conf))
        except ValueError:
            pass
    src = meta.get("other", {}).get("mapping_set_source")
    if src:
        parts.append("  <{}> <{}>".format(P_SRC, iri_escape(src)))
    return " ;\n".join(parts) + " .\n"


def serialize(input_dir, output_dir):
    files = sorted(glob.glob(os.path.join(input_dir, "*.sssom.tsv")))
    if not files:
        sys.exit("no *.sssom.tsv files in " + input_dir)
    trig_path = os.path.join(output_dir, "sssom_all.trig")
    ttls_path = os.path.join(output_dir, "sssom_all.ttls")
    unresolved = {}
    n_rows = 0

    with open(trig_path, "w", buffering=1 << 20) as trig, \
         open(ttls_path, "w", buffering=1 << 20) as ttls:
        trig.write(PREAMBLE)
        ttls.write(PREAMBLE)

        for fi, path in enumerate(files, 1):
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                meta, curie = parse_header(fh)
                expand = make_expand(curie, unresolved)
                set_id = meta.get("mapping_set_id") or ("file://" + path)
                set_iri = iri_escape(set_id)

                meta_block = set_metadata_lines(set_iri, meta)
                trig.write("\n" + meta_block)
                ttls.write("\n" + meta_block)
                trig.write("<{}> {{\n".format(set_iri))

                # column header already consumed by parse_header; fh is at row 1
                tbuf = []
                sbuf = []
                for line in fh:
                    if not line.strip():
                        continue
                    f = line.rstrip("\n").split("\t")
                    if len(f) < 4:
                        continue
                    sid, pid, oid, just = f[0], f[1], f[2], f[3]
                    slab = f[4] if len(f) > 4 else ""
                    olab = f[5] if len(f) > 5 else ""
                    s = expand(sid); p = expand(pid); o = expand(oid)
                    triple = "<{}> <{}> <{}>".format(s, p, o)

                    # TriG: bare triple inside the named graph
                    tbuf.append("  " + triple + " .\n")

                    # Turtle-star: triple + inline annotation
                    ann = []
                    if just:
                        ann.append("<{}> <{}>".format(P_JUST, expand(just)))
                    if slab:
                        ann.append('<{}> "{}"'.format(P_SLAB, lit_escape(slab)))
                    if olab:
                        ann.append('<{}> "{}"'.format(P_OLAB, lit_escape(olab)))
                    ann.append("<{}> <{}>".format(P_SET, set_iri))
                    sbuf.append("{} {{| {} |}} .\n".format(triple, " ; ".join(ann)))

                    n_rows += 1
                    if len(tbuf) >= 50000:
                        trig.write("".join(tbuf)); tbuf = []
                        ttls.write("".join(sbuf)); sbuf = []
                if tbuf:
                    trig.write("".join(tbuf))
                    ttls.write("".join(sbuf))
                trig.write("}\n")
            sys.stderr.write("\r[{}/{}] {}  rows={}".format(
                fi, len(files), os.path.basename(path), n_rows))
            sys.stderr.flush()

    sys.stderr.write("\nDONE  {} mappings\n".format(n_rows))
    sys.stderr.write("  TriG        -> {}\n".format(trig_path))
    sys.stderr.write("  Turtle-star -> {}\n".format(ttls_path))
    if unresolved:
        sys.stderr.write("WARNING: unresolved CURIE prefixes (minted .well-known IRIs):\n")
        for pfx, n in sorted(unresolved.items(), key=lambda kv: -kv[1]):
            sys.stderr.write("    {:<20} {} occurrences\n".format(pfx + ":", n))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: sssom_serialize.py <input_dir> <output_dir>")
    serialize(sys.argv[1], sys.argv[2])
