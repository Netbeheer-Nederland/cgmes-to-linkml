# cimrdfs2linkml
Generates a LinkML schema from a CIM RDF schema (as per IEC 61970-501).

Currently it only works with the RDFS 2020 serializations of the CGMES 3.0.0 profiles, since some assumptions with regards to the header are baked into the code. Support for other versions of CGMES profiles as well as other CIM RDF Schema models should be a relatively straightforward change of the code.

## Running
Install the dependencies, preferably using `poetry`, and make sure the (virtual) environment you're can find the `cimrdfs2linkml` package (e.g. by extending `$PYTHONPATH`).

Then, to run the script, simply run:

```shell
$ python cimrdfs2linkml/main.py
```

This will read `data/IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf` and generate a LinkML schema from it, which is written to `out.yaml`.
